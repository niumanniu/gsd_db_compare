# Feature Landscape: Schema Selection & Multi-Mode Comparison

**Domain:** Database Comparison Tools
**Researched:** 2026-03-29
**Confidence:** MEDIUM (based on industry patterns from Redgate SQL Compare, dbForge Studio, and standard UX patterns for database tools)

---

## Executive Summary

Schema selection and multi-mode comparison are standard features in mature database comparison tools. The expected patterns are:

1. **Schema Selection:** Dropdown-based selection (single-select or multi-select) with search/filter capabilities, plus exclude patterns with wildcard support for database-level comparisons
2. **Comparison Modes:** Three distinct modes—Single Table (one-to-one), Multi-Table (batch selected tables), and Database-Level (all schemas with exclusions)—each with progressively broader scope and different UI behaviors
3. **Auto-Matching:** Tables with identical names auto-match; users can manually map tables with different names
4. **Progressive Disclosure:** UI complexity increases with mode scope—simple dropdowns for single mode, checkbox tables for multi-mode, pattern-based filtering for database-level

---

## Table Stakes (Users Expect These)

Features users assume exist in any database comparison tool. Missing these = product feels incomplete or amateur.

| Feature | Why Expected | Complexity | Implementation Notes |
|---------|--------------|------------|---------------------|
| **Schema Dropdown Selection** | Users need to select which schemas/databases to compare | LOW | Standard Ant Design Select component with search |
| **Table Selection (Single)** | Compare one specific table between environments | LOW | Single-select dropdown, filtered by schema |
| **Table Selection (Multi)** | Batch compare multiple tables at once | MEDIUM | Multi-select dropdown or checkbox table |
| **Mode Switcher** | Switch between single/multi/database comparison modes | LOW | Tag buttons or radio group (already implemented in TableBrowser.tsx) |
| **Auto-Match Same-Name Tables** | Tables with identical names should auto-pair | MEDIUM | Simple string matching on table_name field |
| **Exclude Patterns (Wildcards)** | Exclude system tables like `sys_*`, `*_log`, `temp_*` | MEDIUM | Pattern input with wildcard-to-regex conversion |
| **Connection Prerequisite** | Must select connections before tables appear | LOW | Disable table selects until connections chosen |
| **Loading State** | Show loading while fetching table lists | LOW | Standard loading spinner on table dropdowns |
| **Table Count Display** | Show row counts in dropdown for context | LOW | Display `table_name (row_count rows)` format |

---

## Differentiators (Competitive Advantage)

Features that set the product apart. Not required, but valuable for user experience.

| Feature | Value Proposition | Complexity | Implementation Notes |
|---------|-------------------|------------|---------------------|
| **Schema-Level Dropdown for Database Mode** | Let users select specific schemas to compare, not just "all" | MEDIUM | Add schema multi-select above table selection in database mode |
| **Smart Table Mapping UI** | Visual interface to manually map tables with different names | HIGH | Drag-drop or dual-listbox for A→B table mapping |
| **Recent Tables Quick-Select** | Quickly re-compare recently compared tables | LOW | Store last 5-10 table pairs in localStorage |
| **Comparison Preview Count** | Show "X tables will be compared" before running | LOW | Count matched tables dynamically as selection changes |
| **Exclude Pattern Presets** | Common patterns like "System Tables", "Temp Tables", "Audit Logs" | LOW | Predefined pattern groups users can toggle |
| **Table Dependency Order** | Compare tables in foreign key dependency order | HIGH | Fetch FK graph, topologically sort before comparison |
| **Progressive Results Loading** | Show results table-by-table as they complete | MEDIUM | Streaming results for multi-table compare |

---

## Anti-Features (Commonly Requested, Often Problematic)

