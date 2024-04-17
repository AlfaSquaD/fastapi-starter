"""
This file is used to bootstrap the application. It is called from the main
"""

import os
from pathlib import Path

from dotenv import load_dotenv
from kink import di


async def bootstrap():
    load_dotenv()
    # Either assign the env variables to global variables or use some kind of DI
    # di["temp_dir"] = Path(os.getenv("TEMP_DIR") or "/app_tmp")
