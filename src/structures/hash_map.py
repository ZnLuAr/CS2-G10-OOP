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

    def put(self, username:Any, id:Any) -> None:
        index = self._hash(username)
        user_data = self._buckets[index]
        for k, (u, _) in enumerate(user_data):
            if username == u:
                user_data = (username, id) #update
                return

        user_data.append((username, id))
        self._size += 1

        if self._size > self._capacity * 0.75:
            self._resize(self._capacity * 2)


    def get(self, username: Any) -> Optional[Any]:
        index = self._hash(username)
        user_data = self._buckets[index]
        for u, i in user_data:
            if u == username:
                return i
        return None

    def remove(self, username: Any) -> bool:
        index = self._hash(username)
        user_data = self._buckets[index]
        for k, (u, _) in enumerate(user_data):
            if u == username:
                del user_data[k]
                self._size -= 1
                return True
        return False

