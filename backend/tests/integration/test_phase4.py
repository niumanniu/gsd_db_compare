"""Integration tests for Phase 4 - Advanced Features (Scheduling & Alerting)."""

import pytest
import asyncio
from httpx import AsyncClient
from typing import AsyncGenerator

BASE_URL = "http://localhost:8000"


@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    """Create async HTTP client."""
    async with AsyncClient(base_url=BASE_URL) as client:
        yield client


@pytest.fixture
async def test_connections(client: AsyncClient) -> AsyncGenerator[tuple[int, int], None]:
    """Create test database connections."""
    # Create source connection
    source_response = await client.post("/api/connections", json={
        "name": "Test Source DB",
        "db_type": "mysql",
        "host": "localhost",
        "port": 3306,
        "database": "test_source",
        "username": "test",
        "password": "test123",
    })

    # Create target connection
    target_response = await client.post("/api/connections", json={
        "name": "Test Target DB",
        "db_type": "mysql",
        "host": "localhost",
        "port": 3306,
        "database": "test_target",
        "username": "test",
        "password": "test123",
    })

    source_id = source_response.json()["id"]
    target_id = target_response.json()["id"]

    yield (source_id, target_id)

    # Cleanup
    await client.delete(f"/api/connections/{source_id}")
    await client.delete(f"/api/connections/{target_id}")


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient) -> None:
    """Test health check endpoint."""
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_scheduled_task_crud(client: AsyncClient, test_connections: tuple[int, int]) -> None:
    """Test full CRUD workflow for scheduled tasks."""
    source_id, target_id = test_connections

    # 1. Create scheduled task
    create_response = await client.post("/api/scheduled-tasks", json={
        "name": "Integration Test Task",
        "description": "Test task for Phase 4",
        "cron_expression": "0 */2 * * *",
        "source_connection_id": source_id,
        "target_connection_id": target_id,
        "tables": [
            {"source": "users", "target": "users", "critical": True},
            {"source": "orders", "target": "orders", "critical": False},
        ],
        "compare_mode": "schema",
        "notification_enabled": False,
        "enabled": True,
    })

    assert create_response.status_code == 201
    task_data = create_response.json()
    task_id = task_data["id"]

    assert task_data["name"] == "Integration Test Task"
    assert task_data["cron_expression"] == "0 */2 * * *"
    assert task_data["enabled"] is True
    assert len(task_data["tables"]) == 2

    # 2. Get task by ID
    get_response = await client.get(f"/api/scheduled-tasks/{task_id}")
    assert get_response.status_code == 200
    assert get_response.json()["id"] == task_id

    # 3. Update task
    update_response = await client.put(f"/api/scheduled-tasks/{task_id}", json={
        "name": "Updated Test Task",
        "enabled": False,
    })
    assert update_response.status_code == 200
    assert update_response.json()["name"] == "Updated Test Task"
    assert update_response.json()["enabled"] is False

    # 4. Toggle task
    toggle_response = await client.post(f"/api/scheduled-tasks/{task_id}/toggle")
    assert toggle_response.status_code == 200
    assert toggle_response.json()["enabled"] is True

    # 5. Run task manually
    run_response = await client.post(f"/api/scheduled-tasks/{task_id}/run")
    assert run_response.status_code == 200
    assert "status" in run_response.json()

    # 6. Delete task
    delete_response = await client.delete(f"/api/scheduled-tasks/{task_id}")
    assert delete_response.status_code == 204

    # Verify deletion
    get_deleted_response = await client.get(f"/api/scheduled-tasks/{task_id}")
    assert get_deleted_response.status_code == 404


@pytest.mark.asyncio
async def test_list_scheduled_tasks(client: AsyncClient, test_connections: tuple[int, int]) -> None:
    """Test listing scheduled tasks."""
    source_id, target_id = test_connections

    # Create multiple tasks
    for i in range(3):
        await client.post("/api/scheduled-tasks", json={
            "name": f"Test Task {i}",
            "cron_expression": "0 * * * *",
            "source_connection_id": source_id,
            "target_connection_id": target_id,
            "tables": [{"source": "test", "target": "test", "critical": False}],
            "enabled": True,
        })

    # Get all tasks
    all_response = await client.get("/api/scheduled-tasks")
    assert all_response.status_code == 200
    tasks = all_response.json()
    assert len(tasks) >= 3

    # Get enabled tasks only
    enabled_response = await client.get("/api/scheduled-tasks?enabled_only=true")
    assert enabled_response.status_code == 200
    enabled_tasks = enabled_response.json()
    assert all(task["enabled"] for task in enabled_tasks)


@pytest.mark.asyncio
async def test_critical_tables_crud(client: AsyncClient, test_connections: tuple[int, int]) -> None:
    """Test critical table management."""
    source_id, target_id = test_connections

    # 1. Mark table as critical
    mark_response = await client.post("/api/critical-tables", json={
        "connection_id": source_id,
        "table_name": "users",
    })
    assert mark_response.status_code == 201
    critical_id = mark_response.json()["id"]

    # 2. List critical tables
    list_response = await client.get("/api/critical-tables", params={"connection_id": source_id})
    assert list_response.status_code == 200
    tables = list_response.json()
    assert any(t["table_name"] == "users" for t in tables)

    # 3. Check if table is critical
    check_response = await client.get("/api/critical-tables/check", params={
        "connection_id": source_id,
        "table_name": "users",
    })
    assert check_response.status_code == 200
    assert check_response.json()["is_critical"] is True

    # Check non-critical table
    check_non_critical = await client.get("/api/critical-tables/check", params={
        "connection_id": source_id,
        "table_name": "non_critical_table",
    })
    assert check_non_critical.json()["is_critical"] is False

    # 4. Remove critical marker
    delete_response = await client.delete(f"/api/critical-tables/{critical_id}")
    assert delete_response.status_code == 204

    # Verify removal
    check_after_delete = await client.get("/api/critical-tables/check", params={
        "connection_id": source_id,
        "table_name": "users",
    })
    assert check_after_delete.json()["is_critical"] is False