Features that seem good but create problems.

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| **Select All Tables (No Filtering)** | Users want to compare everything quickly | Database-level compare already does this; "select all" in multi-mode creates performance issues | Use Database Mode for full comparison; keep Multi-Table for curated selections |
| **Manual Table Pairing for Database Mode** | Users want to map tables differently per comparison | Database mode should be "dumb bulk compare"; manual pairing belongs in Multi-Table mode | Add manual mapping feature to Multi-Table mode instead |
| **Real-Time Table List Refresh** | Users want to see newly created tables immediately | Adds complexity; users can manually refresh connection | Add explicit "Refresh Tables" button instead of auto-refresh |
| **Cross-Schema Table Comparison** | Compare `schema1.tableA` vs `schema2.tableB` | Adds schema selection complexity to table-level comparison | Handle via Database mode with schema filter, not in Single/Multi mode |
| **Save Table Selection Groups** | Save commonly compared table sets | Premature optimization for v1.1; add after validating usage patterns | Track recent selections first; add save groups if users request |

---

## Feature Dependencies

```
[Schema Selection Dropdown]
    └──requires──> [Connection Selection]
                        └──requires──> [Connection Management (existing)]

[Table Selection (Single/Multi)]
    └──requires──> [Connection Selection]
    └──requires──> [Table List Discovery (existing)]

[Database-Level Comparison]
    └──requires──> [Connection Selection]
    └──requires──> [Schema Discovery]
    └──requires──> [Exclude Pattern Filtering]

[Multi-Table Batch Compare]
    └──requires──> [Table Selection (Multi)]
    └──requires──> [Auto-Match Logic]
    └──enhances──> [Single Table Compare]

[Auto-Match Tables]
    └──requires──> [Table List Discovery]
    └──enhances──> [Multi-Table Selection]

[Exclude Pattern Filtering]
    └──requires──> [Table List Discovery]
    └──used_by──> [Database-Level Comparison]
```

### Dependency Notes

- **Schema Selection requires Connection Selection:** Can't show schemas until a connection is chosen
- **Auto-Match enhances Multi-Table:** Auto-matching is only relevant when selecting multiple tables
- **Exclude Patterns used by Database Mode:** Pattern filtering is specifically for database-level bulk comparison
- **Table Discovery is foundational:** All comparison modes depend on existing table list fetching

---

## MVP Definition for v1.1

### Launch With (v1.1)

Minimum viable for the schema selection and multi-mode milestone.

- [ ] **Schema Dropdown for Database Mode** — Essential for selecting which schemas to compare at database level
- [ ] **Mode Switcher (Single/Multi/Database)** — Already implemented in TableBrowser.tsx; verify UX is clear
- [ ] **Multi-Select Table UI** — Checkbox-based selection for multi-table mode
- [ ] **Exclude Pattern Input** — Wildcard support for filtering tables in database mode
- [ ] **Auto-Match Display** — Show count of auto-matched tables in batch compare button
- [ ] **Connection Prerequisite Enforcement** — Disable table selection until connections chosen

### Add After Validation (v1.x)

Features to add once core is working and usage patterns are understood.

- [ ] **Schema-Level Selection for Multi-Table Mode** — Add schema filter dropdown above table list
- [ ] **Recent Tables Quick-Select** — Add "Recent" tab or dropdown section
- [ ] **Exclude Pattern Presets** — Add checkbox presets for common patterns
- [ ] **Comparison Preview Count** — Dynamic count display before running comparison

### Future Consideration (v2+)

Features to defer until product-market fit is established.

- [ ] **Manual Table Mapping UI** — Complex; only needed if users frequently compare differently-named tables
- [ ] **Table Dependency Ordering** — Advanced feature for complex schemas
- [ ] **Save Table Selection Groups** — Only valuable if users repeatedly compare same table sets
- [ ] **Progressive Results Loading** — Performance optimization for very large batch comparisons

---

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority |
|---------|------------|---------------------|----------|
| Schema Dropdown (Database Mode) | HIGH | LOW | P1 |
| Mode Switcher (Single/Multi/Database) | HIGH | LOW (done) | P1 |
| Multi-Select Table UI | HIGH | LOW | P1 |
| Exclude Pattern Filtering | HIGH | MEDIUM | P1 |
| Auto-Match Display | MEDIUM | LOW | P2 |
| Connection Prerequisite Enforcement | MEDIUM | LOW | P2 |
| Schema-Level Selection (Multi-Table) | MEDIUM | MEDIUM | P2 |
| Recent Tables Quick-Select | LOW | LOW | P3 |
| Exclude Pattern Presets | LOW | LOW | P3 |
| Manual Table Mapping UI | MEDIUM | HIGH | P3 |
| Table Dependency Ordering | LOW | HIGH | P4 |

