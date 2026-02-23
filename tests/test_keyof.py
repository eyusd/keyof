from dataclasses import dataclass
from typing import Any, NamedTuple

import pytest
from pydantic import BaseModel

from keyof import KeyOf, nn

# ---------------------------------------------------------------------------
# Data Structures
# ---------------------------------------------------------------------------


@dataclass
class Address:
    city: str
    zipcode: int


@dataclass
class User:
    id: int
    name: str
    tags: list[str]
    metadata: dict[str, Any]
    address: Address | None = None


class PydanticItem(BaseModel):
    name: str
    value: float
    tags: list[str]


class Coordinate(NamedTuple):
    x: int
    y: int


# ---------------------------------------------------------------------------
# Test Data
# ---------------------------------------------------------------------------


@pytest.fixture
def user_data():
    return User(
        id=1,
        name="Alice",
        address=Address(city="Wonderland", zipcode=12345),
        tags=["admin", "user"],
        metadata={"role": "superuser", "login_count": 42, "prefs": {"theme": "dark"}},
    )


@pytest.fixture
def complex_dict():
    return {
        "users": [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}],
        "meta": {"version": "1.0", "flags": {"active": True, "debug": False}},
        "weird_keys": {
            "spaced key": "value",
            "dotted.key": "value",
            "slash/key": "value",
            "bracket[key]": "value",
        },
    }


# ---------------------------------------------------------------------------
# Access Tests (Attributes, Dicts, Lists, etc.)
# ---------------------------------------------------------------------------


def test_user_access_name(user_data):
    path: KeyOf[User, str] = KeyOf(lambda u: u.name)
    assert path.from_(user_data) == "Alice"


def test_user_access_id(user_data):
    path: KeyOf[User, int] = KeyOf(lambda u: u.id)
    assert path.from_(user_data) == 1


def test_user_access_nested_city(user_data):
    path: KeyOf[User, str] = KeyOf(lambda u: nn(u.address).city)
    assert path.from_(user_data) == "Wonderland"


def test_user_access_nested_zipcode(user_data):
    path: KeyOf[User, int] = KeyOf(lambda u: nn(u.address).zipcode)
    assert path.from_(user_data) == 12345


def test_user_access_list_index_0(user_data):
    path: KeyOf[User, str] = KeyOf(lambda u: u.tags[0])
    assert path.from_(user_data) == "admin"


def test_user_access_list_index_1(user_data):
    path: KeyOf[User, str] = KeyOf(lambda u: u.tags[1])
    assert path.from_(user_data) == "user"


def test_user_access_dict_key_role(user_data):
    path: KeyOf[User, Any] = KeyOf(lambda u: u.metadata["role"])
    assert path.from_(user_data) == "superuser"


def test_user_access_nested_dict_key(user_data):
    path: KeyOf[User, Any] = KeyOf(lambda u: u.metadata["prefs"]["theme"])
    assert path.from_(user_data) == "dark"


def test_pydantic_access_name():
    item = PydanticItem(name="Widget", value=19.99, tags=["sale"])
    path: KeyOf[PydanticItem, str] = KeyOf(lambda i: i.name)
    assert path.from_(item) == "Widget"


def test_pydantic_access_value():
    item = PydanticItem(name="Widget", value=19.99, tags=["sale"])
    path: KeyOf[PydanticItem, float] = KeyOf(lambda i: i.value)
    assert path.from_(item) == 19.99


def test_pydantic_access_tags():
    item = PydanticItem(name="Widget", value=19.99, tags=["sale"])
    path: KeyOf[PydanticItem, str] = KeyOf(lambda i: i.tags[0])
    assert path.from_(item) == "sale"


def test_namedtuple_access_x():
    c = Coordinate(x=10, y=20)
    path: KeyOf[Coordinate, int] = KeyOf(lambda p: p.x)
    assert path.from_(c) == 10


def test_namedtuple_access_y():
    c = Coordinate(x=10, y=20)
    path: KeyOf[Coordinate, int] = KeyOf(lambda p: p.y)
    assert path.from_(c) == 20


def test_namedtuple_index_access():
    c = Coordinate(x=10, y=20)
    path: KeyOf[Coordinate, int] = KeyOf(lambda p: p[0])  # type: ignore[index]
    assert path.from_(c) == 10


def test_tuple_access():
    t = (1, 2, "three")
    path: KeyOf[tuple[int, int, str], str] = KeyOf(lambda x: x[2])  # type: ignore[index]
    assert path.from_(t) == "three"


