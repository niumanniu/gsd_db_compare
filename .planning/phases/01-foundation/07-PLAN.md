---
phase: 01-foundation
plan: 07
type: execute
wave: 3
depends_on: ["06-PLAN"]
files_modified:
  - backend/celery_config.py
  - backend/app/worker.py
  - README.md
autonomous: true
requirements:
  - OPS-01
user_setup: []

must_haves:
  truths:
    - "Celery worker can process comparison tasks"
    - "Redis is configured as message broker"
    - "Long-running comparisons execute asynchronously"
  artifacts:
    - path: backend/celery_config.py
      provides: Celery configuration
      contains: "Celery app configuration"
    - path: backend/app/worker.py
      provides: Celery worker entry point
      contains: "compare_schema_task"
  key_links:
    - from: backend/app/worker.py
      to: backend/app/comparison/schema.py
      via: "SchemaComparator"
      pattern: "SchemaComparator"
---

<objective>
Set up Celery for async task processing and create project documentation.

Purpose: Enable background processing for long-running comparisons and document project setup.
Output: Celery worker configuration, async task support, README with setup instructions.
</objective>

<execution_context>
@~/.claude/get-shit-done/workflows/execute-plan.md
@~/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/PROJECT.md
@.planning/ROADMAP.md
@.planning/phases/01-foundation/1-CONTEXT.md (D-7: Async Task Processing)
@.planning/phases/01-foundation/1-RESEARCH.md (Celery Configuration)
</context>

<tasks>

<task type="auto" tdd="false">
  <name>Task 1: Configure Celery and create worker</name>
  <files>backend/celery_config.py, backend/app/worker.py</files>
  <read_first>
    - .planning/phases/01-foundation/1-RESEARCH.md (Celery Configuration)
  </read_first>
  <action>
    Create backend/celery_config.py:

    ```python
    from celery import Celery

    celery_app = Celery(
        'db_compare',
        broker='redis://localhost:6379/0',
        backend='redis://localhost:6379/1',
    )

    celery_app.conf.update(
        task_serializer='json',
        accept_content=['json'],
        result_serializer='json',
        timezone='UTC',
        enable_utc=True,
        task_track_started=True,
        task_time_limit=300,  # 5 minute timeout
    )
    ```

    Create backend/app/worker.py:

    ```python
    from celery_config import celery_app
    from app.comparison.schema import SchemaComparator
    from app.adapters.mysql import MySQLAdapter
    from app.db.session import get_db_session
    from app.db.models import DbConnection
    from cryptography.fernet import Fernet
    import os

    @celery_app.task(bind=True)
    def compare_schema_task(self, source_conn_id, source_table, target_conn_id, target_table):
        # Fetch connections from DB
        # Decrypt passwords
        # Create adapters
        # Fetch metadata
        # Compare and return result
        pass
    ```
  </action>
  <acceptance_criteria>
    - backend/celery_config.py exists with Celery app configuration
    - backend/app/worker.py exists with compare_schema_task
    - Task fetches connections, decrypts passwords, compares schemas
    - Task returns JSON-serializable result
  </acceptance_criteria>
  <verify>
    <automated>ls backend/celery_config.py backend/app/worker.py</automated>
  </verify>
  <done>Celery configured and worker task created</done>
</task>

<task type="auto" tdd="false">
  <name>Task 2: Update comparison API to use async tasks</name>
  <files>backend/app/api/compare.py</files>
  <read_first>
    - backend/app/api/compare.py (current state)
    - backend/app/worker.py
  </read_first>
  <action>
    Update backend/app/api/compare.py:

    1. Import Celery task:
       ```python
       from app.worker import compare_schema_task
       ```

    2. Update POST /api/compare/schema to:
       - Create Celery task instead of synchronous comparison
       - Return task_id immediately

    3. Add GET /api/tasks/{task_id} endpoint:
       - Check task status using AsyncResult
       - Return status: pending/running/completed/failed
       - Return result when completed
  </action>
  <acceptance_criteria>
    - compare.py imports compare_schema_task
    - POST /schema endpoint creates async task
    - GET /tasks/{task_id} returns task status
    - Task result stored in database when completed
  </acceptance_criteria>
  <verify>
    <automated>grep -E "compare_schema_task|AsyncResult|/api/tasks" backend/app/api/compare.py</automated>
  </verify>
  <done>Comparison API updated for async processing</done>
</task>

<task type="auto" tdd="false">
  <name>Task 3: Create project README</name>
  <files>README.md</files>
  <read_first>
    - .planning/PROJECT.md
    - .planning/ROADMAP.md
  </read_first>
  <action>
    Create README.md with:

    1. Project title and description (in Chinese)
    2. Features list
    3. Screenshots (placeholder)
    4. Quick Start:
       - Prerequisites (Python 3.11+, Node.js 18+, Redis, PostgreSQL)
       - Backend setup (pip install, environment variables, alembic upgrade)
       - Frontend setup (npm install, npm run dev)
       - Start Celery worker
    5. Configuration (environment variables)
    6. Usage guide (how to create connections, compare schemas)
    7. Project structure
    8. Development (running tests, etc.)
    9. License
  </action>
  <acceptance_criteria>
    - README.md exists at project root
    - Contains setup instructions for backend and frontend
    - Contains environment variable documentation
    - Contains basic usage guide
    - Written in Chinese (primary language for users)
  </acceptance_criteria>
  <verify>
    <automated>head -50 README.md</automated>
  </verify>
  <done>Project README created</done>
</task>

<task type="auto" tdd="false">
  <name>Task 4: Create .env.example files</name>
  <files>backend/.env.example, frontend/.env.example</files>
  <read_first>
    - .planning/phases/01-foundation/1-CONTEXT.md (T-6: Environment Variables)
  </read_first>
  <action>
    Create backend/.env.example:
    ```
    DATABASE_URL=postgresql://user:password@localhost:5432/db_compare
    ENCRYPTION_KEY=<generate-32-byte-key>
    CELERY_BROKER_URL=redis://localhost:6379/0
    CELERY_RESULT_BACKEND=redis://localhost:6379/1
    LOG_LEVEL=INFO
    ```

    Create frontend/.env.example:
    ```
    VITE_API_BASE_URL=http://localhost:8000
    ```

    Add note about generating ENCRYPTION_KEY:
    ```python
    from cryptography.fernet import Fernet
    print(Fernet.generate_key().decode())
    ```
  </action>
  <acceptance_criteria>
    - backend/.env.example exists with all required variables
    - frontend/.env.example exists with API base URL
    - Instructions for generating ENCRYPTION_KEY included
  </acceptance_criteria>
  <verify>
    <automated>cat backend/.env.example frontend/.env.example</automated>
  </verify>
  <done>Environment variable templates created</done>
</task>

</tasks>

<verification>
- Celery worker starts successfully
- Async comparison tasks execute correctly
- Task status can be polled via API
- README provides clear setup instructions
- Environment variables documented
</verification>

<success_criteria>
- backend/celery_config.py configures Celery correctly
- backend/app/worker.py contains working comparison task
- README.md enables new users to set up project
- .env.example files provide configuration templates
</success_criteria>

<output>
After completion, create `.planning/phases/01-foundation/01-foundation-07-SUMMARY.md` with:
- Celery setup details
- Async task flow description
- Any deployment considerations
</output>

---

*Phase 1: Foundation plans complete. Summary files will be created during execution.*
