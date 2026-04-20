"""src/errors 基础单元测试。

覆盖 docs/error-and-log-design.md §8 的"每个异常能被实例化、消息正确、context 正确"的最小要求。
"""

from __future__ import annotations

import pytest

from src.errors import (
    BusinessRuleError,
    DataError,
    DataIntegrityError,
    DuplicateListingError,
    InsufficientGoldError,
    InvalidInputError,
    InventoryFullError,
    InventoryNotEmptyError,
    ItemBrokenError,
    ItemNotEquippableError,
    ItemNotFoundError,
    LevelOrClassRequirementError,
    ListingNotActiveError,
    ListingNotFoundError,
    NotFoundError,
    PersistenceError,
    PlayerNotFoundError,
    SelfPurchaseError,
    SerializationError,
    TradeError,
    TradingSystemError,
    ValidationError,
)


# ---------------------------------------------------------------------------
# 1. 异常树结构
# ---------------------------------------------------------------------------

class TestExceptionHierarchy:
    """验证三层异常树的继承关系，保证 `except` 语句能正确捕获。"""

    @pytest.mark.parametrize("cls", [DataError, ValidationError, TradeError])
    def test_midtier_inherits_root(self, cls):
        assert issubclass(cls, TradingSystemError)

    @pytest.mark.parametrize(
        "cls",
        [DataIntegrityError, PersistenceError, SerializationError],
    )
    def test_data_subclasses(self, cls):
        assert issubclass(cls, DataError)

    @pytest.mark.parametrize(
        "cls",
        [InvalidInputError, NotFoundError, BusinessRuleError],
    )
    def test_validation_subclasses(self, cls):
        assert issubclass(cls, ValidationError)

    @pytest.mark.parametrize(
        "cls",
        [PlayerNotFoundError, ItemNotFoundError, ListingNotFoundError],
    )
    def test_notfound_subclasses(self, cls):
        assert issubclass(cls, NotFoundError)

    @pytest.mark.parametrize(
        "cls",
        [
            InventoryFullError,
            InventoryNotEmptyError,
            ItemNotEquippableError,
            ItemBrokenError,
            LevelOrClassRequirementError,
        ],
    )
    def test_business_rule_subclasses(self, cls):
        assert issubclass(cls, BusinessRuleError)

    @pytest.mark.parametrize(
        "cls",
        [
            InsufficientGoldError,
            SelfPurchaseError,
            ListingNotActiveError,
            DuplicateListingError,
        ],
    )
    def test_trade_subclasses(self, cls):
        assert issubclass(cls, TradeError)


# ---------------------------------------------------------------------------
# 2. 基类行为
# ---------------------------------------------------------------------------

class TestBaseClass:
    def test_default_message_used_when_omitted(self):
        err = TradingSystemError()
        assert err.message == TradingSystemError.default_message
        assert str(err) == err.message

    def test_explicit_message_overrides_default(self):
        err = TradingSystemError("自定义消息")
        assert err.message == "自定义消息"

    def test_context_stored_as_dict(self):
        err = TradingSystemError(foo=1, bar="x")
        assert err.context == {"foo": 1, "bar": "x"}


# ---------------------------------------------------------------------------
# 3. 关键子类的字段与消息（按 §8 测试模板）
# ---------------------------------------------------------------------------

class TestConcreteExceptions:
    def test_insufficient_gold(self):
        err = InsufficientGoldError(required=1000, available=500)
        assert err.context["required"] == 1000
        assert err.context["available"] == 500
        assert "1000" in err.message and "500" in err.message

    def test_player_not_found(self):
        err = PlayerNotFoundError(player_id="p_001")
        assert err.context["player_id"] == "p_001"
        assert "p_001" in err.message

    def test_item_not_found(self):
        err = ItemNotFoundError(item_id="i_042")
        assert err.context["item_id"] == "i_042"

    def test_listing_not_found(self):
        err = ListingNotFoundError(listing_id="l_009")
        assert err.context["listing_id"] == "l_009"

    def test_listing_not_active(self):
        err = ListingNotActiveError(listing_id="l_007", status="sold")
        assert err.context == {"listing_id": "l_007", "status": "sold"}
        assert "sold" in err.message

    def test_self_purchase(self):
        err = SelfPurchaseError(player_id="p_003")
        assert err.context["player_id"] == "p_003"

    def test_duplicate_listing(self):
        err = DuplicateListingError(item_id="i_011")
        assert err.context["item_id"] == "i_011"

    def test_inventory_full(self):
        err = InventoryFullError(player_id="p_002", capacity=50)
        assert err.context == {"player_id": "p_002", "capacity": 50}
        assert "50" in err.message

    def test_inventory_not_empty(self):
        err = InventoryNotEmptyError(player_id="p_002")
        assert err.context["player_id"] == "p_002"

    def test_item_not_equippable(self):
        err = ItemNotEquippableError(item_id="i_001", reason="耐久=0")
        assert err.context == {"item_id": "i_001", "reason": "耐久=0"}

    def test_item_broken(self):
        err = ItemBrokenError(item_id="i_001")
        assert err.context["item_id"] == "i_001"

    def test_level_or_class_requirement(self):
        err = LevelOrClassRequirementError(
            item_id="i_001", level_req=10, class_req=["warrior", "archer"]
        )
        assert err.context["level_req"] == 10
        assert err.context["class_req"] == ["warrior", "archer"]

    def test_invalid_input(self):
        err = InvalidInputError(field="gold", value=-1)
        assert err.context == {"field": "gold", "value": -1}

    def test_data_integrity(self):
        err = DataIntegrityError(entity="inventory", ref_id="i_999")
        assert err.context == {"entity": "inventory", "ref_id": "i_999"}

    def test_persistence(self):
        err = PersistenceError(path="data/players.json", op="save")
        assert err.context == {"path": "data/players.json", "op": "save"}

    def test_serialization(self):
        err = SerializationError(entity="Item", raw={"x": 1})
        assert err.context["entity"] == "Item"
        assert err.context["raw"] == {"x": 1}


# ---------------------------------------------------------------------------
# 4. 捕获契约：上层 except 能拦截下层
# ---------------------------------------------------------------------------

class TestCatchSemantics:
    """验证服务层抛具体异常 → UI 层用基类捕获的常见模式。"""

    def test_catch_via_root_base(self):
        with pytest.raises(TradingSystemError):
            raise InsufficientGoldError(required=1, available=0)

    def test_catch_via_midtier(self):
        with pytest.raises(TradeError):
            raise SelfPurchaseError(player_id="p_001")

    def test_notfound_catches_specific(self):
        with pytest.raises(NotFoundError):
            raise ItemNotFoundError(item_id="i_999")

    def test_business_rule_catches_specific(self):
        with pytest.raises(BusinessRuleError):
            raise InventoryFullError(player_id="p_001", capacity=50)
