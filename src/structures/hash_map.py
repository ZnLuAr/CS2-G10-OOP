from typing import Any, Optional

__all__ = ["hash_map"]


class hash_map:
    def __init__(self, capacity: int = 16):
        self._capacity = capacity
        self._size = 0
        self._buckets = [[] for _ in range(capacity)]

    def _hash(self, key: Any) -> int:
        return hash(key) % self._capacity

    def _resize(self, new_capacity: int) -> None:
        old_buckets = self._buckets
        self._capacity = new_capacity
        self._size = 0
        self._buckets = [[] for _ in range(self._capacity)]
        for bucket in old_buckets:
            for item_id, username in bucket:
                self.put(item_id, username)

    def put(self, item_id: Any, username: Any) -> None:
        index = self._hash(item_id)
        user_data = self._buckets[index]
        for k, (stored_id, _) in enumerate(user_data):
            if item_id == stored_id:
                user_data[k] = (item_id, username)
                return

        user_data.append((item_id, username))
        self._size += 1

        if self._size > self._capacity * 0.75:
            self._resize(self._capacity * 2)

    def get_username(self, item_id: Any) -> Optional[Any]:
        index = self._hash(item_id)
        user_data = self._buckets[index]
        for stored_id, username in user_data:
            if stored_id == item_id:
                return username
        return None

    def remove(self, item_id: Any) -> bool:
        index = self._hash(item_id)
        user_data = self._buckets[index]
        for k, (stored_id, _) in enumerate(user_data):
            if item_id == stored_id:
                del user_data[k]
                self._size -= 1
                return True
        return False

