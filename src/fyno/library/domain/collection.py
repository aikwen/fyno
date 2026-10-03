from dataclasses import dataclass, field

from .file import LibraryFile


@dataclass
class Collection:
    """Fyno Library 中的 Collection 领域对象。

    Collection 负责维护自身显示名称、所包含的文件以及文件顺序。
    文件系统操作、ID 生成和 .fyno 持久化由更高层负责。
    """

    collection_id: str
    name: str
    files: list[LibraryFile] = field(default_factory=list)

    _file_map: dict[str, LibraryFile] = field(
        init=False,
        repr=False,
        compare=False,
    )

    def __post_init__(self) -> None:
        """根据文件列表初始化 File ID 索引。

        如果 files 中存在重复的 File ID，则保留第一次出现的文件。
        """
        self._file_map = {}

        for file in self.files:
            if file.file_id not in self._file_map:
                self._file_map[file.file_id] = file

    def rename(self, name: str) -> bool:
        """修改 Collection 的显示名称。

        Args:
            name: 新的 Collection 显示名称。

        Returns:
            名称实际发生修改时返回 True；名称为空或未发生变化时返回 False。
        """
        name = name.strip()

        if not name or name == self.name:
            return False

        self.name = name
        return True

    def find_file(self, file_id: str) -> LibraryFile | None:
        """根据 File ID 查找文件。

        Args:
            file_id: 要查找的 File ID。

        Returns:
            找到时返回对应的 LibraryFile，否则返回 None。
        """
        return self._file_map.get(file_id)

    def add_file(self, file: LibraryFile) -> bool:
        """向 Collection 末尾添加文件。

        Args:
            file: 要添加的 LibraryFile。

        Returns:
            添加成功时返回 True；File ID 已存在时返回 False。
        """
        if file.file_id in self._file_map:
            return False

        self.files.append(file)
        self._file_map[file.file_id] = file
        return True

    def remove_file(self, file_id: str) -> bool:
        """从 Collection 中移除文件。

        Args:
            file_id: 要移除的 File ID。

        Returns:
            移除成功时返回 True；文件不存在时返回 False。
        """
        file = self.find_file(file_id)

        if file is None:
            return False

        self.files.remove(file)
        del self._file_map[file_id]
        return True

    def move_file(
        self,
        file_id: str,
        after_file_id: str | None,
    ) -> bool:
        """调整文件在 Collection 中的顺序。

        当 after_file_id 为 None 时，将文件移动到第一位；
        否则将文件移动到指定文件之后。

        Args:
            file_id: 要移动的 File ID。
            after_file_id: 目标 File ID。None 表示移动到第一位。

        Returns:
            顺序实际发生变化时返回 True；
            File 不存在、目标 File 不存在、目标为自身或位置未变化时返回 False。
        """
        file = self.find_file(file_id)

        if file is None:
            return False

        if after_file_id == file_id:
            return False

        current_index = self.files.index(file)

        if after_file_id is None:
            if current_index == 0:
                return False

            self.files.pop(current_index)
            self.files.insert(0, file)
            return True

        target = self.find_file(after_file_id)

        if target is None:
            return False

        target_index = self.files.index(target)

        # 当前已经紧跟在目标 File 后面，不需要再次调整。
        if current_index == target_index + 1:
            return False

        self.files.pop(current_index)

        # 移除当前 File 后，目标索引可能发生变化，因此重新获取位置。
        target_index = self.files.index(target)
        self.files.insert(target_index + 1, file)

        return True

    def replace_files(
            self,
            files: list[LibraryFile],
    ) -> None:
        """整体替换 Collection 中的 File。

        该操作会同时重建 File ID 索引，保证 files 与 _file_map 始终一致。

        Args:
            files: 新的 File 列表。
        """
        self.files = list(files)
        self._file_map = {
            file.file_id: file
            for file in self.files
        }