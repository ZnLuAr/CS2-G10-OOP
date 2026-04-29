class InventoryFullError(Exception):
    def __init__(self):
        super().__init__("Backpack is full")