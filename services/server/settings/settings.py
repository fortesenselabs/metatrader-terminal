import os
import inspect
from dotenv import load_dotenv

# Load environment variables env vars AND from .env file
load_dotenv()


class Settings:
    def __init__(self):
        self.METATRADER_FILES_DIR = self._get_setting("MT_FILES_DIR")
        self.PORT = int(self._get_setting("PORT"))

    def _get_setting(self, key):
        value = os.environ.get(f"{key}")
        if not value:
            raise ValueError(f"Missing environment variable: {key}")
        return value

    def model_dump(self):
        """Dumps all settings as a dictionary, excluding methods."""
        return {
            key: getattr(self, key)
            for key in dir(self)
            if not key.startswith("_") and not inspect.ismethod(getattr(self, key))
        }
