"""Fyno application entrypoint。

该模块负责创建 FastAPI 应用，并挂载各个功能模块提供的 Router。

职责范围：
- 创建 FastAPI app。
- 管理应用生命周期。
- 配置全局中间件。
- 注册各功能模块 Router。
- 托管前端静态资源。
- 提供 SPA fallback。
- 提供本地直接启动入口。

该模块不负责：
- Library 业务逻辑。
- Workspace 生命周期实现。
- Metadata 或文件系统操作。
"""

from contextlib import asynccontextmanager
from pathlib import Path

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .api import router as api_router
from .library.api import router as library_router
from .library.workspace import workspace as workspace_service


STATIC_DIR = Path(__file__).resolve().parent / "static"
ASSETS_DIR = STATIC_DIR / "assets"
INDEX_FILE = STATIC_DIR / "index.html"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """管理 Fyno 应用生命周期。

    应用启动时尝试从本地配置恢复上一次使用的 Library Workspace。

    Args:
        app: FastAPI application。

    Yields:
        应用运行控制权。
    """
    workspace_service.initialize()

    yield


app = FastAPI(
    title="Fyno API",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Router 必须先注册，避免被 SPA fallback 捕获。
app.include_router(
    api_router,
)

app.include_router(
    library_router,
)


# Vite 构建后的静态资源。
if ASSETS_DIR.is_dir():
    app.mount(
        "/assets",
        StaticFiles(directory=ASSETS_DIR),
        name="assets",
    )


@app.get("/{full_path:path}", include_in_schema=False)
def serve_frontend(full_path: str):
    """返回 Fyno 前端页面。

    Vue Router 使用 history 模式，因此除 API 和静态资源外，
    其余路径统一回退到 index.html，由前端 Router 负责解析。
    """
    if not INDEX_FILE.is_file():
        return {
            "detail": "Frontend is not built.",
        }

    return FileResponse(INDEX_FILE)


def main() -> None:
    """启动 Fyno HTTP 服务。"""
    uvicorn.run(
        "fyno.main:app",
        host="127.0.0.1",
        port=9950,
        reload=False,
    )


if __name__ == "__main__":
    main()