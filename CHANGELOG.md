# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-02-26

### Added

- Initial release of `keyof`
- `KeyOf[T, R]` class for type-safe property path navigation
- `nn()` helper for optional chaining: strips `None` from types in KeyOf selectors
- Pipe syntax support: `(u.address | nn).city` as alternative to `nn(u.address).city`
- Value extraction with `from_()` method and optional default values
- Path introspection: `parts`, `depth`, `root`, `leaf`, `parent()`
- Multiple serialization formats:
  - `to_dot()` - dot notation (`a.b.c`)
  - `to_posix()` - POSIX-style (`a/b/c`)
  - `to_bracket()` - bracket notation (`['a']['b']['c']`)
  - `to_jsonpath()` - JSONPath (`$.a.b.c`)
  - `to_xpath()` - XPath (`/a/b/c`)
  - `to_jmespath()` - JMESPath (`a.b.c`)
  - `format()` - custom template formatting
- Support for dataclasses, Pydantic models, NamedTuple, dicts, and lists
- Full type safety with Pylance/Pyright/mypy
- Immutable, hashable instances
- Comparison operators (`==`, `<`) and string equality
- Iteration over path segments
- Python 3.10-3.14 support

[1.0.0]: https://github.com/eyusd/keyof/releases/tag/v1.0.0
