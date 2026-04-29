class Node:
    def __init__(self, data):
        self.data = data
        self.prev = None
        self.next = None

class DoublyLinkedList:
    def __init__(self):
        self.head = None
        self.tail = None
        self.size = 0

    def add_tail(self, data):
        node = Node(data)
        if not self.tail:
            self.head = node
            self.tail = node
        else:
            self.tail.next = node
            node.prev = self.tail
            self.tail = node
        self.size += 1

    def remove_node(self, node):
        if node is None:
            raise ValueError("Cannot remove None node")
        if node.prev:
            node.prev.next = node.next
        else:
            self.head = node.next

        if node.next:
            node.next.prev = node.prev
        else:
            self.tail = node.prev

        self.size -= 1

    def to_list(self):
        res = []
        cur = self.head
        while cur:
            res.append(cur.data)
            cur = cur.next
        return res

    def clear(self):
        self.head = None
        self.tail = None
        self.size = 0

    def is_empty(self):
         """判断链表是否为空"""
         return self.size == 0

    def __iter__(self):
            """支持迭代，方便遍历背包"""
            cur = self.head
            while cur:
                yield cur.data
                cur = cur.next

    def __len__(self):
            """支持 len() 调用"""
            return self.size

    def find(self, predicate):
            """按条件查找节点，返回第一个匹配的 Node 或 None"""
            cur = self.head
            while cur:
                if predicate(cur.data):
                    return cur
                cur = cur.next
            return None