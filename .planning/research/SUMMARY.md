# Research Summary: DB Compare - 数据库库表比对系统

**Domain:** Database Comparison System for NOC/DBA Teams
**Researched:** 2026-03-28
**Overall confidence:** HIGH

## Executive Summary

DB Compare is a greenfield database comparison tool designed for Chinese internet company operations teams. The system supports MySQL and Oracle databases, providing table schema comparison and data comparison capabilities. The key value proposition is reducing manual comparison errors, improving change verification efficiency, and ensuring environment consistency.

The 2025-2026 technology stack centers on **Python 3.11+ with FastAPI** for backend (excellent database ecosystem with SQLAlchemy, cx_Oracle, mysql-connector), **React 18+ with TypeScript** for frontend (Ant Design for enterprise UI), and **PostgreSQL 16+** for operational data storage (configuration, history, scheduled tasks).

The architecture follows a **layered adapter pattern**: Database Adapters (MySQL/Oracle) → Comparison Engine (Schema/Data) → API Layer → Presentation (Web UI). Critical design decisions include **read-only mode** (no DDL/DML execution), **adapter pattern for multi-database support**, and **batch processing for large table comparison**.

The feature roadmap prioritizes **MySQL schema comparison** (Phase 1), followed by **Oracle support and cross-database comparison** (Phase 2), **data comparison engine** (Phase 3), and **scheduling/alerting automation** (Phase 4).

Key pitfalls identified from industry patterns include: metadata query performance on large schemas, data type mapping complexity between MySQL/Oracle, character set/collation differences, and large table comparison memory exhaustion. The research recommends strict MVP scope (MySQL first, defer Oracle to Phase 2) and explicit performance gate reviews for large table handling.

## Key Findings

**Stack:** Python 3.11+ + FastAPI for backend (database driver ecosystem maturity), React 18+ + TypeScript + Ant Design for frontend (enterprise dashboard components), PostgreSQL 16+ + Redis 7+ for data layer (configuration storage + caching). Database drivers: `mysql-connector-python` or `aiomysql` for MySQL, `oracledb` (formerly cx_Oracle) for Oracle.

**Architecture:** Layered adapter architecture with 4 layers: Database Adapter Layer (MySQL/Oracle connectors) → Comparison Engine (schema/data comparators) → API Layer (FastAPI REST) → Presentation (React Web UI). Event Queue (Redis/Celery) for async comparison tasks. Build order: Foundation → Schema Comparison → Data Comparison → Automation.

**Critical pitfall:** **Metadata Query Performance** — naive information_schema queries on databases with 10000+ tables can take 30+ seconds. Prevention: selective metadata loading, query optimization, result caching. Second critical pitfall: **Large Table Comparison Memory Exhaustion** — loading entire tables into memory causes OOM. Prevention: streaming comparison, chunked processing, hash-based validation.

## Implications for Roadmap

Based on research, suggested phase structure:

### Phase 1: Foundation (MySQL Schema Comparison)
- **Goal:** Prove value via MySQL schema comparison without Oracle complexity
- **Features:** MySQL connection management, information_schema metadata extraction, table structure comparison (columns, indexes, constraints), basic Web UI for diff visualization
- **Architecture:** MySQL adapter, SQLAlchemy metadata reflection, diff algorithm, FastAPI backend, React frontend
- **Avoids:** Pitfall #1 (Oracle complexity early) — defer to Phase 2; Pitfall #2 (Memory exhaustion) — streaming queries from Day 1

### Phase 2: Multi-Database (Oracle + Cross-DB Comparison)
- **Goal:** Extend to Oracle and enable cross-database comparison
- **Features:** Oracle adapter (ALL_TAB_COLUMNS, ALL_CONSTRAINTS), unified metadata abstraction, MySQL<->Oracle type mapping, cross-database schema comparison, HTML report generation
- **Architecture:** Oracle adapter, unified metadata layer, type mapping registry, report generator (Jinja2)
- **Avoids:** Pitfall #3 (Type mapping complexity) — explicit mapping table; Pitfall #4 (Character set issues) — normalization layer

### Phase 3: Data Comparison Engine
- **Goal:** Deliver data comparison capabilities
- **Features:** Full table comparison (small tables), sampling comparison (large tables), key column comparison, MD5 hash validation, data diff visualization
- **Architecture:** Data comparison engine, chunked query processor, hash calculator, streaming comparator
- **Avoids:** Pitfall #2 (Memory exhaustion) — chunked processing; Pitfall #5 (NULL handling) — explicit NULL-safe comparison

### Phase 4: Automation (Scheduling & Alerting)
- **Goal:** Enable automated comparison workflows
- **Features:** Scheduled comparison tasks, alert notifications (email/DingTalk/WeCom), comparison history tracking, trend analysis and statistics
- **Architecture:** Task scheduler (Celery), notification integrations, history storage, analytics engine
- **Avoids:** Pitfall #6 (Resource contention) — rate limiting, concurrency control

