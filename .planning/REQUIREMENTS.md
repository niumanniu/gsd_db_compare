# Requirements - v1.1 完善比对功能

**Milestone:** v1.1 完善比对功能
**Status:** Active
**Created:** 2026-03-29

---

## v1 Requirements

### Schema Selection (SCH)

**SCH-01:** User can select source schema from dropdown when in database-level comparison mode

**SCH-02:** User can select target schema from dropdown when in database-level comparison mode

**SCH-03:** Schema dropdown shows only schemas from selected connections

**SCH-04:** Schema dropdown supports search/filter for databases with many schemas

**SCH-05:** Backend API endpoint /api/connections/{id}/schemas returns available schemas

### Multi-Mode Comparison (MODE)

**MODE-01:** Mode switcher clearly shows Single/Multi/Database options

**MODE-02:** Switching modes resets table/schema selections atomically (no stale state)

**MODE-03:** Multi-table mode shows count of selected tables

**MODE-04:** Auto-matched tables (same name) are visually indicated

### Database-Level Hardening (DB)

**DB-01:** User can add exclude patterns (wildcards like sys_*, *_log) to filter tables

**DB-02:** Real-time preview shows how many tables match current exclude patterns

**DB-03:** Comparison preview shows total table count before running

**DB-04:** Table count warning shown when comparing 200+ tables

---

## Summary

| Category | Count | IDs |
|----------|-------|-----|
| Schema Selection | 5 | SCH-01 to SCH-05 |
| Multi-Mode Comparison | 4 | MODE-01 to MODE-04 |
| Database-Level Hardening | 4 | DB-01 to DB-04 |

**Total v1 requirements:** 13

---

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| SCH-01 | Phase 5 | Pending |
| SCH-02 | Phase 5 | Pending |
| SCH-03 | Phase 5 | Pending |
| SCH-04 | Phase 5 | Pending |
| SCH-05 | Phase 5 | Pending |
| MODE-01 | Phase 6 | Pending |
| MODE-02 | Phase 6 | Pending |
| MODE-03 | Phase 6 | Pending |
| MODE-04 | Phase 6 | Pending |
| DB-01 | Phase 7 | Pending |
| DB-02 | Phase 7 | Pending |
| DB-03 | Phase 7 | Pending |
| DB-04 | Phase 7 | Pending |

**Coverage:** 13/13 requirements mapped (100%)
