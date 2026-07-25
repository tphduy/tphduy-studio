---
paths:
  - "**/*.py"
---
# Python Style Rules

Applies to all `*.py` files.

1. **Prefer immutable data structures** — use `@dataclass(frozen=True)` or `NamedTuple` for data that should not change after creation; plain `@dataclass` is mutable and allows accidental field reassignment.

```python
# Bad — mutable by default, fields can be reassigned accidentally
@dataclass
class User:
    name: str
    email: str

# Good — frozen dataclass
@dataclass(frozen=True)
class User:
    name: str
    email: str

# Good — NamedTuple
class Point(NamedTuple):
    x: float
    y: float
```

2. **Use Protocol for interfaces, dataclass for DTOs** — `Protocol` enables structural subtyping (duck typing) without forcing explicit inheritance; `@dataclass` replaces raw dicts/tuples for typed data transfer objects.

```python
# Bad — ABC forces explicit inheritance coupling
from abc import ABC, abstractmethod
class Repository(ABC):
    @abstractmethod
    def find_by_id(self, id: str) -> dict | None: ...

# Good — Protocol enables structural subtyping (duck typing)
class Repository(Protocol):
    def find_by_id(self, id: str) -> dict | None: ...
    def save(self, entity: dict) -> dict: ...

# Bad — raw dict as DTO, no type safety
def create_user(data: dict) -> dict: ...

# Good — dataclass DTO
@dataclass
class CreateUserRequest:
    name: str
    email: str
    age: int | None = None
```

3. **Compare enums with `match`/`case`, never raw values** — comparing against raw strings or ints silently breaks when enum values change; `match` also makes exhaustiveness visible via `case _:`.

```python
# Bad
if status == "active":
    ...
elif status == "inactive":
    ...

# Good — match on enum members
match status:
    case UserStatus.ACTIVE:
        ...
    case UserStatus.INACTIVE:
        ...
    case _:
        ...
```
