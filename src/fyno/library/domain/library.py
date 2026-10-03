from dataclasses import dataclass, field

from .collection import Collection
from .file import LibraryFile


@dataclass
class Library:
    """Fyno Library 的领域根对象。

    Library 负责维护当前 Workspace 下的 Collection 集合及其顺序，并提供
    Collection 和 File 的领域级查询能力。文件系统操作、ID 生成以及 .fyno
    持久化由更高层负责。
    """

    collections: list[Collection] = field(default_factory=list)

    _collection_map: dict[str, Collection] = field(
        init=False,
        repr=False,
        compare=False,
    )

    def __post_init__(self) -> None:
        """根据 Collection 列表初始化 Collection ID 索引。

        如果 collections 中存在重复的 Collection ID，则保留第一次出现的
        Collection。
        """
        self._collection_map = {}

        for collection in self.collections:
            if collection.collection_id not in self._collection_map:
                self._collection_map[collection.collection_id] = collection

    def find_collection(self, collection_id: str) -> Collection | None:
        """根据 Collection ID 查找 Collection。

        Args:
            collection_id: 要查找的 Collection ID。

        Returns:
            找到时返回对应的 Collection，否则返回 None。
        """
        return self._collection_map.get(collection_id)

    def add_collection(self, collection: Collection) -> bool:
        """向 Library 末尾添加 Collection。

        Args:
            collection: 要添加的 Collection。

        Returns:
            添加成功时返回 True；Collection ID 已存在时返回 False。
        """
        if collection.collection_id in self._collection_map:
            return False

        self.collections.append(collection)
        self._collection_map[collection.collection_id] = collection
        return True

    def remove_collection(self, collection_id: str) -> bool:
        """从 Library 中移除 Collection。

        Args:
            collection_id: 要移除的 Collection ID。

        Returns:
            移除成功时返回 True；Collection 不存在时返回 False。
        """
        collection = self.find_collection(collection_id)

        if collection is None:
            return False

        self.collections.remove(collection)
        del self._collection_map[collection_id]
        return True

    def move_collection(
        self,
        collection_id: str,
        after_collection_id: str | None,
    ) -> bool:
        """调整 Collection 在 Library 中的顺序。

        当 after_collection_id 为 None 时，将 Collection 移动到第一位；
        否则将 Collection 移动到指定 Collection 之后。

        Args:
            collection_id: 要移动的 Collection ID。
            after_collection_id: 目标 Collection ID。None 表示移动到第一位。

        Returns:
            顺序实际发生变化时返回 True；
            Collection 不存在、目标 Collection 不存在、目标为自身或位置未变化
            时返回 False。
        """
        collection = self.find_collection(collection_id)

        if collection is None:
            return False

        if after_collection_id == collection_id:
            return False

        current_index = self.collections.index(collection)

        if after_collection_id is None:
            if current_index == 0:
                return False

            self.collections.pop(current_index)
            self.collections.insert(0, collection)
            return True

        target = self.find_collection(after_collection_id)

        if target is None:
            return False

        target_index = self.collections.index(target)

        if current_index == target_index + 1:
            return False

        self.collections.pop(current_index)

        # 移除当前 Collection 后目标索引可能变化，因此重新计算位置。
        target_index = self.collections.index(target)
        self.collections.insert(target_index + 1, collection)

        return True

    def find_file(
        self,
        file_id: str,
    ) -> tuple[Collection, LibraryFile] | None:
        """根据全局 File ID 查找文件及其所属 Collection。

        Args:
            file_id: 要查找的 File ID。

        Returns:
            找到时返回 (Collection, LibraryFile)，否则返回 None。
        """
        for collection in self.collections:
            file = collection.find_file(file_id)

            if file is not None:
                return collection, file

        return None

    def replace_collections(
            self,
            collections: list[Collection],
    ) -> None:
        """整体替换 Library 中的 Collection。

        该操作会同时重建 Collection ID 索引，保证 collections 与
        _collection_map 始终保持一致。

        Args:
            collections: 新的 Collection 列表。
        """
        self.collections = list(collections)
        self._collection_map = {
            collection.collection_id: collection
            for collection in self.collections
        }