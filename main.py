import os
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from bootstrap import bootstrap
from helpers.logger import setup_logging

os.environ["DD_TRACE_ENABLED"] = os.getenv(
    "DD_TRACE_ENABLED", "false"
)  # noqa

import structlog
import uvicorn
from asgi_correlation_id import CorrelationIdMiddleware
from asgi_correlation_id.context import correlation_id
from ddtrace.contrib.asgi.middleware import TraceMiddleware
from fastapi import FastAPI, Request, Response
from pydantic import parse_obj_as
from uvicorn.protocols.utils import (
    get_path_with_query_string,
)

from bootstrap import bootstrap

LOG_JSON_FORMAT = parse_obj_as(
    bool, os.getenv("LOG_JSON_FORMAT", False)
)
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
setup_logging(
    json_logs=LOG_JSON_FORMAT, log_level=LOG_LEVEL
)

access_logger = structlog.stdlib.get_logger("api.access")


@asynccontextmanager
async def async_bootstrap(
    app: FastAPI,
):
    await bootstrap()
    try:
        yield
    finally:
        pass


app = FastAPI(lifespan=async_bootstrap)


@app.middleware("http")
async def logging_middleware(
    request: Request, call_next
) -> Response:
    structlog.contextvars.clear_contextvars()
    # These context vars will be added to all log entries emitted during the request
    request_id = correlation_id.get()
    structlog.contextvars.bind_contextvars(
        request_id=request_id
    )

    start_time = time.perf_counter_ns()
    # If the call_next raises an error, we still want to return our own 500 response,
    # so we can add headers to it (process time, request ID...)
    response = Response(status_code=500)
    try:
        response = await call_next(request)
    except Exception:
        # TODO: Validate that we don't swallow exceptions (unit test?)
        structlog.stdlib.get_logger("api.error").exception(
            "Uncaught exception"
        )
        raise
    finally:
        process_time = time.perf_counter_ns() - start_time
        status_code = response.status_code
        url = get_path_with_query_string(request.scope)  # type: ignore
        client_host = request.client.host  # type: ignore
        client_port = request.client.port  # type: ignore
        http_method = request.method
        http_version = request.scope["http_version"]
        # Recreate the Uvicorn access log format, but add all parameters as structured information
        access_logger.info(
            f"""{client_host}:{client_port} - "{http_method} {url} HTTP/{http_version}" {status_code}""",
            http={
                "url": str(request.url),
                "status_code": status_code,
                "method": http_method,
                "request_id": request_id,
                "version": http_version,
            },
            network={
                "client": {
                    "ip": client_host,
                    "port": client_port,
                }
            },
            duration=process_time,
        )
        response.headers["X-Process-Time"] = str(
            process_time / 10**9
        )
        return response


app.add_middleware(CorrelationIdMiddleware)

tracing_middleware = next(
    (
        m
        for m in app.user_middleware
        if m.cls == TraceMiddleware
    ),
    None,
)
if tracing_middleware is not None:
    app.user_middleware = [
        m
        for m in app.user_middleware
        if m.cls != TraceMiddleware
    ]
    structlog.stdlib.get_logger("api.datadog_patch").info(
        "Patching Datadog tracing middleware to be the outermost middleware..."
    )
    app.user_middleware.insert(0, tracing_middleware)
    app.middleware_stack = app.build_middleware_stack()

from routers.hello import router as hello_router

app.include_router(hello_router)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
