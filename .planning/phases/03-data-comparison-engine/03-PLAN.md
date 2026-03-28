---
phase: 03-data-comparison-engine
plan: 03
type: execute
wave: 3
depends_on: ["02-PLAN"]
files_modified:
  - frontend/src/components/DataDiffViewer.tsx
  - frontend/src/components/SummaryPanel.tsx
  - frontend/src/components/DrillDownTable.tsx
  - frontend/src/hooks/useDataComparison.ts
  - frontend/src/types/data_compare.ts
autonomous: true
requirements:
  - UI-DATA-01
  - UI-DATA-02
  - UI-DATA-03
  - UI-DATA-04

must_haves:
  truths:
    - "DataDiffViewer component renders comparison results"
    - "SummaryPanel displays row counts and diff statistics"
    - "DrillDownTable shows差异 rows with highlighted fields"
    - "useDataComparison hook provides compareData function"
  artifacts:
    - path: frontend/src/components/DataDiffViewer.tsx
      provides: Main data diff viewer component
      contains: "export function DataDiffViewer"
    - path: frontend/src/hooks/useDataComparison.ts
      provides: Data comparison React hook
      contains: "export function useDataComparison"
  key_links:
    - from: frontend/src/components/DataDiffViewer.tsx
      to: frontend/src/hooks/useDataComparison.ts
      via: "Uses useDataComparison hook"
      pattern: "import { useDataComparison } from './useDataComparison'"
---

<objective>
Create UI components for displaying data comparison results with summary and drill-down capabilities.

Purpose: Provide users with clear visualization of data differences, including summary statistics and detailed差异 rows.
Output: DataDiffViewer component, SummaryPanel, DrillDownTable, and useDataComparison hook.
</objective>

<execution_context>
@~/.claude/get-shit-done/workflows/execute-plan.md
@~/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/PROJECT.md
@.planning/ROADMAP.md
@.planning/phases/03-data-comparison-engine/CONTEXT.md
@.planning/phases/03-data-comparison-engine/02-PLAN.md
@frontend/src/components/SchemaDiffViewer.tsx (reference for diff viewer pattern)
@frontend/src/hooks/useComparison.ts (reference for hook pattern)
</context>

<tasks>

<task type="auto" tdd="false">
  <name>Task 1: Create TypeScript types for data comparison</name>
  <files>frontend/src/types/data_compare.ts</files>
  <read_first>
    - frontend/src/types/index.ts (existing types)
    - backend/app/schemas/api.py (API schemas from Wave 2)
  </read_first>
  <action>
    Create frontend/src/types/data_compare.ts:

    1. DataCompareRequest:
       - source_connection_id: number
       - target_connection_id: number
       - source_table: string
       - target_table: string
       - mode?: 'auto' | 'full' | 'hash' | 'sample'
       - threshold?: number
       - sample_size?: number
       - batch_size?: number

    2. FieldDiff:
       - field_name: string
       - source_value: unknown | null
       - target_value: unknown | null
       - difference_type: string

    3. RowDiff:
       - primary_key_value: unknown
       - diff_type: 'added' | 'removed' | 'modified'
       - field_diffs: FieldDiff[]

    4. DataSummary:
       - source_row_count: number
       - target_row_count: number
       - diff_count: number
       - diff_percentage: number
       - mode_used: string
       - hash_source?: string
       - hash_target?: string
       - sampled_row_count?: number

    5. DataCompareResponse:
       - summary: DataSummary
       - diffs: RowDiff[]
       - has_more: boolean
       - truncated: boolean

    6. Export types from frontend/src/types/index.ts
  </action>
  <acceptance_criteria>
    - frontend/src/types/data_compare.ts exists
    - All types match backend API schemas
    - Types exported from frontend/src/types/index.ts
    - TypeScript compilation succeeds
  </acceptance_criteria>
  <verify>
    <automated>grep -E "export (interface|type) (DataCompare|FieldDiff|RowDiff|DataSummary)" frontend/src/types/data_compare.ts</automated>
  </verify>
  <done>TypeScript types for data comparison created</done>
