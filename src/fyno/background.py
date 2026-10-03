"""Fyno background process。

该模块负责：
- 启动 Fyno HTTP 服务。
- 启动系统托盘。
- 协调 Uvicorn 与 Tray 生命周期。
- 在用户退出 Fyno 时优雅停止 HTTP 服务。

该模块不负责：
- FastAPI app 定义。
- API Router 注册。
- Library 业务逻辑。
- 后台进程启动。
"""

import ctypes
import sys
from threading import Thread

import uvicorn

from .desktop.tray import create_tray
from .main import HOST, PORT, app


def _enable_dpi_awareness() -> None:
    """启用 Windows Per-Monitor DPI Awareness。"""
    if sys.platform != "win32":
        return

    try:
        ctypes.windll.user32.SetProcessDpiAwarenessContext(
            ctypes.c_void_p(-4)
        )
    except (AttributeError, OSError):
        pass


def run() -> None:
    """运行 Fyno 后台进程。

    Tray 运行在主线程，
    Uvicorn HTTP 服务运行在后台线程。
    """
    _enable_dpi_awareness()

    config = uvicorn.Config(
        app=app,
        host=HOST,
        port=PORT,
        reload=False,
    )

    server = uvicorn.Server(
        config=config,
    )

    server_thread = Thread(
        target=server.run,
        name="fyno-http",
    )

    def exit_fyno() -> None:
        """请求停止 Fyno HTTP 服务。"""
        server.should_exit = True

    tray = create_tray(
        on_exit=exit_fyno,
    )

    server_thread.start()

    try:
        tray.run()
    finally:
        server.should_exit = True
        server_thread.join()


if __name__ == "__main__":
    run()