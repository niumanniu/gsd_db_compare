---
phase: 01-foundation
plan: 05
type: execute
wave: 2
depends_on: ["04-PLAN"]
files_modified:
  - frontend/package.json
  - frontend/src/App.tsx
  - frontend/src/components/ConnectionForm.tsx
  - frontend/src/components/ConnectionList.tsx
autonomous: true
requirements:
  - CONN-01
  - CONN-02
user_setup: []

must_haves:
  truths:
    - "React project initialized with Vite and TypeScript"
    - "Connection management UI exists"
    - "Can create, list, delete connections"
  artifacts:
    - path: frontend/src/components/ConnectionForm.tsx
      provides: Connection form component
      contains: "function ConnectionForm"
    - path: frontend/src/components/ConnectionList.tsx
      provides: Connection list component
      contains: "function ConnectionList"
  key_links:
    - from: frontend/src/components/ConnectionForm.tsx
      to: frontend/src/hooks/useConnections.ts
      via: "useConnections hook"
      pattern: "useConnections"
---

<objective>
Create React frontend with connection management UI.

Purpose: Provide user interface for managing database connections.
Output: React components for connection CRUD operations.
</objective>

<execution_context>
@~/.claude/get-shit-done/workflows/execute-plan.md
@~/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/PROJECT.md
@.planning/ROADMAP.md
@.planning/phases/01-foundation/1-CONTEXT.md (T-4: React Project Structure)
@.planning/phases/01-foundation/1-RESEARCH.md (React Patterns)
</context>

<tasks>

<task type="auto" tdd="false">
  <name>Task 1: Initialize React project with Vite and TypeScript</name>
  <files>frontend/package.json, frontend/vite.config.ts, frontend/tsconfig.json</files>
  <read_first>
    - .planning/research/STACK.md (Frontend section)
  </read_first>
  <action>
    Create frontend project structure:

    1. Run: npm create vite@latest . -- --template react-ts
       Or create manually:
       - frontend/package.json with dependencies
       - frontend/vite.config.ts
       - frontend/tsconfig.json, tsconfig.node.json
       - frontend/index.html

    2. Install dependencies:
       - react, react-dom
       - typescript
       - antd
       - zustand
       - axios
       - @tanstack/react-query
       - @tanstack/react-table

    3. Create directory structure:
       - frontend/src/components/
       - frontend/src/hooks/
       - frontend/src/api/
       - frontend/src/types/
  </action>
  <acceptance_criteria>
    - frontend/package.json exists with all dependencies
    - frontend/vite.config.ts exists
    - frontend/tsconfig.json exists
    - frontend/index.html exists
    - frontend/src directory structure created
  </acceptance_criteria>
  <verify>
    <automated>ls frontend/package.json frontend/vite.config.ts frontend/tsconfig.json frontend/index.html</automated>
  </verify>
  <done>React project initialized</done>
</task>

<task type="auto" tdd="false">
  <name>Task 2: Create API client and hooks</name>
  <files>frontend/src/api/client.ts, frontend/src/hooks/useConnections.ts</files>
  <read_first>
    - .planning/phases/01-foundation/1-RESEARCH.md (React Patterns)
  </read_first>
  <action>
    Create frontend/src/api/client.ts:
    ```typescript
    import axios from 'axios';

    const apiClient = axios.create({
      baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
    });

    export default apiClient;
    ```

    Create frontend/src/hooks/useConnections.ts:
    ```typescript
    import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
    import apiClient from '../api/client';

    export function useConnections() {
      const queryClient = useQueryClient();

      const { data: connections, isLoading } = useQuery({
        queryKey: ['connections'],
        queryFn: () => apiClient.get('/api/connections').then(r => r.data),
      });

      const createMutation = useMutation({
        mutationFn: (data: any) => apiClient.post('/api/connections', data),
        onSuccess: () => queryClient.invalidateQueries(['connections']),
      });

      const deleteMutation = useMutation({
        mutationFn: (id: number) => apiClient.delete(`/api/connections/${id}`),
        onSuccess: () => queryClient.invalidateQueries(['connections']),
      });

      return {
        connections: connections || [],
        isLoading,
        createConnection: createMutation.mutateAsync,
        deleteConnection: deleteMutation.mutateAsync,
      };
    }
    ```
  </action>
  <acceptance_criteria>
    - frontend/src/api/client.ts exists
    - frontend/src/hooks/useConnections.ts exists
    - useConnections hook provides: connections, isLoading, createConnection, deleteConnection
    - API client configured with baseURL from env
  </acceptance_criteria>
  <verify>
    <automated>ls frontend/src/api/client.ts frontend/src/hooks/useConnections.ts</automated>
  </verify>
  <done>API client and hooks created</done>
</task>

<task type="auto" tdd="false">
  <name>Task 3: Create connection form and list components</name>
  <files>frontend/src/components/ConnectionForm.tsx, frontend/src/components/ConnectionList.tsx</files>
  <read_first>
    - .planning/phases/01-foundation/1-RESEARCH.md (React Patterns - Connection Form)
  </read_first>
  <action>
    Create frontend/src/components/ConnectionForm.tsx:
    - Form with fields: name, db_type (select), host, port, database, username, password
    - Submit button with loading state
    - Form validation using Ant Design rules
    - onSuccess callback to close modal/refresh list

    Create frontend/src/components/ConnectionList.tsx:
    - Table displaying saved connections
    - Columns: name, db_type, host, port, database, actions
    - Action buttons: View Tables, Delete
    - "Add Connection" button to open form modal
    - Loading state handling
    - Error state handling
  </action>
  <acceptance_criteria>
    - frontend/src/components/ConnectionForm.tsx exists
    - frontend/src/components/ConnectionList.tsx exists
    - ConnectionForm has all required fields with validation
    - ConnectionList displays connections in table format
    - Delete button works with confirmation
  </acceptance_criteria>
  <verify>
    <automated>grep -E "function ConnectionForm|function ConnectionList" frontend/src/components/*.tsx</automated>
  </verify>
  <done>Connection UI components created</done>
</task>

<task type="auto" tdd="false">
  <name>Task 4: Set up main App component</name>
  <files>frontend/src/App.tsx, frontend/src/main.tsx</files>
  <read_first>
    - frontend/src/components/ConnectionList.tsx
  </read_first>
  <action>
    Update frontend/src/App.tsx:
    - Import QueryClientProvider from @tanstack/react-query
    - Create QueryClient instance
    - Wrap app with QueryClientProvider
    - Render ConnectionList as main view
    - Add header with title

    Update frontend/src/main.tsx:
    - Import App component
    - Import Ant Design styles
    - Render App with React.StrictMode
  </action>
  <acceptance_criteria>
    - frontend/src/App.tsx contains QueryClientProvider setup
    - frontend/src/main.tsx renders App component
    - App displays connection management UI
  </acceptance_criteria>
  <verify>
    <automated>grep "QueryClientProvider" frontend/src/App.tsx</automated>
  </verify>
  <done>React app configured and ready to run</done>
</task>

</tasks>

<verification>
- Frontend builds without errors (npm run build)
- Frontend dev server starts (npm run dev)
- Connection form submits data to API
- Connection list displays saved connections
- Delete connection works with confirmation
</verification>

<success_criteria>
- frontend/ contains complete React application
- ConnectionForm can create new connections
- ConnectionList displays and deletes connections
- UI is responsive and usable
</success_criteria>

<output>
After completion, create `.planning/phases/01-foundation/01-foundation-05-SUMMARY.md` with:
- Components created
- UI library decisions
- Any frontend challenges encountered
</output>
