"""Fyno Library Collection 操作。

该模块负责协调 Collection 的领域状态、Workspace 物理目录以及
`.fyno/library.json` 元数据。

职责范围：
- 创建 Collection。
- 修改 Collection display name。
- 删除 Collection。
- 调整 Collection 顺序。

该模块不负责：
- Workspace 生命周期管理。
- File 操作。
- FastAPI 请求和响应处理。
"""

from pathlib import Path

from ..domain.collection import Collection
from ..domain.library import Library
from ..storage import filesystem
from ..storage import metadata
from .workspace import get_library, get_workspace


def create_collection(name: str) -> Collection | None:
    """创建 Collection。

    创建成功后会同时创建对应的物理目录，并将 Collection 追加到
    Library 末尾。

    Args:
        name: Collection display name。

    Returns:
        创建成功时返回新的 Collection；名称为空时返回 None。

    Raises:
        RuntimeError: 当前 Workspace 或 Library 尚未初始化时抛出。
        OSError: 创建目录或保存 Metadata 失败时抛出。
    """
    name = name.strip()

    if not name:
        return None

    workspace, library = _require_runtime()

    collection_id = filesystem.generate_collection_id()
    collection = Collection(
        collection_id=collection_id,
        name=name,
    )

    filesystem.create_collection(
        workspace,
        collection_id,
    )

    if not library.add_collection(collection):
        filesystem.delete_collection(
            workspace,
            collection_id,
        )
        return None

    try:
        metadata.save_library(
            workspace,
            library,
        )
    except OSError:
        library.remove_collection(
            collection_id
        )

        try:
            filesystem.delete_collection(
                workspace,
                collection_id,
            )
        except OSError:
            pass

        raise

    return collection


def rename_collection(
    collection_id: str,
    name: str,
) -> bool:
    """修改 Collection display name。

    Collection display name 与物理目录名无关，因此该操作只修改领域
    状态和 Metadata。

    Args:
        collection_id: Collection ID。
        name: 新的 display name。

    Returns:
        名称实际发生变化时返回 True；Collection 不存在、名称为空或
        名称没有变化时返回 False。

    Raises:
        RuntimeError: 当前 Workspace 或 Library 尚未初始化时抛出。
        OSError: Metadata 保存失败时抛出。
    """
    workspace, library = _require_runtime()

    collection = library.find_collection(
        collection_id
    )

    if collection is None:
        return False

    old_name = collection.name

    if not collection.rename(name):
        return False

    try:
        metadata.save_library(
            workspace,
            library,
        )
    except OSError:
        collection.name = old_name
        raise

    return True


def delete_collection(
    collection_id: str,
) -> bool:
    """删除 Collection。

    删除操作首先删除对应的物理目录，然后更新 Library 领域状态并保存
    Metadata。

    如果 Metadata 保存失败，会恢复当前运行时领域状态。此时物理目录已经
    被删除，后续可通过 Rebuild / Repair 清理 Metadata 中残留的 Collection。

    Args:
        collection_id: 要删除的 Collection ID。

    Returns:
        删除成功时返回 True；Collection 不存在时返回 False。

    Raises:
        RuntimeError: 当前 Workspace 或 Library 尚未初始化时抛出。
        OSError: 物理目录删除或 Metadata 保存失败时抛出。
    """
    workspace, library = _require_runtime()

    collection = library.find_collection(
        collection_id
    )

    if collection is None:
        return False

    old_collections = list(
        library.collections
    )

    # 先删除真实数据。
    # 如果物理删除失败，Domain 和 Metadata 都不会发生变化。
    filesystem.delete_collection(
        workspace,
        collection_id,
    )

    if not library.remove_collection(
        collection_id
    ):
        return False

    try:
        metadata.save_library(
            workspace,
            library,
        )
    except OSError:
        # Metadata 没有成功提交，恢复 Runtime，使其继续与 Metadata 一致。
        # 此时物理目录已经删除，后续 Repair 会清理 Metadata 中的残留。
        library.replace_collections(
            old_collections
        )
        raise

    return True


def move_collection(
    collection_id: str,
    after_collection_id: str | None,
) -> bool:
    """调整 Collection 顺序。

    当 after_collection_id 为 None 时，将 Collection 移动到第一位；
    否则移动到指定 Collection 之后。

    Args:
        collection_id: 要移动的 Collection ID。
        after_collection_id: 目标 Collection ID，None 表示第一位。

    Returns:
        顺序实际发生变化时返回 True；操作无效或位置没有变化时返回 False。

    Raises:
        RuntimeError: 当前 Workspace 或 Library 尚未初始化时抛出。
        OSError: Metadata 保存失败时抛出。
    """
    workspace, library = _require_runtime()

    old_collections = list(
        library.collections
    )

    if not library.move_collection(
        collection_id,
        after_collection_id,
    ):
        return False

    try:
        metadata.save_library(
            workspace,
            library,
        )
    except OSError:
        library.replace_collections(
            old_collections
        )
        raise

    return True


def _require_runtime() -> tuple[Path, Library]:
    """获取当前 Workspace 和 Library。

    Returns:
        当前 Workspace 和 Library。

    Raises:
        RuntimeError: Workspace 尚未设置或 Library 尚未初始化时抛出。
    """
    workspace = get_workspace()
    library = get_library()

    if workspace is None:
        raise RuntimeError(
            "Library workspace is not configured"
        )

    if library is None:
        raise RuntimeError(
            "Library is not initialized"
        )

    return workspace, library