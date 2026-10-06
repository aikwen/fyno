"""Fyno Library Workspace 文件系统操作。

该模块负责直接操作 Workspace 中由 Fyno 管理的 Collection 和 File。

Fyno 管理的物理结构：

    workspace/
    ├── .fyno/
    │   └── library.json
    ├── c<nanosecond_timestamp>/
    │   ├── f<nanosecond_timestamp>.md
    │   └── ...
    └── ...

职责范围：
- 扫描 Workspace 中合法的 Collection 和 File。
- 基于当前纳秒时间生成 Collection/File ID。
- 创建和删除 Collection 目录。
- 创建、读取、写入和删除 Markdown 文件。
- 修改 File 的物理 ID。
- 从 Markdown 中读取一级标题。

该模块不负责：
- `.fyno/library.json` 的读取和写入。
- Collection/File 的 display name 管理。
- Library 领域对象的修改。
- Rebuild / Repair 的整体流程。

Rebuild / Repair 应由上层根据 metadata 与本模块扫描得到的真实磁盘状态进行协调。
"""

import os
import re
import shutil
import tempfile
import threading
import time
from pathlib import Path


_ID_DIGITS = 19

_COLLECTION_ID_PATTERN = re.compile(
    rf"^c\d{{{_ID_DIGITS}}}$"
)
_FILE_ID_PATTERN = re.compile(
    rf"^f\d{{{_ID_DIGITS}}}$"
)
_FILE_NAME_PATTERN = re.compile(
    rf"^(f\d{{{_ID_DIGITS}}})\.md$"
)

_id_lock = threading.Lock()

_last_collection_id = 0
_last_file_id = 0


def _is_collection_id(value: str) -> bool:
    """判断字符串是否为合法的 Collection ID。

    Args:
        value: 要检查的字符串。

    Returns:
        符合 `c + 19 位数字` 格式时返回 True。
    """
    return _COLLECTION_ID_PATTERN.fullmatch(value) is not None


def _is_file_id(value: str) -> bool:
    """判断字符串是否为合法的 File ID。

    Args:
        value: 要检查的字符串。

    Returns:
        符合 `f + 19 位数字` 格式时返回 True。
    """
    return _FILE_ID_PATTERN.fullmatch(value) is not None


def _collection_path(
    workspace: Path,
    collection_id: str,
) -> Path:
    """构造 Collection 的物理目录路径。

    Args:
        workspace: Workspace 根目录。
        collection_id: Collection ID。

    Returns:
        Collection 对应的目录路径。

    Raises:
        ValueError: Collection ID 格式不合法时抛出。
    """
    if not _is_collection_id(collection_id):
        raise ValueError(
            f"Invalid collection ID: {collection_id}"
        )

    return workspace / collection_id


def _file_path(
    workspace: Path,
    collection_id: str,
    file_id: str,
) -> Path:
    """构造 File 的物理文件路径。

    Args:
        workspace: Workspace 根目录。
        collection_id: File 所属的 Collection ID。
        file_id: File ID。

    Returns:
        File 对应的 Markdown 文件路径。

    Raises:
        ValueError: Collection ID 或 File ID 格式不合法时抛出。
    """
    if not _is_file_id(file_id):
        raise ValueError(
            f"Invalid file ID: {file_id}"
        )

    return _collection_path(
        workspace,
        collection_id,
    ) / f"{file_id}.md"


def scan_workspace(
    workspace: Path,
) -> dict[str, list[str]]:
    """扫描 Workspace 中由 Fyno 管理的 Collection 和 File。

    只有符合 `c + 19 位数字` 的一级目录会被识别为 Collection。
    Collection 下只有符合 `f + 19 位数字 + .md` 的普通文件会被识别为 File。

    其他目录和文件，包括 `.fyno`、`.git` 等隐藏目录，会自然被忽略。

    扫描结果按照 ID 升序返回，以保证不同平台上的结果稳定。

    Args:
        workspace: Workspace 根目录。

    Returns:
        Collection ID 到 File ID 列表的映射。

    Raises:
        OSError: Workspace 无法读取时抛出。
    """
    collections: dict[str, list[str]] = {}

    collection_entries = sorted(
        (
            entry
            for entry in workspace.iterdir()
            if entry.is_dir()
            and _is_collection_id(entry.name)
        ),
        key=lambda entry: entry.name,
    )

    for collection_entry in collection_entries:
        file_ids: list[str] = []

        file_entries = sorted(
            (
                entry
                for entry in collection_entry.iterdir()
                if entry.is_file()
                and _FILE_NAME_PATTERN.fullmatch(
                    entry.name
                )
            ),
            key=lambda entry: entry.name,
        )

        for file_entry in file_entries:
            match = _FILE_NAME_PATTERN.fullmatch(
                file_entry.name
            )

            if match is not None:
                file_ids.append(
                    match.group(1)
                )

        collections[
            collection_entry.name
        ] = file_ids

    return collections


