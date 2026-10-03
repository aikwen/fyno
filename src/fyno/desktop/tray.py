"""Fyno Windows system tray.

该模块负责：
- 创建 Fyno 系统托盘图标。
- 提供 Open Fyno 菜单。
- 提供 Exit 菜单。
- 打开本地 Fyno Web 页面。

该模块不负责：
- FastAPI / Uvicorn 启动。
- 应用生命周期管理。
- 后端业务逻辑。
- 资源路径解析。
"""

from collections.abc import Callable
import webbrowser

import pystray
from PIL import Image

from ..resource.resource import get_resource


FYNO_URL = "http://127.0.0.1:9950"


def _load_icon() -> Image.Image:
    """加载 Fyno 托盘图标。

    Returns:
        Pillow Image 对象。

    Raises:
        FileNotFoundError:
            图标资源不存在时抛出。
    """
    icon_path = get_resource(
        "icon/fyno.ico"
    )

    if icon_path is None:
        raise FileNotFoundError(
            "Fyno tray icon not found."
        )

    return Image.open(icon_path)


def _open_fyno(
    icon: pystray.Icon,
    item: pystray.MenuItem,
) -> None:
    """在默认浏览器中打开 Fyno。"""
    webbrowser.open(
        FYNO_URL
    )


def create_tray(
    on_exit: Callable[[], None],
) -> pystray.Icon:
    """创建 Fyno 系统托盘。

    Args:
        on_exit:
            用户点击 Exit 时调用的回调。
            上层应负责停止 Uvicorn 和结束应用。

    Returns:
        已配置但尚未运行的 pystray.Icon。
    """

    def exit_fyno(
        icon: pystray.Icon,
        item: pystray.MenuItem,
    ) -> None:
        on_exit()
        icon.stop()

    menu = pystray.Menu(
        pystray.MenuItem(
            "Open Fyno",
            _open_fyno,
            default=True,
        ),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem(
            "Exit",
            exit_fyno,
        ),
    )

    return pystray.Icon(
        name="fyno",
        icon=_load_icon(),
        title="Fyno",
        menu=menu,
    )