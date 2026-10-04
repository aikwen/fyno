"""Fyno application entrypoint。

该模块负责创建 FastAPI 应用，并提供 Fyno 启动入口。

职责范围：
- 创建 FastAPI app。
- 管理应用生命周期。
- 配置全局中间件。
- 注册各功能模块 Router。
- 托管前端静态资源。
- 提供 SPA fallback。
- 检测 Fyno 是否已经运行。
- 启动 Fyno 后台进程。

该模块不负责：
- Library 业务逻辑。
- Workspace 生命周期实现。
- Metadata 或文件系统操作。
- Tray 生命周期。
- Uvicorn 后台运行逻辑。
"""

from contextlib import asynccontextmanager
from pathlib import Path
import json
import socket
import subprocess
import sys
import urllib.error
import urllib.request
import webbrowser

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .__about__ import __version__
from .api import router as api_router
from .library.api import router as library_router
from .library.workspace import workspace as workspace_service


HOST = "127.0.0.1"
PORT = 9950

FYNO_URL = f"http://{HOST}:{PORT}"
HEALTH_URL = f"{FYNO_URL}/api/health"

STATIC_DIR = Path(__file__).resolve().parent / "static"
ASSETS_DIR = STATIC_DIR / "assets"
INDEX_FILE = STATIC_DIR / "index.html"
FAVICON_FILE = STATIC_DIR / "favicon.svg"


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
    version=__version__,
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


@app.get(
    "/api/health",
    include_in_schema=False,
)
def health() -> dict[str, str]:
    """返回 Fyno 实例信息。"""
    return {
        "app": "fyno",
        "version": __version__,
    }


# Vite 构建后的静态资源。
if ASSETS_DIR.is_dir():
    app.mount(
        "/assets",
        StaticFiles(directory=ASSETS_DIR),
        name="assets",
    )


@app.get(
    "/favicon.svg",
    include_in_schema=False,
)
def favicon():
    return FileResponse(
        FAVICON_FILE,
        media_type="image/svg+xml",
    )

@app.get(
    "/{full_path:path}",
    include_in_schema=False,
)
def serve_frontend(
    full_path: str,
):
    """返回 Fyno 前端页面。

    Vue Router 使用 history 模式，因此除 API 和静态资源外，
    其余路径统一回退到 index.html，由前端 Router 负责解析。
    """
    if not INDEX_FILE.is_file():
        return {
            "detail": "Frontend is not built.",
        }

    return FileResponse(INDEX_FILE)


def _is_fyno_running() -> bool:
    """判断当前 Fyno 实例是否已经运行。"""
    try:
        with urllib.request.urlopen(
            HEALTH_URL,
            timeout=0.5,
        ) as response:
            data = json.load(response)

        return data.get("app") == "fyno"

    except (
        urllib.error.URLError,
        TimeoutError,
        OSError,
        json.JSONDecodeError,
    ):
        return False


def _is_port_used() -> bool:
    """判断 Fyno HTTP 端口是否已经被占用。"""
    with socket.socket(
        socket.AF_INET,
        socket.SOCK_STREAM,
    ) as sock:
        sock.settimeout(0.3)

        return (
            sock.connect_ex(
                (HOST, PORT)
            )
            == 0
        )

def _start_background() -> None:
    """启动独立的 Fyno 后台进程。"""
    kwargs = {}

    if sys.platform == "win32":
        kwargs["creationflags"] = (
            subprocess.CREATE_NO_WINDOW
        )

    subprocess.Popen(
        [
            sys.executable,
            "-m",
            "fyno.background",
        ],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        close_fds=True,
        **kwargs,
    )


def main() -> None:
    """启动或打开 Fyno。

    已有 Fyno 实例运行时直接打开浏览器；
    未运行时启动独立后台进程。
    """
    if _is_fyno_running():
        webbrowser.open(
            FYNO_URL
        )
        return

    if _is_port_used():
        raise RuntimeError(
            f"Port {PORT} is already in use "
            "by another application."
        )

    _start_background()


if __name__ == "__main__":
    main()