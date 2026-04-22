from typing import Any, List, Optional, Tuple

__all__ = ["hash_map"]

class hash_map():
    def __init__(self, capacity: int = 16):
        self._capacity = capacity
        self._size = 0
        self._buckets = [[] for _ in range(capacity)]  #store keywords, id

    def _hash(self, key: Any) -> int:
        return hash(key) % self._capacity

    def _resize(self, new_capacity:int) ->None:
        old_buckets = self._buckets
        self._capacity = new_capacity
        self._size = 0
        self._buckets = [[] for _ in range(self._capacity)]
        for bucket in old_buckets:
            for u, i in bucket:
                self.put(u, i)

    def put(self, id:Any, username:Any) -> None:
        index = self._hash(id)
        user_data = self._buckets[index]
        for k, (i, _) in enumerate(user_data):
            if id == i:
                user_data[k] = (id, username) #update
                return

        user_data.append((id, username))
        self._size += 1

        if self._size > self._capacity * 0.75:
            self._resize(self._capacity * 2)


    def get_username(self, id: Any) -> Optional[Any]:
        index = self._hash(id)
        user_data = self._buckets[index]
        for i, u in user_data:
            if i == id:
                return u
        return None


    def remove(self, id: Any) -> bool:
        index = self._hash(id)
        user_data = self._buckets[index]
        for k, (i, _) in enumerate(user_data):
            if id == i:
                del user_data[k]
                self._size -= 1
                return True
        return False

