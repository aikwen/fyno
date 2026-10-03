"""Fyno Filesystem API。

该模块提供 Fyno 全局可复用的文件系统相关 HTTP 接口。

职责范围：
- 解析目录补全请求。
- 校验用户输入路径。
- 调用 util.fs 中的目录搜索能力。
- 将 Path 对象转换为 API 响应。

该模块不负责：
- Library Workspace 管理。
- Collection / File 业务逻辑。
- 直接维护应用状态。
"""

import os
from pathlib import Path

from fastapi import APIRouter, Query
from pydantic import BaseModel

from ..utils.fs import list_directories


router = APIRouter(
    prefix="/filesystem",
    tags=["filesystem"],
)


class DirectoryResponse(BaseModel):
    """目录搜索响应。"""

    name: str
    path: str


@router.get(
    "/directories",
    response_model=list[DirectoryResponse],
)
def search_directories(
    path: str = Query(
        min_length=1,
    ),
    limit: int = Query(
        default=20,
        ge=1,
        le=20,
    ),
) -> list[DirectoryResponse]:
    """搜索用户输入路径对应的直接子目录。

    输入既可以是完整目录，也可以是正在输入中的目录前缀。

    例如：

    `D:\\fyno\\wo`

    会被解析为：

    - parent: `D:\\fyno`
    - prefix: `wo`

    Args:
        path: 用户当前输入的路径。
        limit: 最大返回数量。

    Returns:
        匹配到的目录列表。
    """
    query = path.strip()

    if not query:
        return []

    query = os.path.expanduser(
        query
    )

    separators = tuple(
        separator
        for separator in (
            os.sep,
            os.altsep,
        )
        if separator
    )

    if query.endswith(separators):
        parent = query
        prefix = None
    else:
        parent, prefix = os.path.split(
            query
        )

    if not parent:
        return []

    parent_path = Path(parent)

    if not parent_path.is_absolute():
        return []

    directories = list_directories(
        parent_path,
        prefix=prefix,
        limit=limit,
    )

    return [
        DirectoryResponse(
            name=directory.name,
            path=str(directory),
        )
        for directory in directories
    ]