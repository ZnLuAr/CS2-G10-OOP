from __future__ import annotations

import pytest

from src.errors import InvalidInputError, ItemNotFoundError
from src.services.item_service import ItemService
from src.services.persistence import Persistence


@pytest.fixture
def service(tmp_path):
    persistence = Persistence(data_dir=str(tmp_path / "data"))
    persistence.seed_if_empty()
    repo = persistence.load_all()
    return ItemService(repo, persistence)


def test_get_by_id(service):
    iid = next(iter(service.repo.items))
    assert service.get_by_id(iid)["item_id"] == iid


def test_get_by_id_missing_raises(service):
    with pytest.raises(ItemNotFoundError):
        service.get_by_id("i_999999")


def test_list_all(service):
    items = service.list_all()
    assert len(items) == len(service.repo.items)


def test_list_all_by_category_prefix(service):
    items = service.list_all("weapon")
    assert all(item.get("category", "").startswith("weapon") for item in items)


def test_browse_catalog_root(service):
    root = service.browse_catalog("root")
    assert root.get("key") == "root"


def test_browse_catalog_missing_raises(service):
    with pytest.raises(InvalidInputError):
        service.browse_catalog("nope")


def test_items_in_category(service):
    items = service.items_in_category("weapon")
    assert all(item.get("category", "").startswith("weapon") for item in items)


def test_create_item_not_implemented(service):
    with pytest.raises(NotImplementedError):
        service.create_item({})
