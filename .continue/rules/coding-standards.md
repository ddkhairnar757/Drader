# Coding Standards

## Layered Architecture
Structure all modules in this order:
```
models/      — Pydantic models / dataclasses
schemas/     — Database schema definitions
repositories/ — Database access only
services/    — Business logic only
tests/       — Unit tests
```

## Responsibility Rules
- **Repositories**: Database access only. No business logic.
- **Services**: Business logic only. No direct database access.
- Keep files small and focused. One responsibility per module.

## File Organisation
- Prefer many small modules over one large file.
- Each module should have a clear single purpose.
- Name files after their primary export.

## Database
- Generate migrations separately as SQL scripts.
- Migrations go in a `migrations/` directory.
- Do not use ORM auto-migrations.

## When Asked to Build a Feature
1. Create the smallest working version first.
2. Do not modify unrelated files.
3. Do not add features that were not requested.
4. Do not pre-optimise for scale.

## General
- Use type hints everywhere.
- Use explicit imports (no `from module import *`).
- Prefer dataclasses and Pydantic over raw dicts.
- Write docstrings for public functions and classes.