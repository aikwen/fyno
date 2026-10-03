"""Fyno Library Workspace 生命周期管理。

该模块负责维护当前 Library Workspace 的运行时状态，并协调 Domain、
Metadata Storage 和真实文件系统之间的加载与重建过程。

职责范围：
- 初始化当前 Workspace。
- 获取和切换当前 Workspace。
- 维护当前内存中的 Library。
- Reload：直接重新读取 `.fyno/library.json`。
- Rebuild：根据真实文件系统创建或修复 `.fyno/library.json`。
- Repair：保留有效 Metadata，并修复与真实文件系统之间的不一致。

该模块不负责：
- Collection 的日常创建、删除、重命名和排序。
- File 的日常创建、删除、重命名和排序。
- FastAPI 请求和响应处理。
"""

import json
import os
import secrets
import time
from pathlib import Path

from ...config.library import (
    LibraryConfigKey,
    get_config,
    set_config,
)
from ..domain.collection import Collection
from ..domain.file import LibraryFile
from ..domain.library import Library
from ..storage import filesystem
from ..storage import metadata


_current_workspace: Path | None = None
_current_library: Library | None = None


def get_workspace() -> Path | None:
    """获取当前运行时 Workspace。

    Returns:
        当前 Workspace 路径；尚未设置时返回 None。
    """
    return _current_workspace


def get_library() -> Library | None:
    """获取当前运行时 Library。

    Returns:
        当前 Library；尚未加载时返回 None。
    """
    return _current_library


def initialize() -> bool:
    """根据 Fyno 应用配置初始化当前 Workspace。

    配置中没有 Workspace，或配置的路径已经无效时，不加载任何
    Workspace。该函数不会自动修改或重建 `.fyno`。

    Returns:
        成功恢复有效 Workspace 时返回 True，否则返回 False.

    Raises:
        OSError: 读取 Workspace Metadata 失败时抛出。
        json.JSONDecodeError: Metadata JSON 损坏时抛出。
        ValueError: Metadata 数据结构不合法时抛出。
    """
    global _current_workspace
    global _current_library

    directory = get_config(
        LibraryConfigKey.WORKSPACE
    )

    if not isinstance(directory, str):
        _current_workspace = None
        _current_library = None
        return False

    workspace = Path(
        os.path.expanduser(directory)
    )

    if (
        not workspace.is_absolute()
        or not workspace.is_dir()
    ):
        _current_workspace = None
        _current_library = None
        return False

    library = metadata.load_library(workspace)

    _current_workspace = workspace
    _current_library = library

    return True


def set_workspace(
    directory: str | Path,
) -> Library | None:
    """切换当前 Workspace。

    Workspace 必须是存在的绝对目录。目标 Workspace 没有
    `.fyno/library.json` 时仍然允许切换，此时当前 Library 为 None，
    后续可以通过 rebuild() 初始化。

    Args:
        directory: 新的 Workspace 路径。

    Returns:
        目标 Workspace 已有 Metadata 时返回加载后的 Library；
        尚未初始化时返回 None。

    Raises:
        ValueError: Workspace 路径为空、不是绝对路径或不是有效目录时抛出。
        OSError: Metadata 读取失败时抛出。
        json.JSONDecodeError: Metadata JSON 损坏时抛出。
    """
    global _current_workspace
    global _current_library

    raw_directory = str(directory).strip()

    if not raw_directory:
        raise ValueError(
            "Workspace directory cannot be empty"
        )

    workspace = Path(
        os.path.expanduser(raw_directory)
    )

    if not workspace.is_absolute():
        raise ValueError(
            "Workspace directory must be an absolute path"
        )

    if not workspace.exists():
        raise ValueError(
            "Workspace directory does not exist"
        )

    if not workspace.is_dir():
        raise ValueError(
            "Workspace path is not a directory"
        )

    # 先尝试读取目标 Workspace。
    # 读取失败时不修改当前 runtime 和 application config。
    library = metadata.load_library(workspace)

    _current_workspace = workspace
    _current_library = library

    set_config(
        LibraryConfigKey.WORKSPACE,
        str(workspace),
    )

    return library


def reload() -> Library | None:
    """重新读取当前 Workspace 的 Metadata。

    Reload 只重新读取 `.fyno/library.json`，不会扫描真实文件系统，
    也不会执行任何 Repair。

    Returns:
        重新加载后的 Library；Metadata 不存在时返回 None。

    Raises:
        RuntimeError: 当前没有 Workspace 时抛出。
        OSError: Metadata 读取失败时抛出。
        json.JSONDecodeError: Metadata JSON 损坏时抛出。
        ValueError: Metadata 数据结构不合法时抛出。
    """
    global _current_library

    workspace = _require_workspace()

    library = metadata.load_library(workspace)
    _current_library = library

    return library