def test_primitive_str_index_access():
    s = "hello"
    path: KeyOf[str, str] = KeyOf(lambda x: x[0])  # type: ignore[index]
    assert path.from_(s) == "h"


def test_complex_dict_nested_list(complex_dict):
    path: KeyOf[dict, Any] = KeyOf(lambda x: x["users"][0]["name"])
    assert path.from_(complex_dict) == "Alice"


def test_complex_dict_nested_bool(complex_dict):
    path: KeyOf[dict, Any] = KeyOf(lambda x: x["meta"]["flags"]["active"])
    assert path.from_(complex_dict) is True


def test_complex_dict_weird_spaced_key(complex_dict):
    path: KeyOf[dict, Any] = KeyOf(lambda x: x["weird_keys"]["spaced key"])
    assert path.from_(complex_dict) == "value"


def test_complex_dict_weird_bracket_key(complex_dict):
    path: KeyOf[dict, Any] = KeyOf(lambda x: x["weird_keys"]["bracket[key]"])
    assert path.from_(complex_dict) == "value"


# ---------------------------------------------------------------------------
# Default Value Tests
# ---------------------------------------------------------------------------


def test_default_values_none_path(user_data):
    user_data.address = None
    path: KeyOf[User, str] = KeyOf(lambda u: nn(u.address).city)

    with pytest.raises(AttributeError):
        path.from_(user_data)

    assert path.from_(user_data, default="N/A") == "N/A"
    assert path.from_(user_data, default=None) is None


def test_default_values_missing_list_index(complex_dict):
    path: KeyOf[dict, Any] = KeyOf(lambda d: d["users"][99])

    with pytest.raises(AttributeError):
        path.from_(complex_dict)

    assert path.from_(complex_dict, default="DefaultUser") == "DefaultUser"


def test_default_values_missing_dict_key(complex_dict):
    path: KeyOf[dict, Any] = KeyOf(lambda d: d["meta"]["missing"])

    with pytest.raises(AttributeError):
        path.from_(complex_dict)

    assert path.from_(complex_dict, default="FoundIt") == "FoundIt"


# ---------------------------------------------------------------------------
# Path Introspection Tests
# ---------------------------------------------------------------------------


def test_path_parts():
    path: KeyOf[User, Any] = KeyOf(lambda u: u.metadata["prefs"]["theme"])
    assert path.parts == ("metadata", "prefs", "theme")


def test_path_depth():
    path: KeyOf[User, Any] = KeyOf(lambda u: u.metadata["prefs"]["theme"])
    assert path.depth == 3


def test_path_root():
    path: KeyOf[User, Any] = KeyOf(lambda u: u.metadata["prefs"]["theme"])
    assert path.root == "metadata"


def test_path_leaf():
    path: KeyOf[User, Any] = KeyOf(lambda u: u.metadata["prefs"]["theme"])
    assert path.leaf == "theme"


def test_path_iteration():
    path: KeyOf[User, Any] = KeyOf(lambda u: u.metadata["prefs"]["theme"])
    assert list(path) == ["metadata", "prefs", "theme"]


def test_path_contains():
    path: KeyOf[User, Any] = KeyOf(lambda u: u.metadata["prefs"]["theme"])
    assert "prefs" in path
    assert "metadata" in path
    assert "theme" in path
    assert "other" not in path


def test_path_len():
    path: KeyOf[User, Any] = KeyOf(lambda u: u.metadata["prefs"]["theme"])
    assert len(path) == 3


def test_parent_path():
    path: KeyOf[User, Any] = KeyOf(lambda u: u.metadata["prefs"]["theme"])
    parent = path.parent()
    assert str(parent) == "metadata.prefs"
    assert parent.parts == ("metadata", "prefs")


def test_grandparent_path():
    path: KeyOf[User, Any] = KeyOf(lambda u: u.metadata["prefs"]["theme"])
    grandparent = path.parent().parent()
    assert str(grandparent) == "metadata"


def test_parent_error_at_root():
    path: KeyOf[User, Any] = KeyOf(lambda u: u.metadata)
    with pytest.raises(ValueError):
        path.parent()


# ---------------------------------------------------------------------------
# Serialization Tests
# ---------------------------------------------------------------------------


def test_to_dot(complex_dict):
    path: KeyOf[dict, Any] = KeyOf(lambda d: d["users"][0]["name"])
    assert path.to_dot() == "users.0.name"


