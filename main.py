"""uvicorn entrypoint — also usable as CLI: python main.py"""

import uvicorn
from dotenv import load_dotenv

load_dotenv()

from src.bossfinder.config import get_settings

if __name__ == "__main__":
    settings = get_settings()
    uvicorn.run(
        "src.bossfinder.api:app",
        host=settings.host,
        port=settings.port,
        log_level=settings.log_level,
        reload=False,
    )