def generate_collection_id() -> str:
    """生成新的 Collection ID。

    ID 基于当前 Unix 纳秒时间戳生成。为了避免同一进程中极短时间内
    连续生成相同时间值，会同时参考最近一次生成的 Collection ID，
    保证当前进程内单调递增。

    Returns:
        新的 Collection ID。
    """
    global _last_collection_id

    with _id_lock:
        numeric_id = max(
            time.time_ns(),
            _last_collection_id + 1,
        )

        _last_collection_id = numeric_id

    return f"c{numeric_id}"


def generate_file_id() -> str:
    """生成新的 File ID。

    ID 基于当前 Unix 纳秒时间戳生成。为了避免同一进程中极短时间内
    连续生成相同时间值，会同时参考最近一次生成的 File ID，
    保证当前进程内单调递增。

    Returns:
        新的 File ID。
    """
    global _last_file_id

    with _id_lock:
        numeric_id = max(
            time.time_ns(),
            _last_file_id + 1,
        )

        _last_file_id = numeric_id

    return f"f{numeric_id}"


def create_collection(
    workspace: Path,
    collection_id: str,
) -> None:
    """创建 Collection 物理目录。

    Args:
        workspace: Workspace 根目录。
        collection_id: 要创建的 Collection ID。

    Raises:
        ValueError: Collection ID 格式不合法时抛出。
        FileExistsError: Collection 已存在时抛出。
        OSError: Collection 目录创建失败时抛出。
    """
    path = _collection_path(
        workspace,
        collection_id,
    )

    path.mkdir()


def delete_collection(
    workspace: Path,
    collection_id: str,
) -> None:
    """删除 Collection 及其全部物理内容。

    Args:
        workspace: Workspace 根目录。
        collection_id: 要删除的 Collection ID。

    Raises:
        ValueError: Collection ID 格式不合法时抛出。
        FileNotFoundError: Collection 不存在时抛出。
        OSError: 删除失败时抛出。
    """
    path = _collection_path(
        workspace,
        collection_id,
    )

    if not path.is_dir():
        raise FileNotFoundError(
            path
        )

    shutil.rmtree(
        path
    )


def create_file(
    workspace: Path,
    collection_id: str,
    file_id: str,
) -> None:
    """创建空的 Markdown 文件。

    Args:
        workspace: Workspace 根目录。
        collection_id: File 所属 Collection ID。
        file_id: 要创建的 File ID。

    Raises:
        ValueError: Collection ID 或 File ID 格式不合法时抛出。
        FileNotFoundError: Collection 不存在时抛出。
        FileExistsError: File 已存在时抛出。
        OSError: 文件创建失败时抛出。
    """
    collection_path = _collection_path(
        workspace,
        collection_id,
    )

    if not collection_path.is_dir():
        raise FileNotFoundError(
            collection_path
        )

    path = _file_path(
        workspace,
        collection_id,
        file_id,
    )

    # 使用 x 模式保证已有文件不会被意外覆盖。
    with path.open(
        "x",
        encoding="utf-8",
    ):
        pass


def read_file_content(
    workspace: Path,
    collection_id: str,
    file_id: str,
) -> str | None:
    """读取 Markdown 文件完整内容。

    Args:
        workspace: Workspace 根目录。
        collection_id: File 所属 Collection ID。
        file_id: File ID。

    Returns:
        File 存在时返回完整 UTF-8 文本内容；
        File 不存在时返回 None。

    Raises:
        ValueError: Collection ID 或 File ID 格式不合法时抛出。
        OSError: 文件读取失败时抛出。
        UnicodeError: 文件不是有效 UTF-8 文本时抛出。
    """
    path = _file_path(
        workspace,
        collection_id,
        file_id,
    )

    if not path.is_file():
        return None

    return path.read_text(
        encoding="utf-8",
    )


