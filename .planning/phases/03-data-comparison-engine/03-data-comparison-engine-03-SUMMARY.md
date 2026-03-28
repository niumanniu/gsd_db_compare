# Phase 3 Wave 3: UI Components for Data Comparison - Summary

**Completed:** 2026-03-28  
**Wave:** 3 (UI Components)  
**Depends on:** Wave 2 (API schemas)

---

## Component Hierarchy

```
DataDiffViewer (main container)
├── Configuration Section
│   ├── Mode Selector (Radio.Group)
│   ├── Threshold Selector (Select)
│   ├── Sample Size Selector (Select)
│   └── Action Buttons (Compare, Reset)
├── Loading State (Spin)
├── Error State (Alert)
└── Results Section
    ├── SummaryPanel
    │   ├── Table names header
    │   ├── Statistics Grid (4 columns)
    │   │   ├── Source Row Count
    │   │   ├── Target Row Count
    │   │   ├── Difference Count
    │   │   └── Diff Percentage
    │   └── Additional Info (hash values, sampled rows)
    └── DrillDownTable
        ├── Main Table (row-level diffs)
        └── Expanded Rows (field-level diffs)
```

---

## Data Flow

```
User clicks "Compare Data"
    ↓
DataDiffViewer.handleCompare()
    ↓
useDataComparison.compareData(requestData)
    ↓
POST /api/compare/data
    ↓
Backend returns DataCompareResponse
    ↓
comparisonResult updated in hook
    ↓
SummaryPanel + DrillDownTable render results
```

---

## Hook Implementation Details

### useDataComparison (`frontend/src/hooks/useDataComparison.ts`)

Built with `@tanstack/react-query` useMutation:

| Property | Type | Description |
|----------|------|-------------|
| `compareData` | `(data: DataCompareRequest) => Promise` | Mutation function |
| `isComparing` | `boolean` | Pending state |
| `comparisonResult` | `DataCompareResponse | null` | Last result |
| `error` | `Error | null` | Error state |
| `resetComparison` | `() => void` | Reset state |

**Endpoint:** `POST /api/compare/data`

---

## TypeScript Types (`frontend/src/types/data_compare.ts`)

```
DataCompareRequest
├── source_connection_id: number
├── target_connection_id: number
├── source_table: string
├── target_table: string
├── mode?: 'auto' | 'full' | 'hash' | 'sample'
├── threshold?: number
├── batch_size?: number
└── sample_size?: number

FieldDiff
├── field_name: string
├── source_value: unknown | null
├── target_value: unknown | null
└── diff_type: 'value' | 'null' | 'type' | 'length'

RowDiff
├── primary_key: unknown
├── diff_type: 'missing_in_target' | 'missing_in_source' | 'content_diff'
├── field_diffs: FieldDiff[]
├── source_row: Record<string, unknown> | null
└── target_row: Record<string, unknown> | null

DataSummary
├── source_table: string
├── target_table: string
├── source_row_count: number
├── target_row_count: number
├── diff_count: number
├── diff_percentage: number | null
├── mode_used: 'full' | 'hash' | 'sample' | 'hash+sample'
├── has_more: boolean
├── source_hash?: string
├── target_hash?: string
└── sampled_row_count?: number

DataCompareResponse
├── summary: DataSummary
└── diffs: RowDiff[]
```

---

## Styling Decisions

### Color Coding (SummaryPanel)

**Diff Percentage:**
| Percentage | Color | Hex |
|------------|-------|-----|
| 0% | Green | #52c41a |
| < 1% | Yellow | #faad14 |
| 1-5% | Orange | #fa8c16 |
| > 5% | Red | #ff4d4f |

**Diff Count:**
| Count | Color | Hex |
|-------|-------|-----|
| 0 | Green | #52c41a |
| < 100 | Yellow | #faad14 |
| < 1000 | Orange | #fa8c16 |
| ≥ 1000 | Red | #ff4d4f |

### Diff Type Badges (DrillDownTable)

| Diff Type | Color | Icon | Label |
|-----------|-------|------|-------|
| missing_in_target | Red | CloseCircleOutlined | MISSING IN TARGET |
| missing_in_source | Green | CheckCircleOutlined | MISSING IN SOURCE |
| content_diff | Gold | DiffOutlined | MODIFIED |

### Value Highlighting (Field Diffs)

| Condition | Background |
|-----------|------------|
| NULL difference | #fff1b8 (yellow tint) |
| Source value | #fff2f0 (red tint) |
| Target value | #f6ffed (green tint) |

---

## Edge Cases Handled

### NULL Value Display
- NULL values shown as "NULL" text with secondary color
- NULL vs non-NULL highlighted with yellow background
- Both NULL treated as equal (no diff shown)

### Large Result Sets
- Pagination: 10 rows per page default
- Size changer: 10/20/50/100 per page
- Total count display
- `has_more` flag for additional results

### Hash Mode Display
- Hash values truncated to 16 chars with ellipsis
- "Hashes Match" badge when identical
- Hash section only shown when available

### Sample Mode Display
- Sampled row count displayed
- "Load More" button when has_more=true
- Diff percentage calculated from sample

### Empty States
- "No comparison results yet" before first run
- "No differences found" when data identical
- Error alert with message on failure

---

## Files Created/Modified

| File | Purpose |
|------|---------|
| `frontend/src/types/data_compare.ts` | TypeScript type definitions |
| `frontend/src/types/index.ts` | Re-exports data compare types |
| `frontend/src/hooks/useDataComparison.ts` | React hook for API integration |
| `frontend/src/components/SummaryPanel.tsx` | Statistics display component |
| `frontend/src/components/DrillDownTable.tsx` | Row/field diff table component |
| `frontend/src/components/DataDiffViewer.tsx` | Main viewer component |

---

## Integration Notes

1. **Component Usage:**
   ```tsx
   <DataDiffViewer
     sourceConnectionId={1}
     targetConnectionId={2}
     sourceTable="users"
     targetTable="users_backup"
     onComplete={() => console.log('Done')}
   />
   ```

2. **Direct Hook Usage:**
   ```tsx
   const { compareData, isComparing, comparisonResult } = useDataComparison();
   
   await compareData({
     source_connection_id: 1,
     target_connection_id: 2,
     source_table: 'users',
     target_table: 'users_backup',
     mode: 'auto',
   });
   ```

3. **Ant Design Dependencies:**
   - Card, Statistic, Row, Col, Tag, Typography
   - Table, Button, Select, Radio, Space, Divider
   - Alert, Empty, Spin
   - Icons from @ant-design/icons

---

## Testing Recommendations

1. **Unit Tests:**
   - SummaryPanel percentage formatting
   - DrillDownTable diff type badges
   - useDataComparison hook state management

2. **Integration Tests:**
   - DataDiffViewer full workflow
   - Error handling display
   - Loading state transitions

3. **E2E Tests:**
   - Compare with different modes
   - Verify results display correctly
   - Test pagination and expandable rows

---

## Next Steps (Wave 4)

- [ ] Integrate DataDiffViewer into main comparison page
- [ ] Add export/download functionality
- [ ] Implement real-time progress updates
- [ ] Add comparison history tracking
