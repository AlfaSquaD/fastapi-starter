from fastapi import FastAPI
from bootstrap import bootstrap

bootstrap()

app = FastAPI()

from routers.hello import router as hello_router

app.include_router(hello_router)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