def write_file_content(
    workspace: Path,
    collection_id: str,
    file_id: str,
    content: str,
) -> bool:
    """覆盖写入 Markdown 文件完整内容。

    写入前会检查目标 File 是否真实存在。写入过程通过同目录临时文件和
    `os.replace` 完成，以避免覆盖过程中异常导致原文件只写入部分内容。

    Args:
        workspace: Workspace 根目录。
        collection_id: File 所属 Collection ID。
        file_id: File ID。
        content: 新的完整 Markdown 内容。

    Returns:
        写入成功时返回 True；
        File 不存在时返回 False。

    Raises:
        ValueError: Collection ID 或 File ID 格式不合法时抛出。
        OSError: 临时文件创建、写入或替换失败时抛出。
        UnicodeError: 内容无法按 UTF-8 编码时抛出。
    """
    path = _file_path(
        workspace,
        collection_id,
        file_id,
    )

    if not path.is_file():
        return False

    temp_path: Path | None = None

    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            newline="",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as temp_file:
            temp_file.write(
                content
            )
            temp_file.flush()

            os.fsync(
                temp_file.fileno()
            )

            temp_path = Path(
                temp_file.name
            )

        os.replace(
            temp_path,
            path,
        )

        temp_path = None
    finally:
        if (
            temp_path is not None
            and temp_path.exists()
        ):
            try:
                temp_path.unlink()
            except OSError:
                pass

    return True


def delete_file(
    workspace: Path,
    collection_id: str,
    file_id: str,
) -> None:
    """删除 Markdown 文件。

    Args:
        workspace: Workspace 根目录。
        collection_id: File 所属 Collection ID。
        file_id: 要删除的 File ID。

    Raises:
        ValueError: Collection ID 或 File ID 格式不合法时抛出。
        FileNotFoundError: File 不存在时抛出。
        OSError: 文件删除失败时抛出。
    """
    path = _file_path(
        workspace,
        collection_id,
        file_id,
    )

    path.unlink()


def rename_file_id(
    workspace: Path,
    collection_id: str,
    old_file_id: str,
    new_file_id: str,
) -> None:
    """修改 File 的物理 ID。

    该操作主要用于 Rebuild / Repair 中解决重复 File ID。
    普通 display name rename 不应调用此函数，因为 display name
    与物理 File ID 相互独立。

    Args:
        workspace: Workspace 根目录。
        collection_id: File 所属 Collection ID。
        old_file_id: 当前 File ID。
        new_file_id: 新的 File ID。

    Raises:
        ValueError: Collection ID 或 File ID 格式不合法时抛出。
        FileNotFoundError: 原 File 不存在时抛出。
        FileExistsError: 新 File ID 已存在于当前 Collection 时抛出。
        OSError: 文件重命名失败时抛出。
    """
    source = _file_path(
        workspace,
        collection_id,
        old_file_id,
    )

    target = _file_path(
        workspace,
        collection_id,
        new_file_id,
    )

    if not source.is_file():
        raise FileNotFoundError(
            source
        )

    if target.exists():
        raise FileExistsError(
            target
        )

    source.rename(
        target
    )


def read_markdown_title(
    workspace: Path,
    collection_id: str,
    file_id: str,
) -> str | None:
    """读取 Markdown 文件中的第一个一级标题。

    只有形如 `# Title` 的 ATX 一级标题会被识别为文件 display name。
    `## Title` 等其他层级标题不会被识别。

    Args:
        workspace: Workspace 根目录。
        collection_id: File 所属 Collection ID。
        file_id: File ID。

    Returns:
        找到一级标题时返回去除首尾空白后的标题文本；
        文件中不存在有效一级标题时返回 None。

    Raises:
        ValueError: Collection ID 或 File ID 格式不合法时抛出。
        FileNotFoundError: File 不存在时抛出。
        OSError: 文件读取失败时抛出。
    """
    path = _file_path(
        workspace,
        collection_id,
        file_id,
    )

    with path.open(
        "r",
        encoding="utf-8",
        errors="replace",
    ) as file:
        for line in file:
            if not line.startswith(
                "# "
            ):
                continue

            title = line[2:].strip()

            if title:
                return title

    return None
