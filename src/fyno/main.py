"""Fyno application entrypoint。

该模块负责创建 FastAPI 应用，并挂载各个功能模块提供的 Router。

职责范围：
- 创建 FastAPI app。
- 管理应用生命周期。
- 配置全局中间件。
- 注册各功能模块 Router。
- 提供本地直接启动入口。

该模块不负责：
- Library 业务逻辑。
- Workspace 生命周期实现。
- Metadata 或文件系统操作。
"""

from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api import router as api_router
from .library.api import router as library_router
from .library.workspace import workspace as workspace_service


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

app.include_router(
    api_router,
)

app.include_router(
    library_router,
)


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