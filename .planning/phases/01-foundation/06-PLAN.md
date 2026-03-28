---
phase: 01-foundation
plan: 06
type: execute
wave: 3
depends_on: ["05-PLAN"]
files_modified:
  - frontend/src/components/SchemaDiffViewer.tsx
  - frontend/src/components/TableBrowser.tsx
  - frontend/src/hooks/useComparison.ts
autonomous: true
requirements:
  - SCHEMA-01
  - SCHEMA-03
user_setup: []

must_haves:
  truths:
    - "Table browser component exists for selecting tables"
    - "Schema diff viewer displays comparison results"
    - "Can initiate schema comparison from UI"
  artifacts:
    - path: frontend/src/components/SchemaDiffViewer.tsx
      provides: Schema diff visualization
      contains: "function SchemaDiffViewer"
    - path: frontend/src/components/TableBrowser.tsx
      provides: Table selection UI
      contains: "function TableBrowser"
  key_links:
    - from: frontend/src/components/SchemaDiffViewer.tsx
      to: frontend/src/hooks/useComparison.ts
      via: "useComparison hook"
      pattern: "useComparison"
---

<objective>
Create schema comparison UI with table browser and diff viewer.

Purpose: Enable users to select tables and view schema differences visually.
Output: Table browser, schema comparison trigger, side-by-side diff viewer.
</objective>

<execution_context>
@~/.claude/get-shit-done/workflows/execute-plan.md
@~/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/PROJECT.md
@.planning/ROADMAP.md
@.planning/phases/01-foundation/1-CONTEXT.md (D-10: UI Design Principles)
@.planning/phases/01-foundation/1-RESEARCH.md (React Patterns - Schema Diff Viewer)
</context>

<tasks>

<task type="auto" tdd="false">
  <name>Task 1: Create table browser component</name>
  <files>frontend/src/components/TableBrowser.tsx</files>
  <read_first>
    - .planning/phases/01-foundation/1-RESEARCH.md (React Patterns)
  </read_first>
  <action>
    Create frontend/src/components/TableBrowser.tsx:

    - Accept connection_id as prop
    - Fetch table list using API when connection changes
    - Display tables in searchable/selectable list
    - Support multi-select for source and target selection
    - Show basic table info (name, row count if available)
    - "Compare Selected" button to trigger comparison
  </action>
  <acceptance_criteria>
    - frontend/src/components/TableBrowser.tsx exists
    - Component accepts connection_id prop
    - Fetches and displays table list
    - Supports selecting source and target tables
    - Has compare button to trigger comparison
  </acceptance_criteria>
  <verify>
    <automated>grep "function TableBrowser" frontend/src/components/TableBrowser.tsx</automated>
  </verify>
  <done>Table browser component created</done>
</task>

<task type="auto" tdd="false">
  <name>Task 2: Create comparison hook</name>
  <files>frontend/src/hooks/useComparison.ts</files>
  <read_first>
    - frontend/src/hooks/useConnections.ts (pattern reference)
  </read_first>
  <action>
    Create frontend/src/hooks/useComparison.ts:

    ```typescript
    import { useMutation, useQuery } from '@tanstack/react-query';
    import apiClient from '../api/client';

    export function useComparison() {
      // Compare schemas mutation
      const compareMutation = useMutation({
        mutationFn: (data: {
          source_connection_id: number;
          source_table: string;
          target_connection_id: number;
          target_table: string;
        }) => apiClient.post('/api/compare/schema', data),
      });

      // Task polling (if async)
      const { data: taskResult } = useQuery({
        queryKey: ['task', taskId],
        queryFn: () => apiClient.get(`/api/tasks/${taskId}`).then(r => r.data),
        enabled: !!taskId && taskStatus !== 'completed',
        refetchInterval: 1000, // Poll every second
      });

      return {
        compareSchemas: compareMutation.mutateAsync,
        isComparing: compareMutation.isPending,
        comparisonResult: compareMutation.data?.data,
        error: compareMutation.error,
        taskResult, // For async tasks
      };
    }
    ```
  </action>
  <acceptance_criteria>
    - frontend/src/hooks/useComparison.ts exists
    - Hook provides compareSchemas function
    - Hook provides isComparing state
    - Hook provides comparisonResult data
    - Hook provides error handling
  </acceptance_criteria>
  <verify>
    <automated>grep "function useComparison" frontend/src/hooks/useComparison.ts</automated>
  </verify>
  <done>Comparison hook created</done>
