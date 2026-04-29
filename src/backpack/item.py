class Item:
    RARITY_ORDER = ["common", "uncommon", "rare", "epic", "legendary"]

    def __init__(self, item_id: str, name: str, rarity: str, category: str,
                 stackable: bool = None, stack_size_max: int = 1):
        self.item_id = item_id
        self.name = name
        self.rarity = rarity
        self.category = category
        self.stackable = stackable if stackable is not None else (
            category in ["consumable", "misc"] or category.startswith("consumable.")
        )
        self.stack_size_max = stack_size_max if self.stackable else 1