</task>

<task type="auto" tdd="false">
  <name>Task 2: Create useDataComparison hook</name>
  <files>frontend/src/hooks/useDataComparison.ts</files>
  <read_first>
    - frontend/src/hooks/useComparison.ts (reference pattern)
    - frontend/src/api/client.ts (API client)
    - frontend/src/types/data_compare.ts (types from Task 1)
  </read_first>
  <action>
    Create frontend/src/hooks/useDataComparison.ts:

    1. Import dependencies:
       - useMutation from @tanstack/react-query
       - apiClient
       - DataCompareRequest, DataCompareResponse types

    2. Create compareData mutation:
       - POST to /api/compare/data
       - Accept DataCompareRequest
       - Return DataCompareResponse

    3. Create hook return object:
       - compareData: mutation function
       - isComparing: isPending status
       - comparisonResult: data from mutation
       - error: error from mutation
       - resetComparison: reset function

    4. Export useDataComparison function
  </action>
  <acceptance_criteria>
    - frontend/src/hooks/useDataComparison.ts exists
    - Uses useMutation for API calls
    - compareData function posts to correct endpoint
    - Returns comparison state and result
    - TypeScript types correct
  </acceptance_criteria>
  <verify>
    <automated>grep -E "export function useDataComparison|compareData" frontend/src/hooks/useDataComparison.ts</automated>
  </verify>
  <done>Data comparison hook created for API integration</done>
</task>

<task type="auto" tdd="false">
  <name>Task 3: Create SummaryPanel component</name>
  <files>frontend/src/components/SummaryPanel.tsx</files>
  <read_first>
    - frontend/src/components/SchemaDiffViewer.tsx (reference styling)
    - frontend/src/types/data_compare.ts
  </read_first>
  <action>
    Create frontend/src/components/SummaryPanel.tsx:

    1. Props interface:
       - summary: DataSummary
       - sourceTable: string
       - targetTable: string
       - sourceDbType?: string
       - targetDbType?: string

    2. Component structure:
       - Card/Panel container
       - Table names header
       - Statistics grid:
         - Source row count
         - Target row count
         - Difference count
         - Difference percentage (with color coding)
       - Mode badge (show comparison mode used)
       - Optional: hash values if hash mode used

    3. Styling:
       - Use Ant Design Card, Statistic, Grid components
       - Color-code diff percentage:
         - Green: 0% (no differences)
         - Yellow: <1%
         - Orange: 1-5%
         - Red: >5%

    4. Export SummaryPanel component
  </action>
  <acceptance_criteria>
    - frontend/src/components/SummaryPanel.tsx exists
    - Displays all summary statistics
    - Color-coded diff percentage
    - Shows comparison mode used
    - Uses Ant Design components
    - TypeScript types correct
  </acceptance_criteria>
  <verify>
    <automated>grep -E "export.*SummaryPanel|DataSummary" frontend/src/components/SummaryPanel.tsx</automated>
  </verify>
  <done>SummaryPanel component created for displaying comparison statistics</done>
</task>

