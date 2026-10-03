"""Fyno Library Collection API。

该模块负责处理 Collection 相关 HTTP 请求，并将请求转换为
Workspace 层操作。

职责范围：
- 查询 Collection 列表。
- 创建 Collection。
- 修改 Collection display name。
- 删除 Collection。
- 调整 Collection 顺序。
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
    Query,
)
from pydantic import BaseModel

from ..domain.collection import Collection
from ..domain.library import Library
from ..workspace import collection as collection_workspace
from .dependencies import require_library


router = APIRouter(
    prefix="/collections",
    tags=["library"],
)


class CreateCollectionRequest(BaseModel):
    """创建 Collection 请求。"""

    name: str


class RenameCollectionRequest(BaseModel):
    """修改 Collection display name 请求。"""

    name: str


class MoveCollectionRequest(BaseModel):
    """调整 Collection 顺序请求。"""

    afterCollectionId: str | None = None


class CollectionResponse(BaseModel):
    """Collection 响应。"""

    collectionId: str
    name: str
    fileCount: int


class SuccessResponse(BaseModel):
    """通用成功响应。"""

    success: bool


def _to_response(
    collection: Collection,
) -> CollectionResponse:
    """将 Collection Domain 对象转换为 API 响应。

    Args:
        collection: Collection Domain 对象。

    Returns:
        Collection API 响应。
    """
    return CollectionResponse(
        collectionId=collection.collection_id,
        name=collection.name,
        fileCount=len(collection.files),
    )


@router.get(
    "",
    response_model=list[CollectionResponse],
)
def get_collections(
    offset: int = Query(
        default=0,
        ge=0,
    ),
    limit: int = Query(
        default=20,
        ge=1,
        le=100,
    ),
    keywords: list[str] | None = Query(
        default=None,
    ),
    library: Library = Depends(
        require_library
    ),
) -> list[CollectionResponse]:
    """查询 Collection 列表。

    支持 offset / limit 分页，以及多个 keyword 的 AND 模糊匹配。
    """
    collections = library.collections

    if keywords:
        normalized_keywords = [
            keyword.strip().casefold()
            for keyword in keywords
            if keyword.strip()
        ]

        if normalized_keywords:
            collections = [
                collection
                for collection in collections
                if all(
                    keyword in collection.name.casefold()
                    for keyword in normalized_keywords
                )
            ]

    page = collections[
        offset : offset + limit
    ]

    return [
        _to_response(collection)
        for collection in page
    ]


@router.post(
    "",
    response_model=CollectionResponse,
)
def create_collection(
    request: CreateCollectionRequest,
    library: Library = Depends(
        require_library
    ),
) -> CollectionResponse:
    """创建 Collection。"""
    if not request.name.strip():
        raise HTTPException(
            status_code=400,
            detail="Collection name cannot be empty",
        )

    collection = collection_workspace.create_collection(
        request.name
    )

    if collection is None:
        raise HTTPException(
            status_code=400,
            detail="Collection could not be created",
        )

    return _to_response(collection)


@router.patch(
    "/{collection_id}",
    response_model=CollectionResponse,
)
def rename_collection(
    collection_id: str,
    request: RenameCollectionRequest,
    library: Library = Depends(
        require_library
    ),
) -> CollectionResponse:
    """修改 Collection display name。"""
    collection = library.find_collection(
        collection_id
    )

    if collection is None:
        raise HTTPException(
            status_code=404,
            detail="Collection not found",
        )

    if not request.name.strip():
        raise HTTPException(
            status_code=400,
            detail="Collection name cannot be empty",
        )

    collection_workspace.rename_collection(
        collection_id,
        request.name,
    )

    return _to_response(collection)


@router.delete(
    "/{collection_id}",
    response_model=SuccessResponse,
)
def delete_collection(
    collection_id: str,
    library: Library = Depends(
        require_library
    ),
) -> SuccessResponse:
    """删除 Collection。"""
    if library.find_collection(collection_id) is None:
        raise HTTPException(
            status_code=404,
            detail="Collection not found",
        )

    if not collection_workspace.delete_collection(
        collection_id
    ):
        raise HTTPException(
            status_code=404,
            detail="Collection not found",
        )

    return SuccessResponse(
        success=True,
    )


@router.patch(
    "/{collection_id}/position",
    response_model=SuccessResponse,
)
def move_collection(
    collection_id: str,
    request: MoveCollectionRequest,
    library: Library = Depends(
        require_library
    ),
) -> SuccessResponse:
    """调整 Collection 顺序。"""
    if library.find_collection(collection_id) is None:
        raise HTTPException(
            status_code=404,
            detail="Collection not found",
        )

    if request.afterCollectionId == collection_id:
        raise HTTPException(
            status_code=400,
            detail="Cannot move collection after itself",
        )

    if (
        request.afterCollectionId is not None
        and library.find_collection(
            request.afterCollectionId
        )
        is None
    ):
        raise HTTPException(
            status_code=404,
            detail="Target collection not found",
        )

    collection_workspace.move_collection(
        collection_id,
        request.afterCollectionId,
    )

    return SuccessResponse(
        success=True,
    )