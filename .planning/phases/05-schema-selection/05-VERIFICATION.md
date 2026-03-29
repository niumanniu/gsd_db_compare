---
phase: 05-schema-selection
verified_by: inline
verified_at: 2026-03-29
status: passed
---

# Phase 5 Verification: Schema Selection

## Phase Goal

Users can select specific schemas when running database-level comparisons.

## Must-Have Requirements Verification

### SCH-01: Source schema dropdown visible in database mode ✓
**Evidence:** `frontend/src/components/TableBrowser.tsx:242-256`
- Schema dropdown renders when `compareMode === 'database'`
- Labeled "Source Schema (Database)"
- Bound to `sourceSchema` state

### SCH-02: Target schema dropdown visible in database mode ✓
**Evidence:** `frontend/src/components/TableBrowser.tsx:257-271`
- Schema dropdown renders when `compareMode === 'database'`
- Labeled "Target Schema (User)"
- Bound to `targetSchema` state

### SCH-03: Dropdowns show only schemas from selected connection ✓
**Evidence:** `frontend/src/App.tsx:83-99`
- `useQuery` hooks fetch schemas from `/api/connections/{id}/schemas`
- Query enabled only when connection ID is set (`enabled: !!sourceConnectionId`)
- Each dropdown receives schemas from its respective connection

### SCH-04: Dropdown search/filter works ✓
**Evidence:** `frontend/src/components/TableBrowser.tsx:245-246, 264-265`
- `showSearch` prop enables search input
- `optionFilterProp="children"` filters by displayed schema name

### SCH-05: Backend API endpoint returns schemas ✓
**Evidence:**
- Backend: `backend/app/api/connections.py:187-220` - GET /api/connections/{conn_id}/schemas endpoint
- MySQL adapter: `backend/app/adapters/mysql.py:109-127` - queries information_schema.SCHEMATA
- Oracle adapter: `backend/app/adapters/oracle.py:120-143` - queries ALL_USERS

## Artifacts Created

### Backend Files Modified
| File | Change |
|------|--------|
| `backend/app/adapters/base.py` | Added abstract `get_schemas()` method |
| `backend/app/adapters/mysql.py` | Implemented schema enumeration |
| `backend/app/adapters/oracle.py` | Implemented schema enumeration |
| `backend/app/schemas/api.py` | Added SchemaInfo response model |
| `backend/app/api/connections.py` | Added GET /schemas endpoint |

### Frontend Files Modified
| File | Change |
|------|--------|
| `frontend/src/types/index.ts` | Added SchemaInfo interface |
| `frontend/src/hooks/useConnections.ts` | Added getSchemas mutation |
| `frontend/src/components/TableBrowser.tsx` | Added schema dropdown UI |
| `frontend/src/App.tsx` | Added schema state management |

## Build Verification

- Backend imports verified: `python -c "from app.adapters.base import DatabaseAdapter..."` ✓
- Frontend build: `npm run build` completed successfully ✓
- No TypeScript errors ✓

## Phase Complete

All 5 SCH requirements implemented and verified.

**Plans completed:** 2/2
- 05-01: Backend schema enumeration API ✓
- 05-02: Frontend schema dropdown UI ✓
