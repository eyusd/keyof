"""
keyof.py
========
Type-safe property path navigation for Python.

A ``KeyOf[T]`` object captures a typed path through an object's attributes,
validated statically by Pylance/Pyright via a selector lambda.

Basic usage::

    from keyof import KeyOf

    @dataclass
    class Address:
        city: str

    @dataclass
    class User:
        name: str
        address: Address

    # T is inferred automatically from context, no need to specify User explicitly
    # in most generic contexts (e.g. function arguments, dataclass fields, etc.)
    city_path: KeyOf[User] = KeyOf(lambda u: u.address.city)

    # Retrieve a value
    user = User(name="Alice", address=Address(city="London"))
    city_path.from_(user)       # → "London"

    # Serialize to various string formats
    str(city_path)              # → "address.city"          (dot-separated, default)
    city_path.to_dot()          # → "address.city"
    city_path.to_posix()        # → "address/city"
    city_path.to_python()       # → "address.city"          (same as dot for attributes)
    city_path.to_bracket()      # → "['address']['city']"
    city_path.format("{root}::{sep.join(parts)}")  # custom via mini-DSL

    # With explicit return type annotation (optional)
    name_path: KeyOf[User, str] = KeyOf(lambda u: u.name)
"""

from __future__ import annotations

__all__ = ["KeyOf", "nn"]
__version__ = "1.0.0"

from typing import TYPE_CHECKING, Any, Generic, cast, final, overload

from typing_extensions import TypeVar

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator, Sequence

T = TypeVar("T")
R = TypeVar("R", default=Any)
_MISSING = object()  # sentinel for unset default


# ---------------------------------------------------------------------------
# Internal proxy - records attribute access at runtime
# ---------------------------------------------------------------------------


class _PathProxy:
    """
    Transparent proxy passed to the selector lambda at construction time.
    Every attribute access appends a segment to the recorded path.
    Never exposed publicly.
    """

    __slots__ = ("_parts",)
    _parts: tuple[str, ...]

    def __init__(self, parts: tuple[str, ...] = ()) -> None:
        object.__setattr__(self, "_parts", parts)

    def __getattr__(self, name: str) -> _PathProxy:
        if name.startswith("__") and name.endswith("__"):
            raise AttributeError(name)
        return _PathProxy((*self._parts, name))

    def __getitem__(self, key: Any) -> _PathProxy:
        return _PathProxy((*self._parts, str(key)))

    def __setattr__(self, name: str, value: Any) -> None:
        raise TypeError("_PathProxy is read-only")


_O = TypeVar("_O")


@final
class _NonNull:
    """
    Non-null assertion for optional chaining in KeyOf selectors.

    Strips ``None`` from the type, allowing chaining through optional attributes.
    At runtime this is a no-op. Similar to TypeScript's ``!`` or Kotlin's ``!!``.

    Supports both function call and pipe syntax::

        KeyOf(lambda u: nn(u.address).city)
        KeyOf(lambda u: (u.address | nn).city)
    """

    __slots__ = ()

    def __call__(self, value: _O | None) -> _O:
        return value  # type: ignore[return-value]

    def __ror__(self, value: _O | None) -> _O:
        return value  # type: ignore[return-value]


nn = _NonNull()


