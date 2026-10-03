"""Fyno packaged resource access utilities.

该模块负责：
- 统一定位 Fyno package 内的 resource 目录。
- 根据相对 resource 的路径返回资源文件路径。
- 对不存在的资源返回 None。

该模块不负责：
- 读取资源内容。
- 解析图片、JSON 或其他文件格式。
"""

from pathlib import Path


_RESOURCE_ROOT = Path(__file__).resolve().parent


def get_resource(
    relative_path: str,
) -> Path | None:
    """获取 Fyno resource 目录下的资源文件。

    Args:
        relative_path:
            相对于 `fyno/resource` 的资源路径。
            例如：
            `icon/fyno.ico`

    Returns:
        资源存在时返回绝对 Path。
        不存在时返回 None。
    """
    path = (
        _RESOURCE_ROOT
        / relative_path
    ).resolve()

    try:
        path.relative_to(
            _RESOURCE_ROOT.resolve()
        )
    except ValueError:
        return None

    if not path.is_file():
        return None

    return path