**Priority key:**
- P1: Must have for v1.1 launch
- P2: Should have, add in v1.1 minor releases
- P3: Nice to have, future consideration
- P4: Defer to v2+

---

## User Interaction Patterns by Mode

### Single Table Mode
```
1. Select Source Connection → Load source tables
2. Select Target Connection → Load target tables
3. Select Source Table (dropdown)
4. Select Target Table (dropdown)
5. Click "Compare Schemas"
```

**UI Behavior:**
- Two single-select dropdowns for tables
- Each dropdown filters its own connection's tables
- Button enabled only when both tables selected

### Multi-Table Mode
```
1. Select Source Connection → Load source tables
2. Select Target Connection → Load target tables
3. Select multiple Source Tables (checkboxes or multi-select)
4. Select multiple Target Tables (checkboxes or multi-select)
5. System auto-matches same-name tables
6. Click "Batch Compare (X matched tables)"
```

**UI Behavior:**
- Two multi-select dropdowns or checkbox tables
- Auto-match count displayed on button
- Matched pairs: tables with identical names
- Unmatched tables: compared as "exists in A only" or "exists in B only"

### Database-Level Mode
```
1. Select Source Connection → Load source schemas
2. Select Target Connection → Load target schemas
3. (Optional) Select specific schemas to compare (multi-select dropdown)
4. Enter exclude patterns (wildcards like `sys_*`, `*_temp`)
5. Click "Compare Databases"
```

**UI Behavior:**
- No individual table selection (compares all)
- Schema dropdown appears only in this mode
- Exclude pattern input with tag-based display
- Pattern supports `*` (any chars) and `?` (single char) wildcards

---

## Edge Cases to Handle

| Edge Case | User Impact | Handling Strategy |
|-----------|-------------|-------------------|
| **No Matching Tables** | User selects tables but none have same names | Show warning: "No tables with matching names found. Tables will be compared as 'exists in one side only'." |
| **Table Name Exists in Both but Different Schema** | `dbo.users` vs `sales.users` | In Single/Multi mode, compare by table name only. In Database mode, include schema prefix in display |
| **Very Large Table Lists (>500 tables)** | Dropdown becomes unusable | Add search/filter to dropdown; consider virtual scrolling for checkbox tables |
| **Connection Lost Mid-Selection** | Tables selected but connection dies | Re-fetch tables on compare; show error if connection unavailable |
| **Exclude Pattern Matches All Tables** | User accidentally excludes everything | Show warning: "All tables excluded by current patterns" |
| **Case Sensitivity Mismatch** | `Users` vs `users` treated as different | Normalize table names to lowercase for matching; preserve original case for display |
| **Special Characters in Table Names** | `user*log`, `temp?table` | Escape special chars in exclude pattern matching; use exact match for table selection |
| **One Side Has No Tables** | Connection valid but empty database | Show Empty state: "No tables found in [database]" with refresh option |

---

## Competitor Feature Analysis

| Feature | Redgate SQL Compare | dbForge Studio | Our Approach (v1.1) |
|---------|---------------------|----------------|---------------------|
| Schema Selection | Tree view with checkboxes | Dropdown multi-select | Dropdown multi-select (Database mode) |
| Table Selection | Tree view with checkboxes | List with filters | Multi-select dropdown + checkbox table |
| Exclude Patterns | Wizard with object filter | Regex-based filtering | Wildcard patterns (`*`, `?`) |
| Auto-Match | By object name | By object name | By table name (same-name matching) |
| Manual Mapping | Drag-drop in mapping tab | Dual-listbox | Not in v1.1 (future) |
| Mode Switching | Separate wizards | Tabbed interface | Tag buttons (single/multi/database) |

---

## Sources

- [Redgate SQL Compare Feature Overview](https://www.red-gate.com/products/sql-development/sql-compare/)
- [dbForge Studio Schema Comparison](https://www.devart.com/dbforge/studio/)
- Existing codebase analysis: `TableBrowser.tsx` (already implements mode switching)
- Industry patterns from database tool UX research (2024-2025)

---

*Feature research for: Schema Selection & Multi-Mode Comparison*
*Researched: 2026-03-29*
