---
phase: 02-multi-database-support
plan: 04
type: execute
wave: 3
depends_on: ["02-PLAN", "03-PLAN"]
files_modified:
  - frontend/src/components/ReportViewer.tsx
  - frontend/src/components/SchemaDiffViewer.tsx
  - frontend/src/hooks/useComparison.ts
  - frontend/src/App.tsx
autonomous: true
requirements:
  - UI-01
  - UI-02
  - REPORT-01

must_haves:
  truths:
    - "UI includes report export buttons (HTML, Excel)"
    - "Schema diff viewer shows database type information"
    - "Comparison request can specify database types"
    - "Downloaded reports are accessible to user"
  artifacts:
    - path: frontend/src/components/ReportViewer.tsx
      provides: Report export UI
      contains: "function ReportViewer", "export buttons"
    - path: frontend/src/components/SchemaDiffViewer.tsx
      provides: Enhanced diff viewer
      contains: "database type display"
  key_links:
    - from: frontend/src/components/ReportViewer.tsx
      to: frontend/src/hooks/useComparison.ts
      via: "Report export functions"
      pattern: "exportReport"
---

<objective>
Enhance UI for report export and improved comparison viewing.

Purpose: Provide user interface for report generation and display database type information.
Output: Report export buttons, enhanced diff viewer with database info.
</objective>

<execution_context>
@~/.claude/get-shit-done/workflows/execute-plan.md
@~/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/PROJECT.md
@.planning/ROADMAP.md
@.planning/phases/02-multi-database-support/CONTEXT.md (Report export format requirements)
@.planning/phases/01-foundation/1-CONTEXT.md (D-10: UI Design Principles)
</context>

<tasks>

<task type="auto" tdd="false">
  <name>Task 1: Create report export component</name>
  <files>frontend/src/components/ReportViewer.tsx</files>
  <read_first>
    - frontend/src/components/SchemaDiffViewer.tsx (pattern reference)
    - .planning/phases/02-multi-database-support/CONTEXT.md (Report format requirements)
  </read_first>
  <action>
    Create frontend/src/components/ReportViewer.tsx:

    ```typescript
    import { Button, Space, message } from 'antd';
    import { DownloadOutlined, FileExcelOutlined, FileHtmlOutlined } from '@ant-design/icons';
    import apiClient from '../api/client';
    import type { SchemaDiffResponse } from '../types';

    interface ReportViewerProps {
      diffResult: SchemaDiffResponse | null;
      sourceDb: string;
      targetDb: string;
    }

    export const ReportViewer: React.FC<ReportViewerProps> = ({
      diffResult,
      sourceDb,
      targetDb,
    }) => {
      const handleExportHTML = async () => {
        try {
          const response = await apiClient.post('/api/reports/html', {
            diff_result: diffResult,
            source_db: sourceDb,
            target_db: targetDb,
          }, {
            responseType: 'blob',
          });
          // Trigger download
          const blob = new Blob([response.data], { type: 'text/html' });
          const url = window.URL.createObjectURL(blob);
          const link = document.createElement('a');
          link.href = url;
          link.download = `comparison_report_${Date.now()}.html`;
          link.click();
          window.URL.revokeObjectURL(url);
          message.success('HTML report downloaded');
        } catch (error) {
          message.error('Failed to generate HTML report');
        }
      };

      const handleExportExcel = async () => {
        try {
          const response = await apiClient.post('/api/reports/excel', {
            diff_result: diffResult,
            source_db: sourceDb,
            target_db: targetDb,
          }, {
            responseType: 'blob',
          });
          // Trigger download
          const blob = new Blob([response.data], {
            type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
          });
          const url = window.URL.createObjectURL(blob);
          const link = document.createElement('a');
          link.href = url;
          link.download = `comparison_report_${Date.now()}.xlsx`;
          link.click();
          window.URL.revokeObjectURL(url);
          message.success('Excel report downloaded');
        } catch (error) {
          message.error('Failed to generate Excel report');
        }
      };

      if (!diffResult) {
        return null;
      }

      return (
        <div style={{ marginTop: 24, padding: '16px', background: '#f5f5f5', borderRadius: 8 }}>
          <Space>
            <Button
              type="primary"
              icon={<FileHtmlOutlined />}
              onClick={handleExportHTML}
              disabled={!diffResult}
            >
              Export HTML
            </Button>
            <Button
              type="primary"
              icon={<FileExcelOutlined />}
              onClick={handleExportExcel}
              disabled={!diffResult}
            >
              Export Excel
            </Button>
          </Space>
        </div>
      );
    };
    ```
  </action>
  <acceptance_criteria>
    - frontend/src/components/ReportViewer.tsx exists
    - Component has Export HTML button
    - Component has Export Excel button
    - Buttons trigger API calls to report endpoints
    - Downloaded files have proper filenames
    - Success/error messages displayed
  </acceptance_criteria>
  <verify>
    <automated>grep -E "function ReportViewer|handleExportHTML|handleExportExcel" frontend/src/components/ReportViewer.tsx</automated>
  </verify>
  <done>Report export component created</done>
