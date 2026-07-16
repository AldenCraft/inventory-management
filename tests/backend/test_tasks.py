"""
Tests for the tasks CRUD endpoints.

The task store is an in-memory global that persists across requests within the
process, so each test cleans up any task it creates to stay independent of the
others (and of run order).
"""
import pytest


class TestTasksEndpoints:
    """Test suite for /api/tasks CRUD endpoints."""

    def test_get_tasks_returns_list(self, client):
        """GET /api/tasks returns a JSON list."""
        response = client.get("/api/tasks")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_create_task(self, client):
        """POST /api/tasks creates a task with a server-assigned id."""
        payload = {"title": "Test task", "priority": "high", "dueDate": "2025-11-01"}
        response = client.post("/api/tasks", json=payload)
        assert response.status_code == 201

        task = response.json()
        assert task["title"] == "Test task"
        assert task["priority"] == "high"
        assert task["dueDate"] == "2025-11-01"
        assert task["status"] == "pending"
        # Server-assigned ids start at 1000 to avoid colliding with client mock ids (1-4).
        assert isinstance(task["id"], int)
        assert task["id"] >= 1000

        # Cleanup
        client.delete(f"/api/tasks/{task['id']}")

    def test_created_task_appears_in_list(self, client):
        """A created task is retrievable via GET and disappears after delete."""
        payload = {"title": "Persisted task", "priority": "low", "dueDate": "2025-12-15"}
        task_id = client.post("/api/tasks", json=payload).json()["id"]

        ids = [t["id"] for t in client.get("/api/tasks").json()]
        assert task_id in ids

        client.delete(f"/api/tasks/{task_id}")
        ids_after = [t["id"] for t in client.get("/api/tasks").json()]
        assert task_id not in ids_after

    def test_create_task_defaults_priority(self, client):
        """Priority defaults to medium when omitted."""
        response = client.post("/api/tasks", json={"title": "No priority", "dueDate": "2025-11-05"})
        assert response.status_code == 201
        task = response.json()
        assert task["priority"] == "medium"
        client.delete(f"/api/tasks/{task['id']}")

    def test_toggle_task(self, client):
        """PATCH toggles a task between pending and completed."""
        task_id = client.post(
            "/api/tasks", json={"title": "Toggle me", "priority": "medium", "dueDate": "2025-11-10"}
        ).json()["id"]

        toggled = client.patch(f"/api/tasks/{task_id}")
        assert toggled.status_code == 200
        assert toggled.json()["status"] == "completed"

        toggled_back = client.patch(f"/api/tasks/{task_id}")
        assert toggled_back.json()["status"] == "pending"

        client.delete(f"/api/tasks/{task_id}")

    def test_delete_task(self, client):
        """DELETE removes a task and reports success."""
        task_id = client.post(
            "/api/tasks", json={"title": "Delete me", "priority": "high", "dueDate": "2025-11-12"}
        ).json()["id"]

        response = client.delete(f"/api/tasks/{task_id}")
        assert response.status_code == 200
        assert response.json()["success"] is True

    def test_delete_missing_task_returns_404(self, client):
        """Deleting a non-existent task returns 404."""
        response = client.delete("/api/tasks/999999")
        assert response.status_code == 404

    def test_toggle_missing_task_returns_404(self, client):
        """Toggling a non-existent task returns 404."""
        response = client.patch("/api/tasks/999999")
        assert response.status_code == 404

    def test_create_task_requires_title(self, client):
        """Missing required fields yield a 422 validation error."""
        response = client.post("/api/tasks", json={"priority": "high", "dueDate": "2025-11-01"})
        assert response.status_code == 422
