from typing import Any, Iterator, Optional

__all__ = ["HashMap", "hash_map"]




class HashMap:
    """
    自实现哈希表（单独链地址法）

    提供类似 Python dict 的 mapping 接口，用于 Repository 的 ID 索引。
    """

    def __init__(self, capacity: int = 16):
        if capacity <= 0:
            raise ValueError("capacity must be positive")
        self._capacity = capacity
        self._size = 0
        self._buckets: list[list[tuple[Any, Any]]] = [[] for _ in range(capacity)]


    def _hash(self, key: Any) -> int:
        return hash(key) % self._capacity


    def _resize(self, new_capacity: int) -> None:
        old_buckets = self._buckets
        self._capacity = new_capacity
        self._size = 0
        self._buckets = [[] for _ in range(self._capacity)]
        for bucket in old_buckets:
            for k, v in bucket:
                self.put(k, v)


    def put(self, key: Any, value: Any) -> None:
        """插入或更新键值对"""
        index = self._hash(key)
        bucket = self._buckets[index]
        for i, (stored_key, _) in enumerate(bucket):
            if key == stored_key:
                bucket[i] = (key, value)
                return

        bucket.append((key, value))
        self._size += 1

        if self._size > self._capacity * 0.75:
            self._resize(self._capacity * 2)


    def get(self, key: Any, default: Any = None) -> Any:
        """获取键对应的值，不存在返回 default"""
        index = self._hash(key)
        bucket = self._buckets[index]
        for stored_key, value in bucket:
            if key == stored_key:
                return value
        return default


    def remove(self, key: Any) -> bool:
        """删除键值对，成功返回 True，键不存在返回 False"""
        index = self._hash(key)
        bucket = self._buckets[index]
        for i, (stored_key, _) in enumerate(bucket):
            if key == stored_key:
                del bucket[i]
                self._size -= 1
                return True
        return False


    def pop(self, key: Any, default: Any = None) -> Any:
        """删除并返回键对应的值，不存在返回 default"""
        index = self._hash(key)
        bucket = self._buckets[index]
        for i, (stored_key, value) in enumerate(bucket):
            if key == stored_key:
                del bucket[i]
                self._size -= 1
                return value
        return default


    def clear(self) -> None:
        """清空所有键值对"""
        self._buckets = [[] for _ in range(self._capacity)]
        self._size = 0


    def keys(self) -> list[Any]:
        """返回所有键的列表"""
        result = []
        for bucket in self._buckets:
            for k, _ in bucket:
                result.append(k)
        return result


    def values(self) -> list[Any]:
        """返回所有值的列表"""
        result = []
        for bucket in self._buckets:
            for _, v in bucket:
                result.append(v)
        return result


    def items(self) -> list[tuple[Any, Any]]:
        """返回所有键值对的列表"""
        result = []
        for bucket in self._buckets:
            for k, v in bucket:
                result.append((k, v))
        return result


    def to_dict(self) -> dict[Any, Any]:
        """转换为原生 dict（用于测试和兼容场景）"""
        return dict(self.items())


    def __setitem__(self, key: Any, value: Any) -> None:
        self.put(key, value)


    def __getitem__(self, key: Any) -> Any:
        value = self.get(key, None)
        if value is None and key not in self:
            raise KeyError(key)
        return value


    def __delitem__(self, key: Any) -> None:
        if not self.remove(key):
            raise KeyError(key)


    def __contains__(self, key: Any) -> bool:
        return self.get(key, None) is not None or any(
            k == key for bucket in self._buckets for k, _ in bucket
        )


    def __len__(self) -> int:
        return self._size


    def __iter__(self) -> Iterator[Any]:
        """迭代所有键"""
        for bucket in self._buckets:
            for k, _ in bucket:
                yield k


    def __repr__(self) -> str:
        items_str = ", ".join(f"{k!r}: {v!r}" for k, v in self.items())
        return f"HashMap({{{items_str}}})"




# 兼容旧代码的别名和方法
class hash_map(HashMap):
    """旧版兼容类，保留原 API"""

    def get_username(self, item_id: Any) -> Optional[Any]:
        """兼容旧 API：get_username(item_id)"""
        return self.get(item_id)