</task>

<task type="auto" tdd="false">
  <name>Task 2: Enhance SchemaDiffViewer with database type info</name>
  <files>frontend/src/components/SchemaDiffViewer.tsx</files>
  <read_first>
    - frontend/src/components/SchemaDiffViewer.tsx (current implementation)
  </read_first>
  <action>
    Update frontend/src/components/SchemaDiffViewer.tsx to show database type information:

    1. Add new props:
       ```typescript
       interface SchemaDiffViewerProps {
         diffResult: SchemaDiffResponse | null;
         sourceDbName?: string;    // e.g., "MySQL 8.0.32"
         targetDbName?: string;    // e.g., "MySQL 5.7.40"
         sourceDbType?: string;    // e.g., "mysql"
         targetDbType?: string;    // e.g., "mysql"
       }
       ```

    2. Add database info header at top of component:
       ```tsx
       <div style={{ marginBottom: 16, padding: 12, background: '#e6f7ff', borderRadius: 8 }}>
         <Text strong>Comparison: </Text>
         <Tag color="blue">{sourceDbType?.toUpperCase()}</Tag>
         <Text type="secondary"> {sourceDbName} </Text>
         <ArrowRightOutlined />
         <Tag color="blue">{targetDbType?.toUpperCase()}</Tag>
         <Text type="secondary"> {targetDbName} </Text>
       </div>
       ```

    3. Add comparison mode indicator:
       - Show "Same Database Type" or "Cross Database Comparison" badge
  </action>
  <acceptance_criteria>
    - SchemaDiffViewer accepts database type/name props
    - Header displays source and target database information
    - Comparison mode badge visible
    - Database info styled distinctly from diff content
  </acceptance_criteria>
  <verify>
    <automated>grep -E "sourceDbType|targetDbType|sourceDbName|targetDbName" frontend/src/components/SchemaDiffViewer.tsx</automated>
  </verify>
  <done>SchemaDiffViewer enhanced with database information</done>
</task>

