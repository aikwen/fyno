"""Fyno Library File API。

该模块负责处理 File 相关 HTTP 请求，并将请求转换为
Workspace 层操作。

职责范围：
- 查询 Collection 下的 File 列表。
- 查询 File Markdown 内容。
- 创建 File。
- 修改 File Markdown 内容。
- 修改 File display name。
- 删除 File。
- 调整 File 顺序。
- 将 Domain 对象转换为 API 响应。

该模块不负责：
- 直接修改 Domain 状态。
- 直接读写 Metadata。
- 直接操作 Workspace 文件系统。
"""

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
)
from pydantic import BaseModel

from ..domain.file import LibraryFile
from ..domain.library import Library
from ..workspace import file as file_workspace
from .dependencies import require_library


router = APIRouter(
    prefix="/collections/{collection_id}/files",
    tags=["library"],
)


class CreateFileRequest(BaseModel):
    """创建 File 请求。"""

    name: str


class RenameFileRequest(BaseModel):
    """修改 File display name 请求。"""

    name: str


class MoveFileRequest(BaseModel):
    """调整 File 顺序请求。"""

    afterFileId: str | None = None


class UpdateFileContentRequest(BaseModel):
    """修改 File Markdown 内容请求。"""

    content: str


class FileResponse(BaseModel):
    """File 响应。"""

    collectionId: str
    fileId: str
    name: str


class FileContentResponse(BaseModel):
    """File Markdown 内容响应。"""

    collectionId: str
    fileId: str
    content: str


class SuccessResponse(BaseModel):
    """通用成功响应。"""

    success: bool


def _to_response(
    collection_id: str,
    file: LibraryFile,
) -> FileResponse:
    """将 LibraryFile Domain 对象转换为 API 响应。

    Args:
        collection_id: File 所属的 Collection ID。
        file: LibraryFile Domain 对象。

    Returns:
        File API 响应。
    """
    return FileResponse(
        collectionId=collection_id,
        fileId=file.file_id,
        name=file.name,
    )


@router.get(
    "",
    response_model=list[FileResponse],
)
def get_files(
    collection_id: str,
    library: Library = Depends(
        require_library
    ),
) -> list[FileResponse]:
    """查询 Collection 下的 File 列表。"""
    collection = library.find_collection(
        collection_id
    )

    if collection is None:
        raise HTTPException(
            status_code=404,
            detail="Collection not found",
        )

    return [
        _to_response(
            collection_id,
            file,
        )
        for file in collection.files
    ]


@router.get(
    "/{file_id}",
    response_model=FileContentResponse,
)
def get_file_content(
    collection_id: str,
    file_id: str,
    library: Library = Depends(
        require_library
    ),
) -> FileContentResponse:
    """查询 File Markdown 内容。"""
    collection = library.find_collection(
        collection_id
    )

    if collection is None:
        raise HTTPException(
            status_code=404,
            detail="Collection not found",
        )

    if collection.find_file(file_id) is None:
        raise HTTPException(
            status_code=404,
            detail="File not found",
        )

    content = file_workspace.read_file_content(
        collection_id,
        file_id,
    )

    if content is None:
        raise HTTPException(
            status_code=404,
            detail="File content not found",
        )

    return FileContentResponse(
        collectionId=collection_id,
        fileId=file_id,
        content=content,
    )


@router.post(
    "",
    response_model=FileResponse,
)
def create_file(
    collection_id: str,
    request: CreateFileRequest,
    library: Library = Depends(
        require_library
    ),
) -> FileResponse:
    """创建 File。"""
    if library.find_collection(collection_id) is None:
        raise HTTPException(
            status_code=404,
            detail="Collection not found",
        )

    if not request.name.strip():
        raise HTTPException(
            status_code=400,
            detail="File name cannot be empty",
        )

    file = file_workspace.create_file(
        collection_id,
        request.name,
    )

    if file is None:
        raise HTTPException(
            status_code=400,
            detail="File could not be created",
        )

    return _to_response(
        collection_id,
        file,
    )


@router.put(
    "/{file_id}",
    response_model=FileContentResponse,
)
def update_file_content(
    collection_id: str,
    file_id: str,
    request: UpdateFileContentRequest,
    library: Library = Depends(
        require_library
    ),
) -> FileContentResponse:
    """修改 File Markdown 内容。"""
    collection = library.find_collection(
        collection_id
    )

    if collection is None:
        raise HTTPException(
            status_code=404,
            detail="Collection not found",
        )

    if collection.find_file(file_id) is None:
        raise HTTPException(
            status_code=404,
            detail="File not found",
        )

    if not file_workspace.write_file_content(
        collection_id,
        file_id,
        request.content,
    ):
        raise HTTPException(
            status_code=404,
            detail="File content not found",
        )

    return FileContentResponse(
        collectionId=collection_id,
        fileId=file_id,
        content=request.content,
    )


@router.patch(
    "/{file_id}",
    response_model=FileResponse,
)
def rename_file(
    collection_id: str,
    file_id: str,
    request: RenameFileRequest,
    library: Library = Depends(
        require_library
    ),
) -> FileResponse:
    """修改 File display name。"""
    collection = library.find_collection(
        collection_id
    )

    if collection is None:
        raise HTTPException(
            status_code=404,
            detail="Collection not found",
        )

    file = collection.find_file(
        file_id
    )

    if file is None:
        raise HTTPException(
            status_code=404,
            detail="File not found",
        )

    if not request.name.strip():
        raise HTTPException(
            status_code=400,
            detail="File name cannot be empty",
        )

    file_workspace.rename_file(
        collection_id,
        file_id,
        request.name,
    )

    return _to_response(
        collection_id,
        file,
    )


@router.delete(
    "/{file_id}",
    response_model=SuccessResponse,
)
def delete_file(
    collection_id: str,
    file_id: str,
    library: Library = Depends(
        require_library
    ),
) -> SuccessResponse:
    """删除 File。"""
    collection = library.find_collection(
        collection_id
    )

    if collection is None:
        raise HTTPException(
            status_code=404,
            detail="Collection not found",
        )

    if collection.find_file(file_id) is None:
        raise HTTPException(
            status_code=404,
            detail="File not found",
        )

    if not file_workspace.delete_file(
        collection_id,
        file_id,
    ):
        raise HTTPException(
            status_code=404,
            detail="File not found",
        )

    return SuccessResponse(
        success=True,
    )


@router.patch(
    "/{file_id}/position",
    response_model=SuccessResponse,
)
def move_file(
    collection_id: str,
    file_id: str,
    request: MoveFileRequest,
    library: Library = Depends(
        require_library
    ),
) -> SuccessResponse:
    """调整 File 顺序。"""
    collection = library.find_collection(
        collection_id
    )

    if collection is None:
        raise HTTPException(
            status_code=404,
            detail="Collection not found",
        )

    if collection.find_file(file_id) is None:
        raise HTTPException(
            status_code=404,
            detail="File not found",
        )

    if request.afterFileId == file_id:
        raise HTTPException(
            status_code=400,
            detail="Cannot move file after itself",
        )

    if (
        request.afterFileId is not None
        and collection.find_file(
            request.afterFileId
        )
        is None
    ):
        raise HTTPException(
            status_code=404,
            detail="Target file not found",
        )

    file_workspace.move_file(
        collection_id,
        file_id,
        request.afterFileId,
    )

    return SuccessResponse(
        success=True,
    )