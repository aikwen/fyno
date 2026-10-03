"""Fyno Library Workspace API。

该模块负责处理 Library Workspace 相关 HTTP 请求，并将请求转换为
Workspace 生命周期操作。

职责范围：
- 查询当前 Workspace。
- 修改当前 Workspace。
- Reload 当前 Library Metadata。
- Rebuild / Repair 当前 Library。

该模块不负责：
- 直接读写应用配置。
- 直接读写 `.fyno/library.json`。
- 直接扫描 Workspace 文件系统。
"""

from pathlib import Path

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
)
from pydantic import BaseModel

from ..domain.library import Library
from ..workspace import workspace as workspace_service
from .dependencies import (
    require_library,
    require_workspace,
)


router = APIRouter(
    prefix="/workspace",
    tags=["library"],
)


class UpdateWorkspaceRequest(BaseModel):
    """修改 Workspace 请求。"""

    directory: str


class WorkspaceResponse(BaseModel):
    """Workspace 响应。"""

    directory: str
    initialized: bool


class SuccessResponse(BaseModel):
    """通用成功响应。"""

    success: bool


def _get_workspace_response() -> WorkspaceResponse:
    """获取当前 Workspace API 响应。"""
    workspace = workspace_service.get_workspace()
    library = workspace_service.get_library()

    return WorkspaceResponse(
        directory=(
            str(workspace)
            if workspace is not None
            else ""
        ),
        initialized=(
            workspace is not None
            and library is not None
        ),
    )


@router.get(
    "",
    response_model=WorkspaceResponse,
)
def get_workspace() -> WorkspaceResponse:
    """获取当前 Workspace。"""
    return _get_workspace_response()


@router.patch(
    "",
    response_model=WorkspaceResponse,
)
def update_workspace(
    request: UpdateWorkspaceRequest,
) -> WorkspaceResponse:
    """修改当前 Workspace。"""
    directory = request.directory.strip()

    if not directory:
        raise HTTPException(
            status_code=400,
            detail="Workspace directory cannot be empty",
        )

    try:
        workspace_service.set_workspace(
            directory
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    return _get_workspace_response()


@router.post(
    "/reload",
    response_model=SuccessResponse,
)
def reload_workspace(
    library: Library = Depends(
        require_library
    ),
) -> SuccessResponse:
    """重新加载当前 Workspace 的 Metadata。

    Reload 只重新读取 `.fyno/library.json`，不会扫描文件系统，也不会
    执行 Repair。
    """
    try:
        workspace_service.reload()
    except (OSError, ValueError) as exc:
        raise HTTPException(
            status_code=500,
            detail=str(exc),
        ) from exc

    return SuccessResponse(
        success=True,
    )


@router.post(
    "/rebuild",
    response_model=SuccessResponse,
)
def rebuild_workspace(
    workspace: Path = Depends(
        require_workspace
    ),
) -> SuccessResponse:
    """重新构建或修复当前 Library。

    如果 Metadata 不存在，则根据 Workspace 文件系统重新创建；
    如果 Metadata 已存在，则根据当前文件系统状态进行 Repair。
    """
    try:
        workspace_service.rebuild()
    except OSError as exc:
        raise HTTPException(
            status_code=500,
            detail=str(exc),
        ) from exc

    return SuccessResponse(
        success=True,
    )