**Phase ordering rationale:**
1. **MySQL first** — Simpler metadata schema, wider adoption, faster time to value
2. **Schema before data** — Structure comparison is prerequisite for meaningful data comparison
3. **Read-only before write** — Build trust before considering sync capabilities
4. **Manual before automated** — Prove value manually, then automate

**Research flags for phases:**
- **Phase 1:** LOW research risk — standard information_schema queries, well-documented MySQL metadata
- **Phase 2:** MEDIUM research risk — Oracle system views, MySQL/Oracle type mapping nuances, character set normalization
- **Phase 3:** MEDIUM-HIGH research risk — efficient data comparison algorithms, BLOB/CLOB handling, NULL-safe comparison
- **Phase 4:** LOW research risk — standard Celery patterns, common notification APIs

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| **Stack** | HIGH | Python/FastAPI, React/TS, PostgreSQL are industry standards. Database drivers (mysql-connector, oracledb) are vendor-supported official libraries. |
| **Features** | HIGH | Schema/data comparison patterns are well-established. Feature set synthesized from existing tools (Redgate SQL Compare, dbt, DataGrip diff). |
| **Architecture** | MEDIUM-HIGH | Adapter pattern is standard for multi-database tools. Specific implementation details (streaming vs. batch processing) may vary based on performance requirements. |
| **Pitfalls** | MEDIUM | Derived from database tool development patterns, community discussions, and logical inference. Performance pitfalls (metadata query, memory exhaustion) are well-documented. |

## Gaps to Address

### Areas Where Research Is Inconclusive

1. **Oracle Connection Method**
   - **Gap:** Should we use instant client, basic driver, or full Oracle client?
   - **Phase:** Phase 2
   - **Research needed:** Compare deployment complexity, licensing requirements, feature support

2. **Data Comparison Algorithm Selection**
   - **Gap:** What's the best algorithm for large table comparison? Full scan with hash? Sampling? Checksum?
   - **Phase:** Phase 3
   - **Research needed:** Benchmark accuracy vs. performance trade-offs for different approaches

3. **Character Set Normalization**
   - **Gap:** How to handle MySQL utf8mb4 vs Oracle AL32UTF8 comparisons?
   - **Phase:** Phase 2
   - **Research needed:** Edge cases in string comparison, collation differences

4. **Large Table Threshold**
   - **Gap:** What row count triggers "large table" handling? 10K? 1M? 100M?
   - **Phase:** Phase 3
   - **Research needed:** Performance testing with realistic data volumes

5. **Cross-Database Type Mapping**
   - **Gap:** How to map MySQL DATETIME to Oracle DATE/TIMESTAMP? DECIMAL to NUMBER?
   - **Phase:** Phase 2
   - **Research needed:** Comprehensive type mapping table with edge cases

### Topics Needing Phase-Specific Research Later

| Phase | Topic | Why Defer |
|-------|-------|-----------|
| Phase 2 | Oracle driver deployment | Depends on customer environment (instant client availability, licensing) |
| Phase 2 | MySQL/Oracle type mapping | Need real schema examples from Phase 1 to validate mapping |
| Phase 3 | Data comparison algorithm tuning | Depends on typical table sizes from Phase 1 usage |
| Phase 3 | BLOB/CLOB comparison strategy | Need customer data patterns to determine best approach |
| Phase 4 | Notification channel prioritization | Depends on customer preferences (email vs. DingTalk vs. WeCom) |

## Sources

- MySQL information_schema documentation: https://dev.mysql.com/doc/refman/8.0/en/information-schema.html
- Oracle data dictionary views: https://docs.oracle.com/en/database/oracle/oracle-database/19/sqlrf/Data-Dictionary-Views.html
- SQLAlchemy reflection documentation: https://docs.sqlalchemy.org/en/20/core/reflection.html
- Python oracledb driver: https://oracle.github.io/python-oracledb/
- MySQL connector documentation: https://dev.mysql.com/doc/connector-python/en/
- Database comparison tools analysis: Redgate SQL Compare, ApexSQL Diff
- Data comparison algorithms: Hash-based vs. row-by-row comparison patterns

---

*Research complete. Files to be written to `.planning/research/`:*
- `SUMMARY.md` — This file (executive summary + roadmap implications)
- `STACK.md` — Technology stack recommendations with versions and rationale
- `FEATURES.md` — Feature landscape (table stakes, differentiators, anti-features)
- `ARCHITECTURE.md` — Architecture patterns, component boundaries, data flows
- `PITFALLS.md` — Domain pitfalls with prevention strategies and phase mappings