def test_to_posix(complex_dict):
    path: KeyOf[dict, Any] = KeyOf(lambda d: d["users"][0]["name"])
    assert path.to_posix() == "users/0/name"


def test_to_python(complex_dict):
    path: KeyOf[dict, Any] = KeyOf(lambda d: d["users"][0]["name"])
    assert path.to_python() == "users.0.name"


def test_to_bracket(complex_dict):
    path: KeyOf[dict, Any] = KeyOf(lambda d: d["users"][0]["name"])
    assert path.to_bracket() == "['users']['0']['name']"


def test_to_jmespath(complex_dict):
    path: KeyOf[dict, Any] = KeyOf(lambda d: d["users"][0]["name"])
    assert path.to_jmespath() == "users.0.name"


def test_to_jsonpath(complex_dict):
    path: KeyOf[dict, Any] = KeyOf(lambda d: d["users"][0]["name"])
    assert path.to_jsonpath() == "$.users.0.name"


def test_to_xpath(complex_dict):
    path: KeyOf[dict, Any] = KeyOf(lambda d: d["users"][0]["name"])
    assert path.to_xpath() == "/users/0/name"


def test_serialization_spaced_key_bracket():
    path: KeyOf[dict, Any] = KeyOf(lambda d: d["spaced key"])
    assert path.to_bracket() == "['spaced key']"


def test_serialization_dotted_key_bracket():
    path: KeyOf[dict, Any] = KeyOf(lambda d: d["dotted.key"])
    assert path.to_bracket() == "['dotted.key']"


def test_serialization_slashed_key_bracket():
    path: KeyOf[dict, Any] = KeyOf(lambda d: d["slash/key"])
    assert path.to_bracket() == "['slash/key']"


def test_str_representation():
    path: KeyOf[User, str] = KeyOf(lambda u: u.name)
    assert str(path) == "name"


def test_repr_representation():
    path: KeyOf[User, str] = KeyOf(lambda u: u.name)
    assert repr(path) == "KeyOf(name)"


def test_fstring_representation():
    path: KeyOf[User, str] = KeyOf(lambda u: u.name)
    assert f"{path}" == "name"


def test_format_dsl_custom():
    path: KeyOf[User, Any] = KeyOf(lambda u: u.metadata["prefs"]["theme"])
    assert path.format("{root} -> {leaf}") == "metadata -> theme"


def test_format_dsl_depth():
    path: KeyOf[User, Any] = KeyOf(lambda u: u.metadata["prefs"]["theme"])
    assert path.format("Depth: {depth}") == "Depth: 3"


def test_format_dsl_custom_sep():
    # Test using {sep} in format template (triggers _JoinHelper.__format__ and join())
    path: KeyOf[User, Any] = KeyOf(lambda u: u.metadata["prefs"]["theme"])
    result = path.format("{sep}")
    assert result == "metadata.prefs.theme"


def test_format_dsl_sql_style():
    path: KeyOf[User, Any] = KeyOf(lambda u: u.metadata["prefs"]["theme"])
    assert path.format("SELECT * FROM {dot}") == "SELECT * FROM metadata.prefs.theme"


# ---------------------------------------------------------------------------
# Comparison and Hashing Tests
# ---------------------------------------------------------------------------


def test_equality_same_path():
    p1: KeyOf[User, str] = KeyOf(lambda u: u.name)
    p2: KeyOf[User, str] = KeyOf(lambda u: u.name)
    assert p1 == p2


def test_equality_different_path():
    p1: KeyOf[User, str] = KeyOf(lambda u: u.name)
    p3: KeyOf[User, int] = KeyOf(lambda u: u.id)
    assert p1 != p3


def test_equality_with_string():
    p1: KeyOf[User, str] = KeyOf(lambda u: u.name)
    assert p1 == "name"


def test_equality_with_string_nested():
    p: KeyOf[User, Any] = KeyOf(lambda u: u.address.city)  # type: ignore[union-attr]
    assert p == "address.city"


def test_not_equality_nested():
    p1: KeyOf[User, Any] = KeyOf(lambda u: u.address.city)  # type: ignore[union-attr]
    p2: KeyOf[User, Any] = KeyOf(lambda u: u.address.zipcode)  # type: ignore[union-attr]
    assert p1 != p2


