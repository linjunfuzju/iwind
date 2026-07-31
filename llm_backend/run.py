import sys
import os
from pathlib import Path

import uvicorn
from app.core.logger import get_logger  # 这个来自 llm_backend/app

logger = get_logger(service="server")

def start_server():
    logger.info("Starting server...")
    logger.info(f"Working directory: {os.getcwd()}")
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=9000,
        access_log=False,
        log_level="error",
        reload=True
    )

if __name__ == "__main__":
    start_server()