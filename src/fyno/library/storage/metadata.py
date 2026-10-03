"""Fyno Library 元数据持久化。

该模块负责 Library 领域对象与 Workspace 中 `.fyno/library.json`
之间的序列化、反序列化和持久化。

职责范围：
- 读取 `.fyno/library.json` 并构建 Library 领域对象。
- 将 Library 领域对象序列化并写入 `.fyno/library.json`。
- 保证元数据文件写入过程的完整性。

该模块不负责：
- 扫描 Workspace 中的 Collection/File。
- 创建或删除 Collection 目录。
- 创建、删除或读取 Markdown 文件。
- Rebuild / Repair 逻辑。

真实 Workspace 文件系统操作由 storage.filesystem 模块负责。
"""

import json
import os
from pathlib import Path
from typing import Any

from ..domain.collection import Collection
from ..domain.file import LibraryFile
from ..domain.library import Library


_METADATA_VERSION = 1
_METADATA_DIRECTORY = ".fyno"
_METADATA_FILENAME = "library.json"


def _get_metadata_path(workspace: Path) -> Path:
    """获取指定 Workspace 的 Library 元数据文件路径。

    Args:
        workspace: Workspace 根目录。

    Returns:
        `.fyno/library.json` 的完整路径。
    """
    return workspace / _METADATA_DIRECTORY / _METADATA_FILENAME


def _serialize_library(library: Library) -> dict[str, Any]:
    """将 Library 领域对象序列化为元数据结构。

    Collection 和 File 在列表中的顺序会被完整保留，并作为 Fyno
    Library 的持久化顺序。

    Args:
        library: 要序列化的 Library。

    Returns:
        可直接进行 JSON 序列化的字典。
    """
    return {
        "version": _METADATA_VERSION,
        "collections": [
            {
                "collectionId": collection.collection_id,
                "name": collection.name,
                "files": [
                    {
                        "fileId": file.file_id,
                        "name": file.name,
                    }
                    for file in collection.files
                ],
            }
            for collection in library.collections
        ],
    }


def _deserialize_library(data: dict[str, Any]) -> Library:
    """将元数据结构反序列化为 Library 领域对象。

    Args:
        data: 从 `.fyno/library.json` 中读取的元数据。

    Returns:
        构建完成的 Library 领域对象。

    Raises:
        ValueError: 元数据版本不支持或数据结构不合法时抛出。
    """
    version = data.get("version")

    if version != _METADATA_VERSION:
        raise ValueError(
            f"Unsupported library metadata version: {version}"
        )

    collections_data = data.get("collections")

    if not isinstance(collections_data, list):
        raise ValueError("Invalid library metadata: collections must be a list")

    collections: list[Collection] = []

    for collection_data in collections_data:
        if not isinstance(collection_data, dict):
            raise ValueError(
                "Invalid library metadata: collection must be an object"
            )

        collection_id = collection_data.get("collectionId")
        name = collection_data.get("name")
        files_data = collection_data.get("files")

        if not isinstance(collection_id, str):
            raise ValueError(
                "Invalid library metadata: collectionId must be a string"
            )

        if not isinstance(name, str):
            raise ValueError(
                "Invalid library metadata: collection name must be a string"
            )

        if not isinstance(files_data, list):
            raise ValueError(
                "Invalid library metadata: files must be a list"
            )

        files: list[LibraryFile] = []

        for file_data in files_data:
            if not isinstance(file_data, dict):
                raise ValueError(
                    "Invalid library metadata: file must be an object"
                )

            file_id = file_data.get("fileId")
            file_name = file_data.get("name")

            if not isinstance(file_id, str):
                raise ValueError(
                    "Invalid library metadata: fileId must be a string"
                )

            if not isinstance(file_name, str):
                raise ValueError(
                    "Invalid library metadata: file name must be a string"
                )

            files.append(
                LibraryFile(
                    file_id=file_id,
                    name=file_name,
                )
            )

        collections.append(
            Collection(
                collection_id=collection_id,
                name=name,
                files=files,
            )
        )

    return Library(collections=collections)


def load_library(workspace: Path) -> Library | None:
    """从 Workspace 中加载 Library 元数据。

    Args:
        workspace: Workspace 根目录。

    Returns:
        元数据存在时返回对应的 Library；不存在时返回 None。

    Raises:
        json.JSONDecodeError: 元数据文件不是合法 JSON 时抛出。
        ValueError: 元数据结构或版本不合法时抛出。
        OSError: 元数据文件读取失败时抛出。
    """
    metadata_path = _get_metadata_path(workspace)

    if not metadata_path.exists():
        return None

    with metadata_path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    if not isinstance(data, dict):
        raise ValueError("Invalid library metadata: root must be an object")

    return _deserialize_library(data)


def save_library(workspace: Path, library: Library) -> None:
    """将 Library 元数据保存到 Workspace。

    如果 `.fyno` 目录不存在会自动创建。元数据首先写入临时文件，
    完成后通过原子替换更新正式文件，避免写入过程中产生不完整的
    `library.json`。

    Args:
        workspace: Workspace 根目录。
        library: 要保存的 Library。

    Raises:
        OSError: 创建目录、写入或替换元数据文件失败时抛出。
        TypeError: Library 序列化结果无法转换为 JSON 时抛出。
    """
    metadata_path = _get_metadata_path(workspace)
    metadata_path.parent.mkdir(parents=True, exist_ok=True)

    data = _serialize_library(library)
    temp_path = metadata_path.with_suffix(".tmp")

    try:
        with temp_path.open("w", encoding="utf-8") as file:
            json.dump(
                data,
                file,
                ensure_ascii=False,
                indent=4,
            )
            file.write("\n")
            file.flush()
            os.fsync(file.fileno())

        os.replace(temp_path, metadata_path)
    finally:
        if temp_path.exists():
            temp_path.unlink()