@final
class KeyOf(Generic[T, R]):
    """
    A statically type-checked path through the attributes of ``T``,
    with optional return-type annotation ``R``.

    Parameters
    ----------
    selector:
        A lambda (or any callable) that navigates from a ``T`` instance to
        the desired attribute.  Pylance/Pyright validates every access in the
        lambda body against ``T``.

    Examples
    --------
    >>> from dataclasses import dataclass
    >>> from keyof import KeyOf
    >>>
    >>> @dataclass
    ... class Inner:
    ...     value: int
    >>>
    >>> @dataclass
    ... class Outer:
    ...     inner: Inner
    ...     label: str
    >>>
    >>> path = KeyOf(lambda o: o.inner.value)
    >>> path.from_(Outer(inner=Inner(value=42), label="hi"))
    42
    >>> str(path)
    'inner.value'
    """

    # ------------------------------------------------------------------
    # Construction
    # ------------------------------------------------------------------

    def __init__(self, selector: Callable[[T], R]) -> None:
        proxy = selector(cast("T", _PathProxy()))
        if not isinstance(proxy, _PathProxy):
            raise TypeError(
                "KeyOf selector must return a property access chain, not a plain value. "
                "Use  KeyOf(lambda x: x.some.attribute)  not  KeyOf(lambda x: 'literal')."
            )
        self._parts: tuple[str, ...] = proxy._parts

    # ------------------------------------------------------------------
    # Value retrieval
    # ------------------------------------------------------------------

    @overload
    def from_(self, obj: T) -> R: ...
    @overload
    def from_(self, obj: T, default: R) -> R: ...
    @overload
    def from_(self, obj: T, default: Any) -> Any: ...

    def from_(self, obj: T, default: Any = _MISSING) -> Any:
        """
        Retrieve the value at this path from *obj*.

        Parameters
        ----------
        obj:
            An instance of ``T`` to navigate.
        default:
            Value to return if any segment along the path is ``None`` or
            missing.  If omitted and the path cannot be resolved,
            ``AttributeError`` is raised.

        Raises
        ------
        AttributeError
            If a path segment is missing and no *default* was provided.
        """
        current: Any = obj
        for i, part in enumerate(self._parts):
            if current is None:
                if default is _MISSING:
                    resolved = ".".join(self._parts[:i])
                    raise AttributeError(
                        f"Cannot resolve '{part}' on None "
                        f"(reached via '{resolved}' on {type(obj).__name__})"
                    )
                return default
            try:
                current = getattr(current, part)
            except AttributeError:
                # Fallback to item access (dict/list)
                try:
                    # If it's a list/tuple/str, try converting key to int
                    if isinstance(current, (list, tuple, str)) and part.isdigit():
                        current = current[int(part)]
                    else:
                        # Use cast("Any", ...) to avoid Pylance confusing "part" (str) with slice
                        # when it narrows types or infers constraints.
                        current = cast("Any", current)[part]
                except (KeyError, IndexError, TypeError):
                    if default is _MISSING:
                        raise AttributeError(
                            f"Cannot resolve '{part}' on {type(current).__name__} (path: '{'.'.join(self._parts[:i])}')"
                        ) from None
                    return default
        return current

    # ------------------------------------------------------------------
    # Path introspection
    # ------------------------------------------------------------------

    @property
    def parts(self) -> tuple[str, ...]:
        """The individual segments of this path, e.g. ``('address', 'city')``."""
        return self._parts

    @property
    def depth(self) -> int:
        """Number of segments in the path."""
        return len(self._parts)

    @property
    def leaf(self) -> str:
        """The last segment, e.g. ``'city'`` for ``address.city``."""
        return self._parts[-1]

    @property
    def root(self) -> str:
        """The first segment, e.g. ``'address'`` for ``address.city``."""
        return self._parts[0]

    def parent(self) -> KeyOf[T, Any]:
        """
        Return a new ``KeyOf`` representing the path one level up.

        Raises
        ------
        ValueError
            If the path has only one segment (no parent).
        """
        if len(self._parts) < 2:
            raise ValueError(f"Path '{self}' has no parent (depth=1).")
        child: KeyOf[T, Any] = object.__new__(KeyOf)
        object.__setattr__(child, "_parts", self._parts[:-1])
        return child

    # ------------------------------------------------------------------
    # String serialization
    # ------------------------------------------------------------------

    def to_dot(self) -> str:
        """``address.city``  - dot-separated (default)."""
        return ".".join(self._parts)

    def to_posix(self) -> str:
        """``address/city``  - POSIX-style slash-separated."""
        return "/".join(self._parts)

    def to_python(self) -> str:
        """
        ``root.address.city``  - valid Python attribute-access expression.
        The first segment is kept as a bare name; subsequent segments use ``.``.
        """
        return ".".join(self._parts)

    def to_bracket(self) -> str:
        """``['address']['city']``  - bracket notation (e.g. for JavaScript interop)."""
        return "".join(f"['{p}']" for p in self._parts)

    def to_jmespath(self) -> str:
        """``address.city``  - JMESPath-compatible dot notation."""
        return ".".join(self._parts)

    def to_jsonpath(self) -> str:
        """``$.address.city``  - JSONPath notation."""
        return "$." + ".".join(self._parts)

    def to_xpath(self) -> str:
        """``/address/city``  - XPath-style slash-separated with leading slash."""
        return "/" + "/".join(self._parts)

    def format(self, template: str) -> str:
        """
        Render the path using a custom template string.

        Available variables:

        - ``{parts}``   - the raw ``tuple[str, ...]`` of segments
        - ``{root}``    - first segment
        - ``{leaf}``    - last segment
        - ``{depth}``   - number of segments (int)
        - ``{dot}``     - dot-separated string
        - ``{posix}``   - slash-separated string
        - ``{bracket}`` - bracket notation string
        - ``{jsonpath}``- JSONPath string
        - ``{xpath}``   - XPath string

        The template also supports a special ``{sep.join(parts)}`` shorthand
        where *sep* is any literal separator you want.

        Examples
        --------
        >>> path.format("{root} > {leaf}")
        'address > city'
        >>> path.format("{depth} segments: {dot}")
        '2 segments: address.city'
        """

        # Provide a helper that lets users write e.g. "::".join(parts) in the template
        class _JoinHelper:
            def __init__(self, parts: Sequence[str]) -> None:
                self._parts = parts

            def join(self, sep: str = ".") -> str:
                return sep.join(self._parts)

            def __format__(self, spec: str) -> str:
                # Allows {sep.join(parts)} via format spec tricks - not needed
                # but keeps the template consistent.
                return self.join()

        return template.format(
            parts=self._parts,
            root=self.root,
            leaf=self.leaf,
            depth=self.depth,
            dot=self.to_dot(),
            posix=self.to_posix(),
            bracket=self.to_bracket(),
            jsonpath=self.to_jsonpath(),
            xpath=self.to_xpath(),
            sep=_JoinHelper(self._parts),
        )

    # ------------------------------------------------------------------
    # Dunder
    # ------------------------------------------------------------------

    def __str__(self) -> str:
        return self.to_dot()

    def __repr__(self) -> str:
        return "KeyOf(" + self.to_dot() + ")"

    def __hash__(self) -> int:
        return hash(self._parts)

    def __eq__(self, other: object) -> bool:
        if isinstance(other, KeyOf):
            return self._parts == other._parts
        if isinstance(other, str):
            return self.to_dot() == other
        return NotImplemented

    def __lt__(self, other: KeyOf[Any, Any]) -> bool:
        """Allows sorting a collection of ``KeyOf`` objects lexicographically."""
        if isinstance(other, KeyOf):
            return self._parts < other._parts
        return NotImplemented

    def __len__(self) -> int:
        return self.depth

    def __iter__(self) -> Iterator[str]:
        """Iterate over the path segments."""
        return iter(self._parts)

    def __contains__(self, segment: str) -> bool:
        """``'city' in path``  - checks whether a segment is part of this path."""
        return segment in self._parts

    def __setattr__(self, name: str, value: Any) -> None:
        if name == "_parts" and "_parts" not in self.__dict__:
            # Allow the single write during __init__ only
            object.__setattr__(self, name, value)
        else:
            raise AttributeError("KeyOf instances are immutable.")
