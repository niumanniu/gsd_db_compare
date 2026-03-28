# Roadmap: DB Compare

**Milestone:** v1.1 完善比对功能
**Granularity:** Standard (default)
**Phases:** 3

---

## Milestones

- ✅ **v1.0 MVP** — Phases 1-4 (shipped 2026-03-28)
- 📋 **v1.1** — Phases 5-7 (planned)

---

## Phases

<details>
<summary>✅ v1.0 MVP (Phases 1-4) — SHIPPED 2026-03-28</summary>

- [x] Phase 1: Foundation (7/7 plans) — completed 2026-03-28
- [x] Phase 2: Multi-Database Support (4/4 plans) — completed 2026-03-28
- [x] Phase 3: Data Comparison Engine (4/4 plans) — completed 2026-03-28
- [x] Phase 4: Advanced Features (4/4 plans) — completed 2026-03-28

**Archive:** See `.planning/milestones/v1.0-ROADMAP.md` for full milestone details.

</details>

### v1.1 (Planned)

- [ ] **Phase 5: Schema Selection** - Backend schema enumeration + frontend dropdown for database-level comparison
- [ ] **Phase 6: Multi-Mode Comparison** - Mode switcher polish + multi-select table UI + atomic state management
- [ ] **Phase 7: Database Hardening** - Exclude pattern filtering + table count safeguards + comparison preview

---

## Phase Details

### Phase 5: Schema Selection
**Goal:** Users can select specific schemas when running database-level comparisons
**Depends on:** Phase 4 (v1.0 foundation - comparison engine, API, UI)
**Requirements:** SCH-01, SCH-02, SCH-03, SCH-04, SCH-05
**Success Criteria** (what must be TRUE):
  1. User in database-level mode sees schema dropdowns for source and target
  2. Schema dropdown lists only schemas from the selected connection
  3. User can type to search/filter schemas in dropdown
  4. Backend returns schemas via GET /api/connections/{id}/schemas
**Plans:** TBD
**UI hint:** yes

### Phase 6: Multi-Mode Comparison
**Goal:** Users can switch between comparison modes without state confusion and see clear selection feedback
**Depends on:** Phase 4 (v1.0 foundation - mode switcher exists)
**Requirements:** MODE-01, MODE-02, MODE-03, MODE-04
**Success Criteria** (what must be TRUE):
  1. Mode switcher clearly displays Single/Multi/Database as distinct options
  2. When user switches modes, previous table/schema selections are cleared
  3. Multi-table mode displays count of selected tables (e.g., "3 tables selected")
  4. Tables with matching names across connections show visual auto-match indicator
**Plans:** TBD
**UI hint:** yes

### Phase 7: Database Hardening
**Goal:** Users can filter out system tables and see comparison scope before running
**Depends on:** Phase 5 (schema selection working)
**Requirements:** DB-01, DB-02, DB-03, DB-04
**Success Criteria** (what must be TRUE):
  1. User can add exclude patterns like sys_* or *_log to filter tables
  2. UI shows count of tables matching current exclude patterns as user types
  3. Before running comparison, user sees total table count that will be compared
  4. Warning banner appears when comparison includes 200+ tables
**Plans:** TBD
**UI hint:** yes

---

## Progress

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 1. Foundation | v1.0 | 7/7 | Complete | 2026-03-28 |
| 2. Multi-Database Support | v1.0 | 4/4 | Complete | 2026-03-28 |
| 3. Data Comparison Engine | v1.0 | 4/4 | Complete | 2026-03-28 |
| 4. Advanced Features | v1.0 | 4/4 | Complete | 2026-03-28 |
| 5. Schema Selection | v1.1 | 0/0 | Not started | - |
| 6. Multi-Mode Comparison | v1.1 | 0/0 | Not started | - |
| 7. Database Hardening | v1.1 | 0/0 | Not started | - |

---

## Coverage

**Total v1.1 requirements:** 13
**Mapped:** 13/13 (100%)

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

---

*Last updated: 2026-03-29 after v1.0 milestone completion, v1.1 roadmap created*