<task type="auto" tdd="false">
  <name>Task 3: Update comparison hook for report exports</name>
  <files>frontend/src/hooks/useComparison.ts</files>
  <read_first>
    - frontend/src/hooks/useComparison.ts (current implementation)
  </read_first>
  <action>
    Update frontend/src/hooks/useComparison.ts to include report export functions:

    ```typescript
    export function useComparison() {
      // ... existing compare mutation ...

      // Report export mutations
      const exportHtmlMutation = useMutation({
        mutationFn: async (data: ReportExportRequest) => {
          const response = await apiClient.post('/api/reports/html', data, {
            responseType: 'blob',
          });
          return response.data;
        },
      });

      const exportExcelMutation = useMutation({
        mutationFn: async (data: ReportExportRequest) => {
          const response = await apiClient.post('/api/reports/excel', data, {
            responseType: 'blob',
          });
          return response.data;
        },
      });

      const downloadReport = (blob: Blob, filename: string) => {
        const url = window.URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = filename;
        link.click();
        window.URL.revokeObjectURL(url);
      };

      return {
        compareSchemas: compareMutation.mutateAsync,
        isComparing: compareMutation.isPending,
        comparisonResult: compareMutation.data ?? null,
        error: compareMutation.error,
        resetComparison: compareMutation.reset,
        exportHTML: exportHtmlMutation.mutateAsync,
        exportExcel: exportExcelMutation.mutateAsync,
        isExporting: exportHtmlMutation.isPending || exportExcelMutation.isPending,
        downloadReport, // Utility function
      };
    }
    ```

    2. Add types to frontend/src/types/index.ts:
       ```typescript
       export interface ReportExportRequest {
         diff_result: SchemaDiffResponse;
         source_db: string;
         target_db: string;
       }
       ```
  </action>
  <acceptance_criteria>
    - useComparison hook exports updated
    - exportHTML and exportExcel functions available
    - downloadReport utility function included
    - isExporting state tracks export progress
    - ReportExportRequest type added
  </acceptance_criteria>
  <verify>
    <automated>grep -E "exportHTML|exportExcel|downloadReport" frontend/src/hooks/useComparison.ts</automated>
  </verify>
  <done>Comparison hook updated with report export functions</done>
</task>

<task type="auto" tdd="false">
  <name>Task 4: Integrate report viewer into main App</name>
  <files>frontend/src/App.tsx</files>
  <read_first>
    - frontend/src/App.tsx (current implementation)
    - frontend/src/components/ReportViewer.tsx
    - frontend/src/components/SchemaDiffViewer.tsx
  </read_first>
  <action>
    Update frontend/src/App.tsx to integrate report viewer:

    1. Import ReportViewer component:
       ```typescript
       import { ReportViewer } from './components/ReportViewer';
       import { SchemaDiffViewer } from './components/SchemaDiffViewer';
       ```

    2. Add state for database names/types:
       ```typescript
       const [sourceDbInfo, setSourceDbInfo] = useState({ name: '', type: 'mysql' });
       const [targetDbInfo, setTargetDbInfo] = useState({ name: '', type: 'mysql' });
       ```

    3. Update layout to include report viewer after SchemaDiffViewer:
       ```tsx
       <div className="App">
         {/* Connection selection */}
         {/* Table selection */}
         {/* Compare button */}

         {comparisonResult && (
           <>
             <SchemaDiffViewer
               diffResult={comparisonResult}
               sourceDbName={sourceDbInfo.name}
               targetDbName={targetDbInfo.name}
               sourceDbType={sourceDbInfo.type}
               targetDbType={targetDbInfo.type}
             />
             <ReportViewer
               diffResult={comparisonResult}
               sourceDb={sourceDbInfo.name}
               targetDb={targetDbInfo.name}
             />
           </>
         )}
       </div>
       ```

    4. Update comparison flow to capture database info when connections selected
  </action>
  <acceptance_criteria>
    - App.tsx imports ReportViewer
    - ReportViewer rendered after SchemaDiffViewer
    - Database info passed to both viewers
    - Report export buttons visible after comparison
    - Full comparison flow works end-to-end
  </acceptance_criteria>
  <verify>
    <automated>grep -E "ReportViewer|SchemaDiffViewer" frontend/src/App.tsx</automated>
  </verify>
  <done>Report viewer integrated into main application</done>
</task>

</tasks>

<verification>
- Export HTML button triggers download
- Export Excel button triggers download
- Database type information displayed in diff viewer
- Report viewer appears after comparison completes
- UI provides clear feedback during export
</verification>

<success_criteria>
- frontend/src/components/ReportViewer.tsx provides export functionality
- frontend/src/components/SchemaDiffViewer.tsx shows database information
- frontend/src/hooks/useComparison.ts includes report export functions
- Frontend App integrates report viewer seamlessly
</success_criteria>

<output>
After completion, create `.planning/phases/02-multi-database-support/02-multi-database-support-04-SUMMARY.md` with:
- UI components added
- Report export flow description
- Any frontend integration considerations
</output>
