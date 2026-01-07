# ADR 0004: Centralized Utility Library

## Status

Accepted

## Context

During the v2.0 player management implementation, several developer experience issues were identified:

1. **Datetime handling inconsistency**: Datetime parsing and UTC conversion logic was scattered across multiple files (`BaseArtifact._parse_datetime_strings()`, individual model validators, service methods). This led to:

   - Inconsistent timezone handling
   - UTC conversion bugs (commits 9c7adb4, 47c8c6d)
   - Deprecation warnings from `datetime.utcnow()` usage (14 instances)

2. **Type definition duplication**: Custom types (e.g., `EntityId`, status enums) were defined inline in models using `Literal` types, leading to:

   - Code duplication across `Player`, `Campaign`, `Session`, `CharacterSheet` models
   - Inconsistent validation rules
   - Maintenance burden when updating validation logic

3. **Local development friction**: No standardized task runner, requiring developers to remember and type ad-hoc shell commands, leading to:

   - Onboarding friction for new developers
   - Inconsistent test execution
   - CI/local parity issues

4. **Code duplication**: Common patterns (timestamps, IDs, validation) repeated across models, violating DRY principles.

## Decision

We will introduce a centralized utility library (`src/gm_chatbot/lib/`) and standardized local development tooling via a `justfile`.

### 1. Utility Library Structure

Create `src/gm_chatbot/lib/` with:

- **`datetime.py`**: UTC-first datetime utilities

  - `utc_now()`: Replaces deprecated `datetime.utcnow()`
  - `ensure_utc()`: Converts any datetime to UTC
  - `parse_datetime()`: Parses ISO strings with `Z` suffix support
  - `format_datetime()`: Formats with presets (iso, human, date)

- **`types.py`**: Reusable Pydantic type definitions
  - `UTC_DATETIME`: Pydantic annotated type ensuring UTC timezone
  - `EntityId`: String type with validation (1-64 chars, alphanumeric + `_-`)
  - `NonEmptyStr`: String that strips whitespace and validates non-empty
  - `SlugStr`: Lowercase alphanumeric with hyphens (URL-safe)
  - `PositiveInt`: Integer with `gt=0` constraint
  - Status enums: `CampaignStatus`, `PlayerStatus`, `SessionStatus`, `CharacterType` (converted from `Literal` to `StrEnum`)

### 2. Justfile for Local Development

Create root-level `justfile` with recipes for:

- Testing: `test`, `test-unit`, `test-integration`, `test-cov`, `test-fast`
- Quality: `lint`, `lint-fix`, `format`, `format-check`, `typecheck`, `check`
- Development: `dev`, `dev-debug`, `shell`
- Data: `db-reset`, `db-seed`, `db-backup`
- CI: `ci`, `ci-full`
- Utilities: `clean`, `deps`, `deps-update`, `info`, `openapi`

### 3. Model Refactoring

Refactor all models to use new utilities:

- `BaseArtifact`: Use `lib.datetime.parse_datetime()` and `UTC_DATETIME` types
- `Player`, `Campaign`, `Session`, `CharacterSheet`: Use status enums and `utc_now()`
- All services: Replace `datetime.utcnow()` with `utc_now()`

### 4. Backward Compatibility

- Status enums accept both string and enum values (via `BeforeValidator`)
- Existing YAML files continue to parse correctly
- API contracts remain unchanged (enums serialize as strings)

## Consequences

### Positive

- **Reduced bugs**: Centralized datetime handling eliminates timezone-related bugs
- **Better DX**: Standardized task runner reduces onboarding time and improves consistency
- **Type safety**: Reusable types ensure consistent validation across models
- **Maintainability**: DRY principles reduce code duplication (~150 LOC → <50 LOC)
- **No deprecation warnings**: All `datetime.utcnow()` calls replaced

### Negative

- **Migration effort**: Requires refactoring existing models and services
- **Learning curve**: Developers need to learn new utility functions and `just` commands
- **Additional abstraction**: One more layer of indirection

### Neutral

- **Additional dependencies**: `just` must be installed (but has fallback to manual commands)
- **Type checking**: Stricter type checking may surface existing issues (but improves code quality)

## Implementation

- **Phase 1**: Create `lib/` module and `justfile` (Day 1)
- **Phase 2**: Refactor core models (Day 1-2)
- **Phase 3**: Fix all service datetime calls (Day 2)
- **Phase 4**: Testing and verification (Day 2-3)
- **Phase 5**: Documentation updates (Day 3)

## References

- PRD-2026-004: Developer Experience Improvements — Utility Library & Local Development Tooling
- ADR-0003: Current Architecture State
- Commit 9c7adb4: UTC conversion bug fix
- Commit 47c8c6d: Datetime handling fix