def rebuild() -> Library:
    """重建或修复当前 Workspace 的 Library Metadata。

    如果 `.fyno/library.json` 不存在或无法正常解析，则完全根据真实
    Workspace 文件系统重新构建 Library。

    如果 Metadata 可以正常读取，则以已有 Metadata 为基础进行 Repair：
    - 删除磁盘中已经不存在的 Collection/File。
    - 保留仍然存在对象的 display name 和顺序。
    - 将 Metadata 中不存在的新对象追加到末尾。
    - 修复跨 Collection 重复的 File ID。
    - 新 File 优先使用 Markdown 一级标题作为 display name。

    Returns:
        重建或修复完成后的 Library。

    Raises:
        RuntimeError: 当前没有 Workspace 时抛出。
        OSError: Workspace 扫描、文件修复或 Metadata 保存失败时抛出。
    """
    global _current_library

    workspace = _require_workspace()

    try:
        old_library = metadata.load_library(
            workspace
        )
    except (json.JSONDecodeError, ValueError):
        old_library = None

    if old_library is None:
        library = _rebuild_from_filesystem(
            workspace
        )
    else:
        library = _repair(
            workspace,
            old_library,
        )

    metadata.save_library(
        workspace,
        library,
    )

    _current_library = library
    return library


def _require_workspace() -> Path:
    """获取当前 Workspace，并确保其已经设置。

    Returns:
        当前 Workspace。

    Raises:
        RuntimeError: 当前没有 Workspace 时抛出。
    """
    if _current_workspace is None:
        raise RuntimeError(
            "Library workspace is not configured"
        )

    return _current_workspace


def _rebuild_from_filesystem(
    workspace: Path,
) -> Library:
    """完全根据真实 Workspace 文件系统构建 Library。

    Args:
        workspace: Workspace 根目录。

    Returns:
        根据真实文件系统构建的 Library。
    """
    snapshot = filesystem.scan_workspace(
        workspace
    )

    snapshot, _ = _repair_duplicate_file_ids(
        workspace,
        snapshot,
    )

    collections: list[Collection] = []

    for collection_id, file_ids in snapshot.items():
        files = [
            LibraryFile(
                file_id=file_id,
                name=_resolve_file_name(
                    workspace,
                    collection_id,
                    file_id,
                ),
            )
            for file_id in file_ids
        ]

        collections.append(
            Collection(
                collection_id=collection_id,
                name=_generate_collection_name(),
                files=files,
            )
        )

    return Library(
        collections=collections
    )


def _repair(
    workspace: Path,
    old_library: Library,
) -> Library:
    """修复 Metadata 与真实文件系统之间的不一致。

    Args:
        workspace: Workspace 根目录。
        old_library: 当前 Metadata 中记录的 Library。

    Returns:
        修复后的 Library。
    """
    snapshot = filesystem.scan_workspace(
        workspace
    )

    preferred_owner = _build_preferred_file_owner(
        old_library,
        snapshot,
    )

    snapshot, renamed_files = (
        _repair_duplicate_file_ids(
            workspace,
            snapshot,
            preferred_owner,
        )
    )

    repaired_collections: list[Collection] = []
    existing_collection_ids: set[str] = set()

    for old_collection in old_library.collections:
        collection_id = (
            old_collection.collection_id
        )

        if collection_id not in snapshot:
            continue

        existing_collection_ids.add(
            collection_id
        )

        available_file_ids = set(
            snapshot[collection_id]
        )
        added_file_ids: set[str] = set()

        files: list[LibraryFile] = []

        for old_file in old_collection.files:
            old_file_id = old_file.file_id

            file_id = renamed_files.get(
                (collection_id, old_file_id),
                old_file_id,
            )

            if file_id not in available_file_ids:
                continue

            if file_id in added_file_ids:
                continue

            files.append(
                LibraryFile(
                    file_id=file_id,
                    name=old_file.name,
                )
            )
            added_file_ids.add(file_id)

        # Metadata 中不存在，但磁盘真实存在的 File 追加到末尾。
        for file_id in snapshot[collection_id]:
            if file_id in added_file_ids:
                continue

            files.append(
                LibraryFile(
                    file_id=file_id,
                    name=_resolve_file_name(
                        workspace,
                        collection_id,
                        file_id,
                    ),
                )
            )
            added_file_ids.add(file_id)

        repaired_collections.append(
            Collection(
                collection_id=collection_id,
                name=old_collection.name,
                files=files,
            )
        )

    # Workspace 中存在但 Metadata 中不存在的 Collection 追加到末尾。
    for collection_id, file_ids in snapshot.items():
        if collection_id in existing_collection_ids:
            continue

        files = [
            LibraryFile(
                file_id=file_id,
                name=_resolve_file_name(
                    workspace,
                    collection_id,
                    file_id,
                ),
            )
            for file_id in file_ids
        ]

        repaired_collections.append(
            Collection(
                collection_id=collection_id,
                name=_generate_collection_name(),
                files=files,
            )
        )

    return Library(
        collections=repaired_collections
    )


