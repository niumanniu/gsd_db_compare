# Project Research Summary

**Project:** DB Compare - v1.1 Schema Selection & Multi-Mode Enhancement
**Domain:** Database Schema Comparison Tools
**Researched:** 2026-03-29
**Confidence:** HIGH

## Executive Summary

DB Compare is a database schema comparison tool that enables users to compare MySQL and Oracle database structures. The existing architecture already implements the three core comparison modes (single-table, multi-table, and database-level), and the primary enhancement needed is schema selection UI for database-level comparison—specifically for Oracle multi-schema scenarios.

The recommended approach is to extend the existing adapter layer with `get_schemas()` methods for schema enumeration, add a schema dropdown to the frontend that appears only in database-level mode, and pass schema filters through to the existing `get_tables()` calls. No new libraries or dependencies are required; all functionality can be built with the existing FastAPI/React/Ant Design stack.

Key risks include performance degradation when enumerating schemas/tables on large databases (500+ tables), case sensitivity issues when comparing across MySQL and Oracle, and state desynchronization when switching between comparison modes. These can be mitigated through virtual scrolling, schema name normalization, and atomic state resets on mode changes.

## Key Findings

### Recommended Stack

**Key Finding: NO NEW DEPENDENCIES REQUIRED.** The existing stack fully supports all required features.

**Core technologies:**
- **FastAPI + Pydantic**: API framework with request validation — already handles all comparison endpoints
- **SQLAlchemy 2.0+**: Metadata reflection — schema-agnostic, works unchanged with schema filtering
- **mysql-connector-python 8.0+**: MySQL driver — queries `information_schema.TABLES` which is already schema-scoped
- **oracledb 2.0+**: Oracle driver — needs `OWNER` filter addition for schema selection support
- **Ant Design 5.22+**: UI components — `Select` component supports search, multi-select, and virtualization
- **Zustand 5.0+**: State management — sufficient for mode state and selection handling

**Critical version notes:** All existing dependencies are current and sufficient. No upgrades needed.

### Expected Features

**Must have (table stakes):**
- **Schema dropdown selection** — users need to select which schemas/databases to compare
- **Mode switcher (Single/Multi/Database)** — already implemented in TableBrowser.tsx
- **Multi-select table UI** — checkbox-based selection for multi-table mode
- **Exclude pattern filtering** — wildcard support for system tables (`sys_*`, `*_log`)
- **Connection prerequisite enforcement** — disable table selection until connections chosen
- **Auto-match same-name tables** — tables with identical names should auto-pair

**Should have (competitive):**
- **Schema-level selection for database mode** — Oracle-specific; MySQL schema = database
- **Comparison preview count** — show "X tables will be compared" before running
- **Exclude pattern presets** — common patterns like "System Tables", "Temp Tables"
- **Real-time pattern matching preview** — show which tables match as user types patterns

**Defer (v2+):**
- **Manual table mapping UI** — complex drag-drop for differently-named tables
- **Save table selection groups** — premature without usage pattern validation
- **Table dependency ordering** — advanced feature for complex schemas
- **Progressive results loading** — optimization for very large batch comparisons

### Architecture Approach

The architecture extends the existing adapter layer with schema enumeration capabilities while keeping the comparison logic unchanged. Schema filtering happens at fetch time, not during comparison.

**Major components:**
1. **DatabaseAdapter (base)** — add abstract `get_schemas()` method and `get_tables(schema?)` signature
2. **MySQLAdapter/OracleAdapter** — implement schema listing via `information_schema.SCHEMATA` and `ALL_USERS`
3. **GET /api/connections/{id}/schemas** — new endpoint for schema enumeration
4. **TableBrowser.tsx** — add schema dropdown UI (database mode only), conditional on mode state
5. **App.tsx** — add schema state (`sourceSchema`, `targetSchema`) and React Query hooks for schema fetching

### Critical Pitfalls

1. **Schema enumeration performance on large databases** — Naive full-fetch of all schemas/tables causes UI freeze with 500+ tables. **Prevention:** Implement virtual scrolling + search-as-you-type from day one; add backend pagination with `limit` parameter.

2. **State desynchronization between compare modes** — Switching modes (single→multi→database) causes stale selections to persist. **Prevention:** Use single state object for mode-specific selections; reset atomically on mode change.

3. **Database-level comparison memory exhaustion** — Loading ALL tables into memory before returning causes OOM on 500+ table databases. **Prevention:** Cap at 200 tables max; consider streaming results with `StreamingResponse`.

4. **Cross-database schema name case sensitivity** — MySQL case sensitivity varies by OS; Oracle always uppercase. **Prevention:** Normalize schema names by database type before comparison; use explicit collation in queries.

