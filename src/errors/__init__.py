class TradingSystemError(Exception):
    default_message: str = "System error"

    def __init__(self, message: str | None = None, **context):
        self.message = message or self.default_message
        self.context = context
        super().__init__(self.message)

    def __str__(self) -> str:
        return self.message


class DataError(TradingSystemError):
    default_message = "Data operation error"


class DataIntegrityError(DataError):
    default_message = "Data integrity error"

    def __init__(self, entity: str, ref_id: str, **context):
        super().__init__(
            message=f"Data integrity error: {entity} references non-existent {ref_id}",
            entity=entity,
            ref_id=ref_id,
            **context,
        )


class PersistenceError(DataError):
    default_message = "Data file read/write failed"

    def __init__(self, path: str, op: str, **context):
        super().__init__(
            message=f"File {path} operation failed: {op}",
            path=path,
            op=op,
            **context,
        )


class SerializationError(DataError):
    default_message = "Data serialization failed"

    def __init__(self, entity: str, raw: str, **context):
        super().__init__(
            message=f"{entity} serialization failed: {raw}",
            entity=entity,
            raw=raw,
            **context,
        )


class ValidationError(TradingSystemError):
    default_message = "Validation failed"


class InvalidInputError(ValidationError):
    default_message = "Invalid input"

    def __init__(self, field: str, value: str, **context):
        super().__init__(
            message=f"Invalid input: {field} = {value}",
            field=field,
            value=value,
            **context,
        )


class NotFoundError(ValidationError):
    default_message = "Target not found"


class PlayerNotFoundError(NotFoundError):
    default_message = "Player not found"

    def __init__(self, player_id: str, **context):
        super().__init__(
            message=f"Player not found: {player_id}",
            player_id=player_id,
            **context,
        )


class ItemNotFoundError(NotFoundError):
    default_message = "Item not found"

    def __init__(self, item_id: str, **context):
        super().__init__(
            message=f"Item not found: {item_id}",
            item_id=item_id,
            **context,
        )


class ListingNotFoundError(NotFoundError):
    default_message = "Listing not found"

    def __init__(self, listing_id: str, **context):
        super().__init__(
            message=f"Listing not found: {listing_id}",
            listing_id=listing_id,
            **context,
        )


class BusinessRuleError(ValidationError):
    default_message = "Business rule violation"


class InventoryFullError(BusinessRuleError):
    default_message = "Inventory full"

    def __init__(self, player_id: str, capacity: int, **context):
        super().__init__(
            message=f"Inventory full ({capacity} slots), cannot add more items",
            player_id=player_id,
            capacity=capacity,
            **context,
        )


class InventoryNotEmptyError(BusinessRuleError):
    default_message = "Inventory not empty, cannot delete player"

    def __init__(self, player_id: str, **context):
        super().__init__(
            message=f"Player {player_id} inventory not empty, cannot delete",
            player_id=player_id,
            **context,
        )


class ItemNotEquippableError(BusinessRuleError):
    default_message = "Item not equippable"

    def __init__(self, item_id: str, reason: str, **context):
        super().__init__(
            message=f"Item {item_id} not equippable: {reason}",
            item_id=item_id,
            reason=reason,
            **context,
        )


class ItemBrokenError(BusinessRuleError):
    default_message = "Item broken"

    def __init__(self, item_id: str, **context):
        super().__init__(
            message=f"Item {item_id} is broken",
            item_id=item_id,
            **context,
        )


class LevelOrClassRequirementError(BusinessRuleError):
    default_message = "Level or class requirement not met"

    def __init__(self, item_id: str, level_req: int, class_req: str, **context):
        super().__init__(
            message=f"Item {item_id} requires level {level_req} and class {class_req}",
            item_id=item_id,
            level_req=level_req,
            class_req=class_req,
            **context,
        )


class TradeError(TradingSystemError):
    default_message = "Trade error"


class InsufficientGoldError(TradeError):
    default_message = "Insufficient gold, cannot complete trade"

    def __init__(self, required: int, available: int, **context):
        super().__init__(
            message=f"Insufficient gold: required {required}, available {available}",
            required=required,
            available=available,
            **context,
        )


class SelfPurchaseError(TradeError):
    default_message = "Cannot purchase own listing"

    def __init__(self, player_id: str, **context):
        super().__init__(
            message=f"Player {player_id} cannot purchase own listing",
            player_id=player_id,
            **context,
        )


class ListingNotActiveError(TradeError):
    default_message = "Listing not active"

    def __init__(self, listing_id: str, status: str, **context):
        super().__init__(
            message=f"Listing {listing_id} not active, status: {status}",
            listing_id=listing_id,
            status=status,
            **context,
        )


class DuplicateListingError(TradeError):
    default_message = "Item already listed"

    def __init__(self, item_id: str, **context):
        super().__init__(
            message=f"Item {item_id} is already listed",
            item_id=item_id,
            **context,
        )


