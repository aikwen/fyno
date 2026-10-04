"""Fyno Library API。

该模块负责聚合 Library 下的各个 API Router，并统一添加
`/library` 路由前缀。
"""

from fastapi import APIRouter

from .collection import router as collection_router
from .file import router as file_router
from .sync import router as sync_router
from .workspace import router as workspace_router


router = APIRouter(
    prefix="/library",
)

router.include_router(
    collection_router,
)

router.include_router(
    file_router,
)

router.include_router(
    sync_router,
)

router.include_router(
    workspace_router,
)
