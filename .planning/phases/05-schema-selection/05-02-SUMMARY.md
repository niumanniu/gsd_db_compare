---
phase: 05-schema-selection
plan: 02
status: completed
completed_at: 2026-03-29
---

# Plan 05-02 Summary: Frontend Schema Dropdown UI

## What Was Implemented

### 1. SchemaInfo TypeScript Type (`frontend/src/types/index.ts`)
- Added `SchemaInfo` interface after `TableInfo`
- Fields: `schema_name` (required), `charset`, `collation`, `account_status`, `created_time` (all optional)
- Matches backend Pydantic schema structure

### 2. getSchemas Mutation (`frontend/src/hooks/useConnections.ts`)
- Added `getSchemasMutation` using React Query
- Calls `GET /api/connections/${id}/schemas`
- Exposes `getSchemas` function and `isFetchingSchemas` loading state

### 3. TableBrowser Schema Dropdown Props (`frontend/src/components/TableBrowser.tsx`)
- Added props: `sourceSchema`, `targetSchema`, `onSourceSchemaChange`, `onTargetSchemaChange`, `sourceSchemas`, `targetSchemas`, `isFetchingSchemas`
- Added SchemaInfo type import
- Render schema dropdowns in database-level mode only
- Dropdowns positioned between connection selection and table/exclude patterns

### 4. Schema Selection State Management (`frontend/src/App.tsx`)
- Added `useState` for `sourceSchema` and `targetSchema`
- Added `useQuery` hooks with queryKey `['connection-schemas', id]`
- Fetches from `/api/connections/{id}/schemas` when connection changes
- Schema state resets when switching to single or multi mode
- Loading state combined: `isFetchingSchemas = loadingSourceSchemas || loadingTargetSchemas`

### 5. Search Functionality (Verification Task)
- Dropdowns use Ant Design `Select` with `showSearch` prop
- `optionFilterProp="children"` enables filtering by displayed schema name
- No code changes needed - verification confirmed implementation

## Dropdown UI Details

Schema dropdowns appear ONLY in `compareMode === 'database'`:
- Source Schema dropdown labeled "Source Schema (Database)"
- Target Schema dropdown labeled "Target Schema (User)"
- Both dropdowns disabled until connection selected
- Loading spinner shown while fetching schemas
- Search box appears when dropdown opens
- Typing filters options by schema_name

## Commits

1. `8bd5c61` - feat: add SchemaInfo TypeScript type
2. `f35ccc1` - feat: add getSchemas mutation to useConnections hook
3. `5bd5cea` - feat: add schema dropdown props and UI to TableBrowser
4. `da37874` - feat: add schema selection state and API calls in App.tsx

## Verification

- [x] All five tasks completed without TypeScript errors
- [x] Frontend builds successfully
- [x] SchemaInfo type defined with correct fields
- [x] useConnections hook exposes getSchemas and isFetchingSchemas
- [x] TableBrowser renders schema dropdowns in database mode
- [x] Dropdowns have `showSearch` and `optionFilterProp="children"`
- [x] App.tsx manages schema state with useQuery fetching
- [x] Schema state resets when switching modes

## Key Files Modified

| File | Change |
|------|--------|
| `frontend/src/types/index.ts` | Added SchemaInfo interface |
| `frontend/src/hooks/useConnections.ts` | Added getSchemas mutation |
| `frontend/src/components/TableBrowser.tsx` | Added schema dropdown props and UI |
| `frontend/src/App.tsx` | Added schema state and useQuery hooks |

## Integration with Backend

Frontend calls backend API endpoint `GET /api/connections/{id}/schemas` implemented in Plan 05-01.

Response format:
```json
[
  {"schema_name": "mydb", "charset": "utf8mb4", "collation": "...", "account_status": null, "created_time": "N/A"},
  {"schema_name": "USER1", "charset": null, "collation": null, "account_status": "OPEN", "created_time": "2024-01-01"}
]
```

## Requirements Satisfied

- SCH-01: Source schema dropdown visible in database mode
- SCH-02: Target schema dropdown visible in database mode
- SCH-03: Dropdowns show only schemas from selected connection (via API)
- SCH-04: Dropdown search/filter works for large schema lists
- SCH-05: Schema selection state resets when switching modes (via useEffect)

## Next Steps

Phase 5 complete. Both backend API and frontend UI are integrated and working.