def test_hashing():
    p1: KeyOf[User, str] = KeyOf(lambda u: u.name)
    p2: KeyOf[User, str] = KeyOf(lambda u: u.name)
    s = {p1, p2}
    assert len(s) == 1
    assert p1 in s


def test_sorting():
    p1: KeyOf[User, str] = KeyOf(lambda u: u.name)
    p2: KeyOf[User, int] = KeyOf(lambda u: u.id)
    p3: KeyOf[User, Any] = KeyOf(lambda u: u.metadata)

    # 'id' < 'metadata' < 'name'
    sorted_paths = sorted([p1, p2, p3])
    # path._parts usage for comparison: ("id",) < ("metadata",) < ("name",)
    assert sorted_paths == [p2, p3, p1]


# ---------------------------------------------------------------------------
# Immutability and Error Tests
# ---------------------------------------------------------------------------


def test_immutability_attr_set():
    path: KeyOf[User, str] = KeyOf(lambda u: u.name)
    with pytest.raises(AttributeError):
        path.some_attr = "value"  # type: ignore[attr-defined]


def test_immutability_parts_set():
    path: KeyOf[User, str] = KeyOf(lambda u: u.name)
    with pytest.raises(AttributeError):
        path._parts = ("hacked",)  # type: ignore[misc]


def test_invalid_construction_literal_string():
    with pytest.raises(TypeError):
        KeyOf(lambda x: "string literal")  # type: ignore[arg-type]


def test_invalid_construction_literal_int():
    with pytest.raises(TypeError):
        KeyOf(lambda x: 123)  # type: ignore[arg-type]


def test_none_path_handling():
    path_identity: KeyOf[User, User] = KeyOf(lambda x: x)
    assert path_identity.parts == ()
    assert str(path_identity) == ""
    assert path_identity.from_(User(1, "A", [], {}), default=None) is not None
    u = User(1, "A", [], {})
    assert path_identity.from_(u) == u


# ---------------------------------------------------------------------------
# Edge Case Coverage Tests
# ---------------------------------------------------------------------------


def test_equality_with_non_keyof_non_str():
    """Test __eq__ returns NotImplemented for non-KeyOf, non-str types."""
    path: KeyOf[User, str] = KeyOf(lambda u: u.name)
    # Comparing with int should return NotImplemented (which becomes False via ==)
    assert (path == 123) is False
    assert path.__eq__(None) is NotImplemented
    assert (path == []) is False


def test_lt_with_non_keyof():
    """Test __lt__ returns NotImplemented for non-KeyOf types."""
    path: KeyOf[User, str] = KeyOf(lambda u: u.name)
    # Comparing with non-KeyOf should return NotImplemented
    with pytest.raises(TypeError):
        _ = path < "string"  # type: ignore[operator]
    with pytest.raises(TypeError):
        _ = path < 123  # type: ignore[operator]


def test_proxy_dunder_access():
    """Test that accessing dunder attributes on proxy raises AttributeError."""
    # When the selector tries to access a non-standard dunder attribute,
    # __getattr__ is called and raises AttributeError
    with pytest.raises(AttributeError):
        KeyOf(lambda x: x.__custom_attr__)  # type: ignore[arg-type,misc]


def test_proxy_setattr():
    """Test that setting attributes on proxy raises TypeError."""

    def bad_selector(x: Any) -> Any:
        x.some_attr = "value"
        return x.some_attr

    with pytest.raises(TypeError, match="read-only"):
        KeyOf(bad_selector)


def test_nn_optional_chaining(user_data):
    """Test nn() for optional chaining through nullable attributes."""
    path: KeyOf[User, str] = KeyOf(lambda u: nn(u.address).city)
    assert path.parts == ("address", "city")
    assert path.from_(user_data) == "Wonderland"


def test_nn_pipe_syntax(user_data):
    """Test nn with pipe operator syntax."""
    path: KeyOf[User, str] = KeyOf(lambda u: (u.address | nn).city)
    assert path.parts == ("address", "city")
    assert path.from_(user_data) == "Wonderland"


def test_nn_with_none_and_default():
    """Test nn() paths handle None with defaults."""
    user_no_address = User(id=2, name="Bob", tags=[], metadata={}, address=None)
    path: KeyOf[User, str] = KeyOf(lambda u: nn(u.address).city)

    with pytest.raises(AttributeError):
        path.from_(user_no_address)

    assert path.from_(user_no_address, default="Unknown") == "Unknown"


if __name__ == "__main__":
    pytest.main([__file__])
