from dataclasses import dataclass


@dataclass
class LibraryFile:
    """Fyno Library 中的文件领域对象。

    LibraryFile 只描述文件自身的领域状态。文件归属、排序、删除等操作由
    Collection 或更高层负责；磁盘读写与 .fyno 持久化也不属于该对象职责。
    """

    file_id: str
    name: str

    def rename(self, name: str) -> bool:
        """修改文件的显示名称。

        Args:
            name: 新的文件显示名称。

        Returns:
            名称实际发生修改时返回 True；名称为空或未发生变化时返回 False。
        """
        name = name.strip()

        if not name or name == self.name:
            return False

        self.name = name
        return True