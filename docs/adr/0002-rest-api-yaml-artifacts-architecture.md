# ADR 0002: REST API-First Architecture with YAML Artifacts

## Status

Accepted

## Context

The original GM Chatbot (v1.0) implemented a WebSocket bridge architecture that connected Roll20's chat interface to a Python backend. While functional, this architecture had significant limitations:

### Pain Points

1. **Tight Coupling**: Game rules were hardcoded in Python (`shadowdark_rules.py`), requiring code changes for any rule modification or new game system support.

2. **Single Campaign Limitation**: The architecture assumed one active game session per server instance with no persistence. Campaign state was lost on server restart.

3. **Platform Lock-in**: The Roll20 integration via Tampermonkey userscript was the only supported interface, preventing support for other VTTs or platforms.

4. **Embedded Calculations**: Dice rolling and game mechanics were calculated directly in application code rather than through verifiable, auditable tools.

5. **No Validation Layer**: Artifacts and game state lacked comprehensive type safety and validation, leading to potential runtime errors.

6. **WebSocket-Only API**: No REST API prevented easy development of alternative clients, integration with other tools, or programmatic access.

7. **Outdated Tooling**: Used pip + requirements.txt instead of modern Python package management.

### Requirements

The system needed to:

- Support multiple concurrent campaigns with persistent state
- Decouple game rules from code to enable multi-system support
- Provide a REST API for broad client compatibility
- Enforce type safety across all data models
- Externalize dice rolling for auditability
- Abstract platform integrations for extensibility
- Modernize the development toolchain

## Decision

We have redesigned the system with a **REST API-first architecture** using **YAML-based artifacts** for persistence. The new architecture (v2.0) consists of:

### Core Architectural Decisions

1. **REST API as Primary Interface**

   - FastAPI with OpenAPI 3.1 specification
   - Scalar API Reference for interactive documentation
   - WebSocket support for real-time chat (secondary to REST)
   - Standard HTTP methods and status codes

2. **YAML-Based Artifact Persistence**

   - All campaign data stored as validated YAML files
   - Campaign structure: `campaigns/{id}/campaign.yaml`, `characters/*.yaml`, `modules/*.yaml`, `state/*.yaml`
   - Human-readable, version-controllable, and tool-friendly format
   - No database dependency

3. **YAML-Based Game Rules**

   - Rules defined in `rules/{system}/core.yaml` format
   - Multiple game systems can coexist (Shadowdark, D&D 5e, Pathfinder, etc.)
   - Rules loaded dynamically without code changes
   - Validated against Pydantic schemas on load

4. **Type-Safe Models with Pydantic v2**

   - All data models use Pydantic with strict validation
   - `BaseArtifact` class for all YAML-serializable models
   - Comprehensive validation before persistence
   - Type hints throughout codebase

5. **External Dice Tools**

   - Dice rolling delegated to external tools (CLI, REST API, or deterministic for testing)
   - No direct random number generation in application code
   - Auditable dice results with full breakdown
   - Tool registry pattern for multiple implementations

6. **Platform Adapter Abstraction**

   - `PlatformAdapter` protocol for VTT/platform integration
   - Implementations: REST (primary), Roll20 WebSocket, Discord, CLI
   - Easy to add new platform support

7. **Service Layer Architecture**

   - Separation of concerns: API → Services → Artifacts/Tools
   - Services: CampaignService, CharacterService, GameStateService, GMService
   - Artifact Store handles YAML persistence
   - Rules Engine handles rule loading and querying

8. **Modern Python Toolchain**
   - UV for package management (replaces pip)
   - Ruff for linting and formatting
   - ty for type checking
   - Pytest for testing

### Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         Client Layer                             │
├─────────────┬─────────────┬─────────────┬───────────────────────┤
│  Typer CLI │  Roll20 WS  │  Discord   │  Web Client           │
└─────────────┴─────────────┴─────────────┴───────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────────┐
│                    REST API Layer (FastAPI)                     │
│  Campaigns │ Characters │ Actions │ Chat/GM │ Tools │ Rules    │
└──────────────────────────────────────┬──────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────┐
│                        Service Layer                            │
│  Campaign │ Character │ Game State │ GM/Chat                    │
└──────────────────────────────────────┬──────────────────────────┘
         │                             │                             │
         ▼                             ▼                             ▼
