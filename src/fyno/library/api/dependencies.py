"""Fyno Library API 公共依赖。

该模块负责定义 Library API 的公共前置条件，并通过 FastAPI Depends
为具体 Endpoint 提供已经校验过的运行时对象。
"""

from pathlib import Path

from fastapi import HTTPException

from ..domain.library import Library
from ..workspace.workspace import (
    get_library,
    get_workspace,
)


def require_workspace() -> Path:
    """获取当前已配置的 Workspace。

    Returns:
        当前 Workspace 路径。

    Raises:
        HTTPException: Workspace 未配置时返回 409。
    """
    workspace = get_workspace()

    if workspace is None:
        raise HTTPException(
            status_code=409,
            detail="Workspace is not configured",
        )

    return workspace


def require_library() -> Library:
    """获取当前已经初始化的 Library。

    Returns:
        当前 Library Domain 对象。

    Raises:
        HTTPException:
            Workspace 未配置时返回 409。
            Library 未初始化时返回 409。
    """
    require_workspace()

    library = get_library()

    if library is None:
        raise HTTPException(
            status_code=409,
            detail="Library is not initialized",
        )

    return library