"""Fyno global API。

该模块负责聚合 Fyno 全局基础能力相关 Router。
"""

from fastapi import APIRouter

from .filesystem import router as filesystem_router


router = APIRouter()

router.include_router(
    filesystem_router,
)