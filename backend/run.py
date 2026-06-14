"""应用启动入口

用法::

    python run.py

也可直接使用 uvicorn::

    uvicorn app.main:app --reload
"""

import sys
from pathlib import Path

import uvicorn

# 将脚本所在目录加入 sys.path，确保从任意工作目录都能找到 app 模块
sys.path.insert(0, str(Path(__file__).parent))

from app.main import app

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
