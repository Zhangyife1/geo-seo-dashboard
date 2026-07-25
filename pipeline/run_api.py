"""
API 服务启动脚本
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import uvicorn
from config import API_CONFIG

if __name__ == "__main__":
    uvicorn.run(
        "api.main:app",
        host=API_CONFIG["host"],
        port=API_CONFIG["port"],
        reload=True,
        log_level="info"
    )