<task type="auto" tdd="false">
  <name>Task 4: Create DrillDownTable component for差异 rows</name>
  <files>frontend/src/components/DrillDownTable.tsx</files>
  <read_first>
    - frontend/src/components/SummaryPanel.tsx (Task 3 output)
    - frontend/src/types/data_compare.ts
  </read_first>
  <action>
    Create frontend/src/components/DrillDownTable.tsx:

    1. Props interface:
       - diffs: RowDiff[]
       - columns: string[] (field names)
       - hasMore: boolean
       - onExpand?: (row: RowDiff) => void

    2. Component structure:
       - Ant Design Table component
       - Columns:
         - Primary key value
         - Diff type badge (added/removed/modified)
         - Expandable row for field-level diffs
       - Pagination for large result sets

    3. Field diff display (expanded row):
       - Table showing each different field
       - Columns: Field Name, Source Value, Target Value
       - Highlight different values:
         - Source: light red background
         - Target: light green background
       - NULL values displayed as "NULL" with distinct styling

    4. Features:
       - Row selection
       - Sortable columns
       - Expandable row details
       - "Load more" if hasMore=true

    5. Export DrillDownTable component
  </action>
  <acceptance_criteria>
    - frontend/src/components/DrillDownTable.tsx exists
    - Displays RowDiff data in table
    - Expandable rows show field-level diffs
    - Diff type badges (added/removed/modified)
    - Value highlighting for differences
    - NULL values displayed clearly
    - Pagination supported
  </acceptance_criteria>
  <verify>
    <automated>grep -E "export.*DrillDownTable|RowDiff" frontend/src/components/DrillDownTable.tsx</automated>
  </verify>
  <done>DrillDownTable component created for displaying差异 row details</done>
</task>

<task type="auto" tdd="false">
  <name>Task 5: Create DataDiffViewer main component</name>
  <files>frontend/src/components/DataDiffViewer.tsx</files>
  <read_first>
    - frontend/src/components/SummaryPanel.tsx
    - frontend/src/components/DrillDownTable.tsx
    - frontend/src/hooks/useDataComparison.ts
  </read_first>
  <action>
    Create frontend/src/components/DataDiffViewer.tsx:

    1. Props interface:
       - sourceConnectionId: number
       - targetConnectionId: number
       - sourceTable: string
       - targetTable: string
       - onComplete?: () => void

    2. Component state:
       - Comparison mode selection (auto/full/hash/sample)
       - Threshold override (optional)
       - Loading state

    3. Component structure:
       - Configuration section:
         - Mode selector (Radio.Group or Select)
         - Advanced options (threshold, sample size)
         - "Compare" button
       - Loading state with progress indicator
       - Results section (when comparison complete):
         - SummaryPanel
         - DrillDownTable

    4. Integration:
       - Use useDataComparison hook
       - Handle comparison errors
       - Display error messages

    5. Export DataDiffViewer component
  </action>
  <acceptance_criteria>
    - frontend/src/components/DataDiffViewer.tsx exists
    - Integrates SummaryPanel and DrillDownTable
    - Mode selector for comparison modes
    - Compare button triggers comparison
    - Displays loading state
    - Handles and displays errors
    - Uses useDataComparison hook
  </acceptance_criteria>
  <verify>
    <automated>grep -E "export.*DataDiffViewer|useDataComparison" frontend/src/components/DataDiffViewer.tsx</automated>
  </verify>
  <done>DataDiffViewer main component created integrating all sub-components</done>
</task>

</tasks>

<verification>
- TypeScript types compile without errors
- useDataComparison hook calls correct API endpoint
- SummaryPanel displays all statistics correctly
- DrillDownTable renders差异 rows with proper highlighting
- DataDiffViewer integrates all components
- NULL values displayed consistently
- Diff type badges render correctly
- Color coding appropriate for diff percentage
</verification>

<success_criteria>
- frontend/src/types/data_compare.ts exports all required types
- frontend/src/hooks/useDataComparison.ts provides comparison functionality
- frontend/src/components/SummaryPanel.tsx renders statistics
- frontend/src/components/DrillDownTable.tsx displays差异 details
- frontend/src/components/DataDiffViewer.tsx integrates components
- UI matches design expectations from CONTEXT.md
</success_criteria>

<output>
After completion, create `.planning/phases/03-data-comparison-engine/03-data-comparison-engine-03-SUMMARY.md` with:
- Component hierarchy and data flow
- Hook implementation details
- Styling decisions
- Edge cases handled (NULL display, large result sets)
</output>