</task>

<task type="auto" tdd="false">
  <name>Task 3: Create schema diff viewer component</name>
  <files>frontend/src/components/SchemaDiffViewer.tsx</files>
  <read_first>
    - .planning/phases/01-foundation/1-RESEARCH.md (React Patterns - Schema Diff Viewer)
    - .planning/phases/01-foundation/1-CONTEXT.md (D-10: UI Design Principles)
  </read_first>
  <action>
    Create frontend/src/components/SchemaDiffViewer.tsx:

    - Accept SchemaDiffResponse as prop
    - Use Ant Design Collapse for expandable sections
    - Sections: Columns, Indexes, Constraints
    - Each section shows:
      - Summary count (e.g., "3 differences")
      - Table with columns: Column Name, Source, Target, Differences
    - Color coding:
      - Green tag for "added"
      - Red tag for "removed"
      - Yellow tag for "modified"
    - Highlight specific field differences (type, nullable, default)
  </action>
  <acceptance_criteria>
    - frontend/src/components/SchemaDiffViewer.tsx exists
    - Component accepts diff result as prop
    - Displays column differences in table format
    - Displays index differences
    - Displays constraint differences
    - Uses color tags for diff types
    - Expandable sections for each category
  </acceptance_criteria>
  <verify>
    <automated>grep "function SchemaDiffViewer" frontend/src/components/SchemaDiffViewer.tsx</automated>
  </verify>
  <done>Schema diff viewer component created</done>
</task>

<task type="auto" tdd="false">
  <name>Task 4: Integrate comparison flow in App</name>
  <files>frontend/src/App.tsx</files>
  <read_first>
    - frontend/src/App.tsx (current state)
    - frontend/src/components/TableBrowser.tsx
    - frontend/src/components/SchemaDiffViewer.tsx
  </read_first>
  <action>
    Update frontend/src/App.tsx:

    1. Add state for:
       - sourceConnectionId, targetConnectionId
       - selectedSourceTable, selectedTargetTable
       - comparisonResult (SchemaDiffResponse | null)

    2. Layout:
       - Top: Connection selection (two dropdowns)
       - Middle: TableBrowser for table selection
       - Bottom: SchemaDiffViewer (shown after comparison)

    3. Wire up useComparison hook:
       - Call compareSchemas when "Compare" button clicked
       - Show loading state during comparison
       - Display result in SchemaDiffViewer
       - Handle errors gracefully
  </action>
  <acceptance_criteria>
    - App.tsx updated with comparison flow
    - Connection selection works
    - Table selection works
    - Compare button triggers comparison
    - Results displayed in SchemaDiffViewer
    - Loading and error states handled
  </acceptance_criteria>
  <verify>
    <automated>grep -E "useComparison|SchemaDiffViewer|TableBrowser" frontend/src/App.tsx</automated>
  </verify>
  <done>Comparison flow integrated in main App</done>
</task>

</tasks>

<verification>
- User can select source and target connections
- User can select tables from each connection
- Clicking Compare shows schema differences
- Diff viewer displays all difference types correctly
- Color coding matches design (green/added, red/removed, yellow/modified)
- Loading states visible during comparison
</verification>

<success_criteria>
- Complete comparison flow from selection to results
- SchemaDiffViewer displays structured, readable diff
- UI is intuitive and responsive
</success_criteria>

<output>
After completion, create `.planning/phases/01-foundation/01-foundation-06-SUMMARY.md` with:
- UI components created
- User flow description
- Any UX decisions made
</output>
