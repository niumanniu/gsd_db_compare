# Technology Stack Recommendation: DB Compare

**Recommended:** 2026-03-28

## Backend

### Core Framework
| Component | Technology | Version | Rationale |
|-----------|------------|---------|-----------|
| **Language** | Python | 3.11+ | Excellent database ecosystem, strong typing support |
| **Web Framework** | FastAPI | 0.115+ | Async support, automatic OpenAPI docs, Pydantic validation |
| **ASGI Server** | Uvicorn | 0.30+ | High-performance async server |

### Database Drivers
| Database | Driver | Version | Rationale |
|----------|--------|---------|-----------|
| **MySQL** | mysql-connector-python | 8.0+ or aiomysql | Official Oracle driver, async option available |
| **Oracle** | oracledb | 2.0+ | Official Oracle driver (thin mode, no Instant Client needed for basic features) |
| **PostgreSQL** | psycopg2-binary | 2.9+ | For application data storage |

### ORM & Query Building
| Component | Technology | Version | Rationale |
|-----------|------------|---------|-----------|
| **ORM** | SQLAlchemy | 2.0+ | Industry standard, excellent metadata reflection |
| **Migrations** | Alembic | 1.12+ | Database schema migrations for app storage |

### Task Queue & Caching
| Component | Technology | Version | Rationale |
|-----------|------------|---------|-----------|
| **Task Queue** | Celery | 5.4+ | Distributed task execution, scheduling |
| **Broker/Cache** | Redis | 7.0+ | Task broker, result backend, caching |

### Logging & Monitoring
| Component | Technology | Version | Rationale |
|-----------|------------|---------|-----------|
| **Logging** | structlog | 24.0+ | Structured logging, JSON output |
| **Validation** | Pydantic | 2.0+ | Data validation, settings management |

### Key Backend Dependencies (pyproject.toml)
```toml
[project]
name = "db-compare-backend"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
    "fastapi>=0.115,<0.130",
    "uvicorn[standard]>=0.30",
    "pydantic>=2.0",
    "pydantic-settings>=2.0",
    "sqlalchemy>=2.0",
    "alembic>=1.12",
    "psycopg2-binary>=2.9",
    "mysql-connector-python>=8.0",
    "oracledb>=2.0",
    "celery[redis]>=5.4",
    "redis>=5.0",
    "structlog>=24.0",
    "httpx>=0.27",
    "jinja2>=3.1",
]
```

## Frontend

### Core Framework
| Component | Technology | Version | Rationale |
|-----------|------------|---------|-----------|
| **Framework** | React | 18.2+ | Largest component ecosystem, TypeScript support |
| **Language** | TypeScript | 5.0+ | Type safety, better IDE support |
| **Build Tool** | Vite | 5.0+ | Fast HMR, modern bundling |

### UI & State
| Component | Technology | Version | Rationale |
|-----------|------------|---------|-----------|
| **UI Library** | Ant Design | 5.0+ | Enterprise components, table-heavy UIs |
| **State Management** | Zustand | 4.0+ | Lightweight, simple API |
| **HTTP Client** | Axios | 1.6+ or TanStack Query | Request handling, caching |

### Data Visualization
| Component | Technology | Version | Rationale |
|-----------|------------|---------|-----------|
| **Diff Visualization** | react-diff-viewer | 3.1+ | Side-by-side diff display |
| **Tables** | TanStack Table | 8.0+ | Headless table with sorting, pagination |

### Key Frontend Dependencies (package.json)
```json
{
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "typescript": "^5.0.0",
    "antd": "^5.0.0",
    "zustand": "^4.0.0",
    "axios": "^1.6.0",
    "@tanstack/react-query": "^5.0.0",
    "@tanstack/react-table": "^8.0.0",
    "react-diff-viewer": "^3.1.0"
  },
  "devDependencies": {
    "vite": "^5.0.0",
    "@types/react": "^18.2.0",
    "@types/node": "^20.0.0"
  }
}
```

## Application Data Storage

### PostgreSQL Schema
| Table | Purpose | Notes |
|-------|---------|-------|
| `db_connections` | Stored database connection configs | Encrypted credentials |
| `comparison_tasks` | Task history and results | JSONB for diff results |
| `scheduled_jobs` | Cron-like scheduled comparisons | Celery beat integration |
| `users` | User accounts and preferences | If auth is needed |

## Development Tools

### Backend
| Tool | Purpose |
|------|---------|
| pytest | Testing framework |
| ruff | Linting and formatting |
| mypy | Type checking |
| httpie | API testing |

### Frontend
| Tool | Purpose |
|------|---------|
| eslint | Linting |
| prettier | Formatting |
| vitest | Unit testing |
| playwright | E2E testing |

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                      Frontend (React)                        │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │ Connection  │  │  Comparison │  │    Report Viewer    │  │
│  │  Manager    │  │   Results   │  │  (HTML/PDF Export)  │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                            │
                            │ REST API
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                 Backend (FastAPI + Celery)                   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              API Layer (FastAPI)                      │   │
│  └──────────────────────────────────────────────────────┘   │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │   MySQL     │  │   Oracle    │  │   Comparison        │  │
│  │   Adapter   │  │   Adapter   │  │   Engine            │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
│  ┌─────────────┐  ┌─────────────────────────────────────┐   │
│  │   Celery    │  │        PostgreSQL (App Data)         │   │
│  │   Worker    │  │  - connections, tasks, schedules     │   │
│  └─────────────┘  └─────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                            │
            ┌───────────────┼───────────────┐
            ▼               ▼               ▼
      ┌──────────┐   ┌──────────┐   ┌──────────┐
      │  MySQL   │   │  Oracle  │   │  Redis   │
      │  Server  │   │  Server  │   │  (Cache) │
      └──────────┘   └──────────┘   └──────────┘
```

## Deployment Considerations

### Oracle Driver Modes
- **Thin mode** (oracledb 2.0+): Pure Python, no Oracle client needed, basic features
- **Thick mode**: Requires Oracle Instant Client, full feature support

**Recommendation:** Start with thin mode for Phase 2, document thick mode setup for users needing advanced features.

### Memory Management
- Use streaming cursors for large table queries
- Process data in chunks (configurable: 1000-10000 rows)
- Clean up temporary data after comparison

### Security
- Encrypt stored database credentials (cryptography library)
- Use read-only database accounts
- Audit log for all comparison activities

---
*Last updated: 2026-03-28*
