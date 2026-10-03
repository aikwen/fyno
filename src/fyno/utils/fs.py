from pathlib import Path

from platformdirs import user_data_dir


def get_app_data_dir() -> Path:
    r"""Returns the Fyno application data directory.

    The directory follows the platform-specific user data convention and is
    created automatically if it does not already exist.

    Windows: ``C:\Users\<user>\AppData\Local\Fyno``

    macOS: ``~/Library/Application Support/Fyno``

    Linux: ``~/.local/share/Fyno``

    Returns:
        The absolute path to the Fyno application data directory.
    """
    app_data_dir = Path(user_data_dir("Fyno", appauthor=False))
    app_data_dir.mkdir(parents=True, exist_ok=True)
    return app_data_dir


def list_directories(
    path: Path,
    prefix: str | None = None,
    limit: int = 20,
) -> list[Path]:
    """获取指定目录下匹配的一级子目录。

    只扫描当前目录的直接子目录，不递归。结果按目录名称排序，并可通过
    prefix 进行大小写无关的前缀匹配。遇到无权限或其他文件系统错误时，
    返回空列表。

    Args:
        path: 要扫描的目录。
        prefix: 可选的目录名称前缀。为 None 或空字符串时不过滤。
        limit: 最多返回的目录数量。

    Returns:
        匹配的一级子目录路径列表。
    """
    if limit <= 0:
        return []

    if not path.is_dir():
        return []

    normalized_prefix = (prefix or "").casefold()

    try:
        directories = sorted(
            (
                entry
                for entry in path.iterdir()
                if entry.is_dir()
            ),
            key=lambda entry: entry.name.casefold(),
        )

        results: list[Path] = []

        for directory in directories:
            if (
                normalized_prefix
                and not directory.name.casefold().startswith(
                    normalized_prefix
                )
            ):
                continue

            results.append(directory)

            if len(results) >= limit:
                break

        return results

    except (PermissionError, OSError):
        return []