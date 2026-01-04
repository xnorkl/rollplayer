# GM Chatbot Documentation

Welcome to the GM Chatbot documentation. This directory contains comprehensive guides for using, testing, and understanding the system.

## Documentation Index

### User Guides

- **[Usage Guide](usage.md)** - Complete API usage guide with examples for campaigns, characters, dice rolling, WebSocket chat, and YAML artifacts.

- **[Testing Guide](testing.md)** - Testing procedures, test structure, CI/CD integration, and manual testing examples.

### Architecture & Development

- **[Requirements Document](requirements.md)** - Complete feature requirements and architecture specification for the v2.0 redesign. This document is intended for architecture reference and development planning.

- **[Architecture Decision Records](adr/)** - Architecture decisions and design rationale:
  - [ADR 0001: Architecture Overview (v1.0)](adr/0001-architecture-overview.md) - Historical document for the original WebSocket-based architecture
  - [ADR 0002: REST API-First Architecture with YAML Artifacts (v2.0)](adr/0002-rest-api-yaml-artifacts-architecture.md) - Current architecture redesign

## Quick Links

- **Getting Started**: See the root [README.md](../README.md) for quick start instructions
- **API Documentation**: Visit `http://localhost:8000/docs` when the server is running
- **Deployment**: See [infrastructure/README.md](../infrastructure/README.md) for Fly.io deployment guide

## Documentation Structure

```
docs/
├── README.md              # This file - documentation index
├── usage.md                # API usage guide
├── testing.md              # Testing procedures
├── requirements.md         # Feature requirements (architecture reference)
└── adr/                    # Architecture Decision Records
    ├── 0001-architecture-overview.md  # Historical ADR (v1.0 architecture)
    └── 0002-rest-api-yaml-artifacts-architecture.md  # Current ADR (v2.0 architecture)
```