def _build_preferred_file_owner(
    library: Library,
    snapshot: dict[str, list[str]],
) -> dict[str, str]:
    """确定重复 File ID 修复时优先保留 ID 的 Collection。

    已经存在于 Metadata 且磁盘仍然存在的 File 优先保留原 ID。
    如果 Metadata 本身存在重复 File ID，则按 Metadata 中首次出现的
    Collection 为准。

    Args:
        library: 当前 Metadata 中的 Library。
        snapshot: 当前真实文件系统快照。

    Returns:
        File ID 到优先 Collection ID 的映射。
    """
    preferred_owner: dict[str, str] = {}

    for collection in library.collections:
        collection_id = collection.collection_id

        if collection_id not in snapshot:
            continue

        physical_files = set(
            snapshot[collection_id]
        )

        for file in collection.files:
            if file.file_id not in physical_files:
                continue

            preferred_owner.setdefault(
                file.file_id,
                collection_id,
            )

    return preferred_owner


def _repair_duplicate_file_ids(
    workspace: Path,
    snapshot: dict[str, list[str]],
    preferred_owner: dict[str, str] | None = None,
) -> tuple[
    dict[str, list[str]],
    dict[tuple[str, str], str],
]:
    """修复不同 Collection 之间重复的 File ID。

    Args:
        workspace: Workspace 根目录。
        snapshot: 当前文件系统快照。
        preferred_owner: File ID 对应的优先保留 Collection。

    Returns:
        修复后的文件系统快照，以及 `(collection_id, old_file_id)` 到
        `new_file_id` 的重命名映射。
    """
    preferred_owner = preferred_owner or {}

    reserved_ids = {
        file_id
        for file_ids in snapshot.values()
        for file_id in file_ids
    }

    maximum = max(
        (
            int(file_id[1:])
            for file_id in reserved_ids
        ),
        default=0,
    )

    next_numeric_id = max(
        time.time_ns(),
        maximum + 1,
    )

    used_ids: set[str] = set()
    renamed_files: dict[
        tuple[str, str],
        str,
    ] = {}

    repaired_snapshot: dict[
        str,
        list[str],
    ] = {}

    for collection_id, file_ids in snapshot.items():
        repaired_file_ids: list[str] = []

        for file_id in file_ids:
            owner = preferred_owner.get(
                file_id
            )

            should_rename = (
                file_id in used_ids
                or (
                    owner is not None
                    and owner != collection_id
                )
            )

            if not should_rename:
                used_ids.add(file_id)
                repaired_file_ids.append(
                    file_id
                )
                continue

            while True:
                new_file_id = (
                    f"f{next_numeric_id}"
                )
                next_numeric_id += 1

                if (
                    new_file_id not in reserved_ids
                    and new_file_id not in used_ids
                ):
                    break

            filesystem.rename_file_id(
                workspace,
                collection_id,
                file_id,
                new_file_id,
            )

            reserved_ids.add(new_file_id)
            used_ids.add(new_file_id)

            renamed_files[
                (collection_id, file_id)
            ] = new_file_id

            repaired_file_ids.append(
                new_file_id
            )

        repaired_snapshot[
            collection_id
        ] = repaired_file_ids

    return (
        repaired_snapshot,
        renamed_files,
    )


def _resolve_file_name(
    workspace: Path,
    collection_id: str,
    file_id: str,
) -> str:
    """获取新发现 File 的默认 display name。

    优先使用 Markdown 中第一个一级标题；不存在有效标题时生成随机名称。

    Args:
        workspace: Workspace 根目录。
        collection_id: Collection ID。
        file_id: File ID。

    Returns:
        File display name。
    """
    title = filesystem.read_markdown_title(
        workspace,
        collection_id,
        file_id,
    )

    if title is not None:
        return title

    return _generate_file_name()


def _generate_collection_name() -> str:
    """生成 Rebuild 使用的 Collection 默认名称。

    Returns:
        形如 `collection-a1b2` 的随机名称。
    """
    return (
        f"collection-{secrets.token_hex(2)}"
    )


def _generate_file_name() -> str:
    """生成 Rebuild 使用的 File 默认名称。

    Returns:
        形如 `file-a1b2` 的随机名称。
    """
    return f"file-{secrets.token_hex(2)}"