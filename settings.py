import os
from dotenv import load_dotenv
load_dotenv(verbose=True)

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
