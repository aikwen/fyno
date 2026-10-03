"""Fyno Library File 操作。

该模块负责协调 File 的领域状态、Workspace 物理文件以及
`.fyno/library.json` 元数据。

职责范围：
- 创建 File。
- 读取 File Markdown 内容。
- 修改 File Markdown 内容。
- 修改 File display name。
- 删除 File。
- 调整 File 顺序。

该模块不负责：
- Workspace 生命周期管理。
- Collection 操作。
- FastAPI 请求和响应处理。
"""

from pathlib import Path

from ..domain.file import LibraryFile
from ..domain.library import Library
from ..storage import filesystem
from ..storage import metadata
from .workspace import get_library, get_workspace


def create_file(
    collection_id: str,
    name: str,
) -> LibraryFile | None:
    """创建 File。

    创建成功后会同时创建对应的 Markdown 文件，并将 File 追加到
    Collection 末尾。

    Args:
        collection_id: File 所属的 Collection ID。
        name: File display name。

    Returns:
        创建成功时返回新的 LibraryFile；Collection 不存在或名称为空时
        返回 None。

    Raises:
        RuntimeError: 当前 Workspace 或 Library 尚未初始化时抛出。
        OSError: 创建物理文件或保存 Metadata 失败时抛出。
    """
    name = name.strip()

    if not name:
        return None

    workspace, library = _require_runtime()

    collection = library.find_collection(
        collection_id
    )

    if collection is None:
        return None

    file_id = filesystem.generate_file_id()

    file = LibraryFile(
        file_id=file_id,
        name=name,
    )

    filesystem.create_file(
        workspace,
        collection_id,
        file_id,
    )

    if not collection.add_file(file):
        filesystem.delete_file(
            workspace,
            collection_id,
            file_id,
        )
        return None

    try:
        metadata.save_library(
            workspace,
            library,
        )
    except OSError:
        collection.remove_file(
            file_id
        )

        try:
            filesystem.delete_file(
                workspace,
                collection_id,
                file_id,
            )
        except OSError:
            pass

        raise

    return file


def read_file_content(
    collection_id: str,
    file_id: str,
) -> str | None:
    """读取 File Markdown 内容。

    只有当前 Library 中存在对应 Collection 和 File 时才会尝试读取
    Workspace 中的物理 Markdown 文件。

    Args:
        collection_id: File 所属的 Collection ID。
        file_id: File ID。

    Returns:
        物理 Markdown 文件存在时返回其 UTF-8 文本内容；
        Collection、File 或物理文件不存在时返回 None。

    Raises:
        RuntimeError: 当前 Workspace 或 Library 尚未初始化时抛出。
        OSError: 读取物理文件失败时抛出。
        UnicodeError: Markdown 文件不是有效 UTF-8 文本时抛出。
    """
    workspace, library = _require_runtime()

    collection = library.find_collection(
        collection_id
    )

    if collection is None:
        return None

    if collection.find_file(file_id) is None:
        return None

    return filesystem.read_file_content(
        workspace,
        collection_id,
        file_id,
    )


def write_file_content(
    collection_id: str,
    file_id: str,
    content: str,
) -> bool:
    """修改 File Markdown 内容。

    只有当前 Library 中存在对应 Collection 和 File，并且 Workspace
    中对应的物理 Markdown 文件仍然存在时才会执行写入。

    File 内容允许为空字符串。

    Args:
        collection_id: File 所属的 Collection ID。
        file_id: File ID。
        content: 新的完整 Markdown 内容。

    Returns:
        写入成功时返回 True；Collection、File 或物理文件不存在时
        返回 False。

    Raises:
        RuntimeError: 当前 Workspace 或 Library 尚未初始化时抛出。
        OSError: 写入物理文件失败时抛出。
    """
    workspace, library = _require_runtime()

    collection = library.find_collection(
        collection_id
    )

    if collection is None:
        return False

    if collection.find_file(file_id) is None:
        return False

    return filesystem.write_file_content(
        workspace,
        collection_id,
        file_id,
        content,
    )


def rename_file(
    collection_id: str,
    file_id: str,
    name: str,
) -> bool:
    """修改 File display name。

    File display name 与物理 Markdown 文件名无关，因此该操作只修改
    领域状态和 Metadata。

    Args:
        collection_id: File 所属的 Collection ID。
        file_id: File ID。
        name: 新的 display name。

    Returns:
        名称实际发生变化时返回 True；Collection 或 File 不存在、名称为空
        或名称没有变化时返回 False。

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

    file = collection.find_file(
        file_id
    )

    if file is None:
        return False

    old_name = file.name

    if not file.rename(name):
        return False

    try:
        metadata.save_library(
            workspace,
            library,
        )
    except OSError:
        file.name = old_name
        raise

    return True


def delete_file(
    collection_id: str,
    file_id: str,
) -> bool:
    """删除 File。

    删除操作首先删除对应的物理 Markdown 文件，然后更新 Collection
    领域状态并保存 Metadata。

    如果 Metadata 保存失败，会恢复当前运行时领域状态。此时物理文件已经
    被删除，后续可通过 Rebuild / Repair 清理 Metadata 中残留的 File。

    Args:
        collection_id: File 所属的 Collection ID。
        file_id: 要删除的 File ID。

    Returns:
        删除成功时返回 True；Collection 或 File 不存在时返回 False。

    Raises:
        RuntimeError: 当前 Workspace 或 Library 尚未初始化时抛出。
        OSError: 物理文件删除或 Metadata 保存失败时抛出。
    """
    workspace, library = _require_runtime()

    collection = library.find_collection(
        collection_id
    )

    if collection is None:
        return False

    if collection.find_file(file_id) is None:
        return False

    old_files = list(
        collection.files
    )

    # 先删除真实数据。
    # 如果物理删除失败，Domain 和 Metadata 都不会发生变化。
    filesystem.delete_file(
        workspace,
        collection_id,
        file_id,
    )

    if not collection.remove_file(
        file_id
    ):
        return False

    try:
        metadata.save_library(
            workspace,
            library,
        )
    except OSError:
        # Metadata 没有成功提交，恢复 Runtime，使其继续与 Metadata 一致。
        # 此时物理文件已经删除，后续 Repair 会清理 Metadata 中的残留。
        collection.replace_files(
            old_files
        )
        raise

    return True


def move_file(
    collection_id: str,
    file_id: str,
    after_file_id: str | None,
) -> bool:
    """调整 File 在 Collection 中的顺序。

    当 after_file_id 为 None 时，将 File 移动到第一位；
    否则移动到指定 File 之后。

    Args:
        collection_id: File 所属的 Collection ID。
        file_id: 要移动的 File ID。
        after_file_id: 目标 File ID，None 表示第一位。

    Returns:
        顺序实际发生变化时返回 True；Collection 不存在、操作无效或位置
        没有变化时返回 False。

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

    old_files = list(
        collection.files
    )

    if not collection.move_file(
        file_id,
        after_file_id,
    ):
        return False

    try:
        metadata.save_library(
            workspace,
            library,
        )
    except OSError:
        collection.replace_files(
            old_files
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