# keyof

[![PyPI version](https://img.shields.io/pypi/v/py-keyof.svg)](https://pypi.org/project/py-keyof/)
[![Python versions](https://img.shields.io/pypi/pyversions/py-keyof.svg)](https://pypi.org/project/py-keyof/)
[![License](https://img.shields.io/pypi/l/py-keyof.svg)](https://github.com/eyusd/keyof/blob/main/LICENSE)
[![CI](https://github.com/eyusd/keyof/actions/workflows/ci.yml/badge.svg)](https://github.com/eyusd/keyof/actions/workflows/ci.yml)

Type-safe property paths for Python, inspired by TypeScript's `keyof`.

## What it does

```python
from dataclasses import dataclass
from keyof import KeyOf

@dataclass
class User:
    name: str
    email: str

# Define a path, your IDE autocompletes, your type checker validates
path = KeyOf(lambda u: u.name)

# Extract the value
user = User(name="Alice", email="alice@example.com")
path.from_(user)  # → "Alice"

# Serialize for APIs, configs, logs...
str(path)  # → "name"
```

## Installation

```bash
pip install py-keyof
```

## Why? 🤔

String-based paths like `"user.address.city"` are convenient, but they break silently when you rename a field. Your IDE can't autocomplete them, and typos only surface at runtime (usually in production, at 3am).

`keyof` uses a lambda to capture the path. Pylance/Pyright sees the lambda and validates every attribute access, so you get squiggly red lines in your editor instead of surprises in production.

## How it works (and Python's limitations)

Python doesn't have TypeScript's `keyof` operator, so we get a bit creative:

1. At runtime, the lambda receives a proxy object that records attribute accesses
2. At type-check time, the lambda is analyzed normally by Pylance/Pyright

The path gets validated statically, but the mechanism is admittedly a bit of a hack. The lambda never actually runs on real data, it only runs once during `KeyOf` construction to capture the path.

## Handling optional fields 🔗

When a field is `T | None`, accessing attributes on it is a type error. Use `nn()` to tell the type checker "trust me, this isn't None":

```python
from keyof import KeyOf, nn

@dataclass
class User:
    address: Address | None

# nn() strips None from the type (no-op at runtime)
path = KeyOf(lambda u: nn(u.address).city)

# Or with pipe syntax, if that's more your style
path = KeyOf(lambda u: (u.address | nn).city)
```

This is similar to TypeScript's `!` or Kotlin's `!!`. The path will still fail at runtime if the value is actually None. Use `path.from_(obj, default=...)` to handle that gracefully.

## Working with dicts and lists

Bracket access works too:

```python
data = {"users": [{"name": "Alice"}]}

path = KeyOf(lambda d: d["users"][0]["name"])
path.from_(data)  # → "Alice"
```

## Path introspection 🔍

```python
path = KeyOf(lambda u: u.address.city)

path.parts   # → ("address", "city")
path.depth   # → 2
path.root    # → "address"
path.leaf    # → "city"
path.parent()  # → KeyOf for "address"
```

## Serialization

Need your path in a different format? `keyof` got you covered:

```python
path = KeyOf(lambda u: u.address.city)

str(path)          # → "address.city"
path.to_jsonpath() # → "$.address.city"
path.to_bracket()  # → "['address']['city']"
path.to_posix()    # → "address/city"
path.to_xpath()    # → "/address/city"
```

## Equality and hashing

Paths are immutable and can be compared, hashed, and used in sets/dicts:

```python
p1 = KeyOf(lambda u: u.name)
p2 = KeyOf(lambda u: u.name)

p1 == p2      # True
p1 == "name"  # True (compares string representation)
{p1, p2}      # Set with one element
```

## Limitations ⚠️

- The lambda trick only works for attribute and item access. Method calls, arithmetic, or other expressions won't work.
- Pipe syntax `(x | nn)` needs parentheses because `.` binds tighter than `|`.
- There's no way to express "this path might not exist" at the type level. That's a runtime concern, handled by the `default` parameter.

## AI disclaimer 🤖

Some of the files in this project were generated with the help of AI, especially the config files and project scaffolding. Github Copilot suggestions were used for some of the implementation, tests, and documentation. While I strive to ensure its correctness and quality, please be aware that it may contain errors or suboptimal patterns. Always review and test the code before using it in production.

## License

MIT