5. **Exclude pattern ambiguity** — Wildcard patterns like `sys_*` behave unexpectedly with special characters. **Prevention:** Use `fnmatch` for proper glob-to-regex conversion; add real-time "matching tables" preview.

## Implications for Roadmap

Based on research, suggested phase structure:

### Phase 1: Schema Selection UI (Backend + Frontend)
**Rationale:** Foundational feature—schema enumeration must work before users can select schemas. This phase unblocks all database-level comparison enhancements.
**Delivers:** Schema dropdown for database-level comparison (Oracle focus), schema-filtered table fetching
**Addresses:** Schema selection feature from FEATURES.md, Oracle multi-schema support
**Avoids:** Pitfall #2 (case sensitivity) via schema normalization, Pitfall #10 (empty schema edge case) via validation

### Phase 2: Multi-Mode Comparison Polish
**Rationale:** Existing mode switching needs state management fixes to prevent desynchronization. Independent from schema selection but critical for UX.
**Delivers:** Atomic state reset on mode changes, multi-select table UI, auto-match display
**Uses:** Zustand state management patterns from existing code
**Implements:** Component Boundaries pattern from ARCHITECTURE.md (TableBrowser mode-specific rendering)
**Avoids:** Pitfall #3 (state desynchronization), Pitfall #7 (concurrent race conditions)

### Phase 3: Database-Level Comparison Hardening
**Rationale:** Once schema selection works, database-level comparison needs performance and scalability improvements.
**Delivers:** Exclude pattern filtering with preview, table count caps, memory-safe comparison
**Uses:** fnmatch for pattern matching, optional FastAPI StreamingResponse for large results
**Implements:** Pattern 2 (Schema-Parameterized Table Fetching) from ARCHITECTURE.md
**Avoids:** Pitfall #4 (memory exhaustion), Pitfall #6 (exclude pattern ambiguity)

### Phase Ordering Rationale

- **Phase 1 first** because schema enumeration (`get_schemas()`) is a prerequisite for schema dropdown UI and schema-filtered table fetching. Without this, database-level comparison cannot scope to specific schemas.

- **Phase 2 can run parallel** to Phase 1—mode switching state fixes are independent from schema selection. However, Phase 2's multi-select UI benefits from Phase 1's table fetching improvements.

- **Phase 3 last** because exclude patterns and memory optimization only matter once schema selection is working. Database-level comparison is the most complex mode and should be built on stable foundations.

### Research Flags

**Phases likely needing deeper research during planning:**
- **Phase 3:** StreamingResponse implementation for large comparisons—needs performance testing to determine if pagination or streaming is better fit

**Phases with standard patterns (skip research-phase):**
- **Phase 1:** Schema enumeration is well-documented (`information_schema.SCHEMATA`, `ALL_USERS` queries)
- **Phase 2:** State management patterns are established in existing codebase (Zustand, React Query)
- **Phase 3:** `fnmatch` for glob patterns is standard Python; table count limiting is straightforward

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | Existing dependencies confirmed sufficient; no new libraries needed |
| Features | MEDIUM | Based on competitor analysis (Redgate SQL Compare, dbForge); user validation needed for prioritization |
| Architecture | HIGH | Extends existing patterns; `get_schemas()` is standard metadata query |
| Pitfalls | MEDIUM | Inferred from codebase analysis and standard UX patterns; some untested assumptions |

**Overall confidence:** HIGH

### Gaps to Address

- **Oracle OWNER filtering**: The `ALL_TABLES WHERE OWNER = :schema` pattern needs validation against actual Oracle instances with multi-schema databases.

- **Large schema enumeration**: Performance thresholds (500+ tables causing UI freeze) are estimated; actual impact depends on network latency and Ant Design Select rendering.

- **Exclude pattern UX**: Real-time matching preview implementation details need UI/UX refinement during frontend development.

## Sources

### Primary (HIGH confidence)
- Existing codebase analysis (`backend/app/api/compare.py`, `backend/app/adapters/`, `frontend/src/components/TableBrowser.tsx`) — confirmed working comparison modes and adapter structure
- MySQL documentation: `information_schema.SCHEMATA`, `information_schema.TABLES` schema filtering
- Oracle documentation: `ALL_TABLES`, `ALL_USERS` system views

### Secondary (MEDIUM confidence)
- Ant Design Select performance documentation — virtual scrolling and search-as-you-type patterns
- FastAPI StreamingResponse documentation — streaming large result sets
- React Query mutation concurrency patterns — preventing race conditions

### Tertiary (LOW confidence)
- Competitor feature analysis (Redgate SQL Compare, dbForge Studio) — UI patterns inferred from product websites, not hands-on testing
- Industry patterns from database tool UX research (2024-2025) — general best practices, not MySQL/Oracle-specific

---
*Research completed: 2026-03-29*
*Ready for roadmap: yes*
