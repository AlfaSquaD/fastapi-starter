"""
This file is used to bootstrap the application. It is called from the main
"""

from kink import di
from pathlib import Path
from dotenv import load_dotenv
import os


def bootstrap():
    load_dotenv()
    # Either assign the env variables to global variables or use some kind of DI
    # di["temp_dir"] = Path(os.getenv("TEMP_DIR") or "/app_tmp")
    