┌─────────────────┐         ┌──────────────────┐         ┌────────────────────┐
│  Rules Engine   │         │  Artifact Store  │         │   Tool Registry    │
│  (YAML Loader)  │         │  (YAML Store)    │         │  (Dice, LLM)       │
└─────────────────┘         └──────────────────┘         └────────────────────┘
         │                             │                             │
         └──────────────────┬──────────┴──────────────┬──────────────┘
                            │                         │
                            ▼                         ▼
                  ┌──────────────────┐       ┌──────────────────┐
                  │   File System    │       │   External APIs  │
                  │ (YAML Artifacts) │       │  (LLM, Dice)     │
                  └──────────────────┘       └──────────────────┘
```

## Consequences

### Positive

1. **Multi-Campaign Support**: System can handle multiple concurrent campaigns with isolated state, enabling production deployment for multiple game groups.

2. **Rule System Flexibility**: New game systems can be added by creating YAML rule files without code changes. Rules can be modified without redeployment.

3. **Client Flexibility**: REST API enables any HTTP client to interact with the system. Web clients, mobile apps, CLI tools, and integrations are all possible.

4. **Type Safety**: Pydantic validation catches errors at API boundaries, preventing invalid data from entering the system.

5. **Auditability**: External dice tools provide verifiable, auditable dice rolls. YAML artifacts provide human-readable audit trails.

6. **Developer Experience**: Modern toolchain (UV, Ruff, ty) provides faster development cycles, better type checking, and consistent code quality.

7. **Platform Extensibility**: Adapter pattern makes it easy to add support for new VTTs or platforms without modifying core logic.

8. **Version Control Friendly**: YAML artifacts can be version controlled, enabling campaign history tracking and rollback capabilities.

9. **No Database Dependency**: YAML file-based persistence eliminates database setup and maintenance overhead.

10. **API Documentation**: OpenAPI 3.1 spec enables automatic client generation and comprehensive API documentation.

### Negative

1. **File System Performance**: YAML file I/O may be slower than database operations for high-volume scenarios, though sufficient for current scale.

2. **Concurrent Write Challenges**: File-based persistence requires careful handling of concurrent writes (mitigated by sequential action processing).

3. **No Built-in Querying**: Unlike databases, YAML files don't support complex queries. All filtering/sorting must be done in application code.

4. **Migration Complexity**: Transitioning from v1.0 required significant refactoring and migration of existing data structures.

5. **Learning Curve**: Team members need to understand YAML artifact structure and Pydantic validation patterns.

6. **Tool Dependency**: External dice tools add a dependency and potential failure point (mitigated by tool registry with fallbacks).

### Neutral

1. **Scalability**: Architecture can scale horizontally, but state is not shared across instances (by design for current use case).

2. **Deployment**: Still containerized and deployable to Fly.io, but with updated Dockerfile and configuration.

3. **Backward Compatibility**: v1.0 clients (Roll20 userscript) require updates to work with v2.0 REST API.

4. **State Management**: Sequential action processing ensures consistency but may limit some real-time use cases (acceptable trade-off).

## Implementation Notes

- See [requirements.md](../requirements.md) for complete functional and non-functional requirements
- Implementation follows the service layer pattern with clear separation of concerns
- All artifacts are validated before persistence using Pydantic models
- Rules engine caches loaded YAML rules for performance
- Tool registry allows runtime selection of dice tool implementation

## References

- [ADR 0001: Architecture Overview](0001-architecture-overview.md) - Previous architecture (v1.0)
- [Requirements Document](../requirements.md) - Complete v2.0 specification
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Pydantic v2 Documentation](https://docs.pydantic.dev/)
- [UV Package Manager](https://github.com/astral-sh/uv)
