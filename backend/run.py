"""应用启动入口

用法::

    python run.py

也可直接使用 uvicorn::

    uvicorn app.main:app --reload
"""

import uvicorn

from app.main import app

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
