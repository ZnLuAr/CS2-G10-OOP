from src.structures.hash_map import hash_map


def test_put_and_get_username():
    mapping = hash_map()

    mapping.put("p_001", "alice")

    assert mapping.get_username("p_001") == "alice"


def test_put_updates_existing_value():
    mapping = hash_map()

    mapping.put("p_001", "alice")
    mapping.put("p_001", "alice_new")

    assert mapping.get_username("p_001") == "alice_new"


def test_remove_deletes_existing_key():
    mapping = hash_map()

    mapping.put("p_001", "alice")

    assert mapping.remove("p_001") is True
    assert mapping.get_username("p_001") is None


def test_remove_missing_key_returns_false():
    mapping = hash_map()

    assert mapping.remove("missing") is False
