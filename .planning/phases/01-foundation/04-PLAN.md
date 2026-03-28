---
phase: 01-foundation
plan: 04
type: execute
wave: 2
depends_on: ["03-PLAN"]
files_modified:
  - backend/app/api/connections.py
  - backend/app/api/compare.py
  - backend/app/main.py
autonomous: true
requirements:
  - CONN-01
  - CONN-02
  - SCHEMA-01
user_setup: []

must_haves:
  truths:
    - "API endpoints for connection CRUD exist"
    - "API endpoint for schema comparison exists"
    - "All endpoints return correct responses"
  artifacts:
    - path: backend/app/api/connections.py
      provides: Connection management API
      contains: "create_connection", "list_connections", "delete_connection"
    - path: backend/app/api/compare.py
      provides: Comparison API
      contains: "compare_schemas"
  key_links:
    - from: backend/app/api/connections.py
      to: backend/app/db/models.py
      via: "DbConnection model"
      pattern: "DbConnection"
---

<objective>
Implement FastAPI REST API endpoints for connection management and schema comparison.

Purpose: Expose backend functionality to frontend via HTTP API.
Output: RESTful API endpoints with proper request/response handling.
</objective>

<execution_context>
@~/.claude/get-shit-done/workflows/execute-plan.md
@~/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/PROJECT.md
@.planning/ROADMAP.md
@.planning/phases/01-foundation/1-CONTEXT.md (T-3: FastAPI Project Structure)
@.planning/phases/01-foundation/1-RESEARCH.md (FastAPI Patterns)
</context>

<tasks>

<task type="auto" tdd="false">
  <name>Task 1: Create connection management API</name>
  <files>backend/app/api/connections.py</files>
  <read_first>
    - .planning/phases/01-foundation/1-RESEARCH.md (FastAPI Patterns - Connection CRUD)
    - backend/app/db/models.py (DbConnection model)
    - backend/app/schemas/api.py (Connection schemas)
  </read_first>
  <action>
    Create backend/app/api/connections.py with endpoints:

    1. POST /api/connections:
       - Accept ConnectionCreate schema
       - Test connection using MySQLAdapter
       - Encrypt password using cryptography.fernet
       - Save DbConnection to database
       - Return ConnectionResponse

    2. GET /api/connections:
       - List all saved connections
       - Return list of ConnectionResponse (passwords hidden)

    3. GET /api/connections/{conn_id}:
       - Get specific connection details
       - Return 404 if not found

    4. DELETE /api/connections/{conn_id}:
       - Delete connection from database
       - Return success response

    5. GET /api/connections/{conn_id}/tables:
       - Connect to database using stored credentials
       - Fetch table list using MySQLAdapter
       - Return list of TableInfo
  </action>
  <acceptance_criteria>
    - backend/app/api/connections.py exists
    - File contains router with prefix "/api/connections"
    - POST endpoint creates and tests connection
    - GET endpoints return connection data
    - DELETE endpoint removes connection
    - GET /tables endpoint fetches table list from database
  </acceptance_criteria>
  <verify>
    <automated>grep -E "router|@router\.(post|get|delete)" backend/app/api/connections.py</automated>
  </verify>
  <done>Connection management API implemented</done>
</task>

<task type="auto" tdd="false">
  <name>Task 2: Create schema comparison API</name>
  <files>backend/app/api/compare.py</files>
  <read_first>
    - backend/app/comparison/schema.py (SchemaComparator)
    - backend/app/adapters/mysql.py (MySQLAdapter)
    - backend/app/schemas/api.py (Comparison schemas)
  </read_first>
  <action>
    Create backend/app/api/compare.py with endpoints:

    1. POST /api/compare/schema:
       - Accept SchemaCompareRequest schema
       - Fetch source and target connection from database
       - Decrypt passwords
       - Create MySQLAdapter for both connections
       - Fetch metadata from both tables
       - Run SchemaComparator.compare()
       - Return SchemaDiffResponse

    2. POST /api/compare/schema/async (optional for large tables):
       - Accept SchemaCompareRequest
       - Create Celery task
       - Return task_id for polling

    3. GET /api/tasks/{task_id}:
       - Get task status and result
       - Return pending/running/completed/failed status
  </action>
  <acceptance_criteria>
    - backend/app/api/compare.py exists
    - File contains router with prefix "/api/compare"
    - POST /schema endpoint compares two table schemas
    - SchemaDiffResponse returned with all diff types
    - Task polling endpoints exist (if async implemented)
  </acceptance_criteria>
  <verify>
    <automated>grep -E "router|@router\.(post|get)" backend/app/api/compare.py</automated>
  </verify>
  <done>Schema comparison API implemented</done>
</task>

<task type="auto" tdd="false">
  <name>Task 3: Set up FastAPI application and routing</name>
  <files>backend/app/main.py</files>
  <read_first>
    - .planning/phases/01-foundation/1-CONTEXT.md (T-3: FastAPI Project Structure)
  </read_first>
  <action>
    Create backend/app/main.py:

    1. Create FastAPI app:
       ```python
       from fastapi import FastAPI
       from fastapi.middleware.cors import CORSMiddleware

       app = FastAPI(title="DB Compare API")

       # CORS for frontend
       app.add_middleware(
           CORSMiddleware,
           allow_origins=["http://localhost:5173"],
           allow_credentials=True,
           allow_methods=["*"],
           allow_headers=["*"],
       )
       ```

    2. Include routers:
       ```python
       from app.api import connections, compare

       app.include_router(connections.router)
       app.include_router(compare.router)
       ```

    3. Health check endpoint:
       ```python
       @app.get("/health")
       def health_check():
           return {"status": "ok"}
       ```

    4. Create backend/app/__init__.py to make app importable
  </action>
  <acceptance_criteria>
    - backend/app/main.py exists
    - File contains FastAPI app instance
    - CORS middleware configured
    - Routers included from connections and compare modules
    - Health check endpoint exists
  </acceptance_criteria>
  <verify>
    <automated>grep -E "FastAPI|include_router|@app\.get" backend/app/main.py</automated>
  </verify>
  <done>FastAPI application set up with all routes</done>
</task>

</tasks>

<verification>
- FastAPI application starts without errors
- All API endpoints respond
- Connection CRUD operations work correctly
- Schema comparison returns correct results
- API documentation available at /docs
</verification>

<success_criteria>
- backend/app/api/connections.py contains connection management endpoints
- backend/app/api/compare.py contains comparison endpoints
- backend/app/main.py creates and configures FastAPI app
- API can be tested via /docs Swagger UI
</success_criteria>

<output>
After completion, create `.planning/phases/01-foundation/01-foundation-04-SUMMARY.md` with:
- API endpoints implemented
- Any API design decisions made
- Testing notes
</output>
