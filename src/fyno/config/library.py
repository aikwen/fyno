import json
import os
from enum import StrEnum
from pathlib import Path
from typing import Any

from ..utils import fs


class LibraryConfigKey(StrEnum):
    """Library 模块支持的配置项。"""

    WORKSPACE = "workspace"


def _get_config_path() -> Path:
    """获取 Library 配置文件路径，并确保配置目录存在。

    Returns:
        Library 配置文件的绝对路径。
    """
    config_dir = fs.get_app_data_dir() / "config"
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir / "library.json"


def _load_config() -> dict[str, Any]:
    """读取完整的 Library 配置。

    配置文件不存在时返回空字典。

    Returns:
        当前 Library 配置。

    Raises:
        json.JSONDecodeError: 配置文件不是合法 JSON 时抛出。
        OSError: 读取配置文件失败时抛出。
    """
    config_path = _get_config_path()

    if not config_path.exists():
        return {}

    with config_path.open("r", encoding="utf-8") as file:
        return json.load(file)


def get_config(key: LibraryConfigKey) -> Any | None:
    """获取指定的 Library 配置项。

    Args:
        key: 要读取的配置项。

    Returns:
        对应配置值；配置文件或配置项不存在时返回 None。
    """
    config = _load_config()
    return config.get(str(key.value))


def set_config(key: LibraryConfigKey, value: Any) -> None:
    """设置指定的 Library 配置项。

    该操作只修改指定字段。配置文件不存在时会自动创建；
    字段已存在时会覆盖原值，其他配置项保持不变。

    配置通过临时文件写入后使用原子替换，避免写入过程中
    导致原配置文件处于不完整状态。

    Args:
        key: 要设置的配置项。
        value: 要保存的配置值。

    Raises:
        TypeError: value 无法被 JSON 序列化时抛出。
        OSError: 配置文件读取或写入失败时抛出。
        json.JSONDecodeError: 已有配置文件不是合法 JSON 时抛出。
    """
    config_path = _get_config_path()
    config = _load_config()

    config[str(key.value)] = value

    temp_path = config_path.with_suffix(".tmp")

    try:
        with temp_path.open("w", encoding="utf-8") as file:
            json.dump(
                config,
                file,
                ensure_ascii=False,
                indent=4,
            )
            file.flush()
            os.fsync(file.fileno())

        os.replace(temp_path, config_path)
    finally:
        if temp_path.exists():
            temp_path.unlink()