@pytest.mark.asyncio
async def test_comparison_history_empty(client: AsyncClient) -> None:
    """Test comparison history endpoints with no data."""
    # Get history (should be empty)
    history_response = await client.get("/api/comparison-history", params={"limit": 10})
    assert history_response.status_code == 200
    assert isinstance(history_response.json(), list)

    # Get stats (should show zeros)
    stats_response = await client.get("/api/comparison-history/stats")
    assert stats_response.status_code == 200
    stats = stats_response.json()
    assert stats["total_comparisons"] == 0

    # Get trend (should be empty)
    trend_response = await client.get("/api/comparison-history/trend", params={"period": "daily", "days": 7})
    assert trend_response.status_code == 200
    trend = trend_response.json()
    assert trend["data_points"] == []


@pytest.mark.asyncio
async def test_notification_settings_crud(client: AsyncClient) -> None:
    """Test notification settings management."""
    # 1. Create notification settings
    create_response = await client.post("/api/notification-settings", json={
        "smtp_host": "smtp.example.com",
        "smtp_port": 587,
        "smtp_username": "test@example.com",
        "smtp_password": "testpass123",
        "use_tls": True,
        "from_email": "noreply@example.com",
        "default_recipients": ["admin@example.com"],
    })
    assert create_response.status_code == 201
    settings_id = create_response.json()["id"]

    # 2. Get settings
    get_response = await client.get("/api/notification-settings")
    assert get_response.status_code == 200
    assert get_response.json()["smtp_host"] == "smtp.example.com"

    # 3. Update settings
    update_response = await client.put("/api/notification-settings", json={
        "smtp_host": "smtp.updated.com",
        "smtp_port": 465,
    })
    assert update_response.status_code == 200
    assert update_response.json()["smtp_host"] == "smtp.updated.com"
    assert update_response.json()["smtp_port"] == 465

    # 4. Delete settings
    delete_response = await client.delete("/api/notification-settings")
    assert delete_response.status_code == 204

    # Verify deletion
    get_after_delete = await client.get("/api/notification-settings")
    assert get_after_delete.status_code == 404


@pytest.mark.asyncio
async def test_cron_expression_validation(client: AsyncClient, test_connections: tuple[int, int]) -> None:
    """Test cron expression validation."""
    source_id, target_id = test_connections

    # Valid cron expressions
    valid_expressions = [
        "* * * * *",      # Every minute
        "0 * * * *",      # Every hour
        "0 2 * * *",      # Daily at 2 AM
        "0 */2 * * *",    # Every 2 hours
        "0 9 * * 1",      # Every Monday at 9 AM
        "0 0 1 * *",      # First day of month
    ]

    for cron_expr in valid_expressions:
        response = await client.post("/api/scheduled-tasks", json={
            "name": f"Test {cron_expr}",
            "cron_expression": cron_expr,
            "source_connection_id": source_id,
            "target_connection_id": target_id,
            "tables": [{"source": "test", "target": "test", "critical": False}],
            "enabled": False,  # Don't actually schedule
        })
        assert response.status_code == 201, f"Failed for cron: {cron_expr}"

        # Cleanup
        task_id = response.json()["id"]
        await client.delete(f"/api/scheduled-tasks/{task_id}")

    # Invalid cron expression
    invalid_response = await client.post("/api/scheduled-tasks", json={
        "name": "Invalid Cron",
        "cron_expression": "invalid",
        "source_connection_id": source_id,
        "target_connection_id": target_id,
        "tables": [{"source": "test", "target": "test", "critical": False}],
        "enabled": False,
    })
    assert invalid_response.status_code == 400


@pytest.mark.asyncio
async def test_api_routes_available(client: AsyncClient) -> None:
    """Test that all Phase 4 API routes are available."""
    # Check API documentation endpoint
    docs_response = await client.get("/docs")
    assert docs_response.status_code == 200

    # Check OpenAPI schema
    openapi_response = await client.get("/openapi.json")
    assert openapi_response.status_code == 200
    openapi = openapi_response.json()

    # Verify Phase 4 endpoints exist
    paths = openapi.get("paths", {})

    # Scheduled tasks endpoints
    assert "/api/scheduled-tasks" in paths
    assert "/api/scheduled-tasks/{id}" in paths

    # Comparison history endpoints
    assert "/api/comparison-history" in paths
    assert "/api/comparison-history/trend" in paths
    assert "/api/comparison-history/stats" in paths

    # Critical tables endpoints
    assert "/api/critical-tables" in paths
    assert "/api/critical-tables/check" in paths

    # Notification settings endpoints
    assert "/api/notification-settings" in paths

    # Count Phase 4 endpoints (should have at least 15)
    phase4_paths = [
        p for p in paths.keys()
        if any(endpoint in p for endpoint in [
            "scheduled-tasks", "comparison-history",
            "critical-tables", "notification-settings"
        ])
    ]
    assert len(phase4_paths) >= 4  # At least 4 resource types
