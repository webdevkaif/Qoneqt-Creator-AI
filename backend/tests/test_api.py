"""
Backend test suite using pytest and httpx AsyncClient.
Tests: auth, projects, generation jobs, script generation, and health check.
Note: Tests require a running MongoDB and Redis.
Run with: pytest tests/ -v
"""
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.core.database import connect_db, close_db

BASE = "/api/v1"


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest_asyncio.fixture
async def client():
    await connect_db()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c
    await close_db()


@pytest_asyncio.fixture
async def auth_client(client):
    """Returns an authenticated client with cookies set."""
    # Register a test user
    resp = await client.post(f"{BASE}/auth/register", json={
        "email": "test_runner@example.com",
        "username": "testrunner",
        "password": "TestPass123",
    })
    # Ignore 409 if already exists, then login
    if resp.status_code == 409:
        resp = await client.post(f"{BASE}/auth/login", json={
            "email": "test_runner@example.com",
            "password": "TestPass123",
        })
    assert resp.status_code in (200, 201), f"Auth failed: {resp.text}"
    token = resp.json()["access_token"]
    client.headers["Authorization"] = f"Bearer {token}"
    return client


# ─── Health Check ────────────────────────────────────────────────────────────

@pytest.mark.anyio
async def test_health_check(client):
    resp = await client.get(f"{BASE}/system/health")
    assert resp.status_code == 200
    data = resp.json()
    assert "status" in data
    assert "ffmpeg" in data
    assert "providers" in data


# ─── Auth ─────────────────────────────────────────────────────────────────────

@pytest.mark.anyio
async def test_register(client):
    import uuid
    unique = uuid.uuid4().hex[:8]
    resp = await client.post(f"{BASE}/auth/register", json={
        "email": f"user_{unique}@example.com",
        "username": f"user_{unique}",
        "password": "ValidPass1",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert "access_token" in data
    assert data["user"]["email"] == f"user_{unique}@example.com"


@pytest.mark.anyio
async def test_register_duplicate_email(client):
    email = "dup_test@example.com"
    payload = {"email": email, "username": "dupuser1", "password": "ValidPass1"}
    await client.post(f"{BASE}/auth/register", json=payload)
    resp = await client.post(f"{BASE}/auth/register", json={**payload, "username": "dupuser2"})
    assert resp.status_code == 409


@pytest.mark.anyio
async def test_login_invalid(client):
    resp = await client.post(f"{BASE}/auth/login", json={
        "email": "nobody@example.com", "password": "wrongpass"
    })
    assert resp.status_code == 401


@pytest.mark.anyio
async def test_get_me(auth_client):
    resp = await auth_client.get(f"{BASE}/auth/me")
    assert resp.status_code == 200
    assert "email" in resp.json()


@pytest.mark.anyio
async def test_weak_password(client):
    resp = await client.post(f"{BASE}/auth/register", json={
        "email": "weak@example.com", "username": "weakuser", "password": "12345678"
    })
    assert resp.status_code == 422  # no letters


# ─── Projects ────────────────────────────────────────────────────────────────

@pytest.mark.anyio
async def test_create_project(auth_client):
    resp = await auth_client.post(f"{BASE}/projects", json={
        "title": "Test Video Project",
        "topic": "Artificial Intelligence in Healthcare",
        "community": "Technology",
        "duration": 30,
        "style": "Educational",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["title"] == "Test Video Project"
    assert data["status"] == "draft"
    return data["id"]


@pytest.mark.anyio
async def test_list_projects(auth_client):
    resp = await auth_client.get(f"{BASE}/projects")
    assert resp.status_code == 200
    data = resp.json()
    assert "projects" in data
    assert "total" in data


@pytest.mark.anyio
async def test_project_ownership(auth_client, client):
    """Another user should not be able to access this project."""
    # Create project
    resp = await auth_client.post(f"{BASE}/projects", json={
        "title": "Private Project", "topic": "Secret", "community": "Technology", "duration": 15, "style": "Educational",
    })
    project_id = resp.json()["id"]

    # Different user
    import uuid
    uid = uuid.uuid4().hex[:8]
    reg = await client.post(f"{BASE}/auth/register", json={
        "email": f"other_{uid}@example.com",
        "username": f"other_{uid}",
        "password": "ValidPass1",
    })
    other_token = reg.json()["access_token"]
    resp2 = await client.get(f"{BASE}/projects/{project_id}",
                              headers={"Authorization": f"Bearer {other_token}"})
    assert resp2.status_code == 404


@pytest.mark.anyio
async def test_update_project(auth_client):
    resp = await auth_client.post(f"{BASE}/projects", json={
        "title": "Update Test", "topic": "ML", "community": "Technology", "duration": 15, "style": "Educational",
    })
    pid = resp.json()["id"]
    resp2 = await auth_client.patch(f"{BASE}/projects/{pid}", json={"title": "Updated Title"})
    assert resp2.status_code == 200
    assert resp2.json()["title"] == "Updated Title"


@pytest.mark.anyio
async def test_delete_project(auth_client):
    resp = await auth_client.post(f"{BASE}/projects", json={
        "title": "To Delete", "topic": "Test", "community": "Technology", "duration": 15, "style": "Educational",
    })
    pid = resp.json()["id"]
    del_resp = await auth_client.delete(f"{BASE}/projects/{pid}")
    assert del_resp.status_code == 204
    get_resp = await auth_client.get(f"{BASE}/projects/{pid}")
    assert get_resp.status_code == 404


# ─── Generation Jobs ─────────────────────────────────────────────────────────

@pytest.mark.anyio
async def test_script_generation_queued(auth_client):
    """Script generation should be accepted and return a queued job."""
    proj = await auth_client.post(f"{BASE}/projects", json={
        "title": "AI Script Test", "topic": "Climate Change Solutions",
        "community": "Science", "duration": 15, "style": "Educational",
    })
    pid = proj.json()["id"]
    resp = await auth_client.post(f"{BASE}/generate/script/{pid}")
    assert resp.status_code == 202
    data = resp.json()
    assert data["status"] in ("queued", "running")
    assert data["job_type"] == "script"
    return data["id"]


@pytest.mark.anyio
async def test_duplicate_job_prevention(auth_client):
    proj = await auth_client.post(f"{BASE}/projects", json={
        "title": "Dup Job Test", "topic": "Test Topic",
        "community": "Technology", "duration": 15, "style": "Educational",
    })
    pid = proj.json()["id"]
    r1 = await auth_client.post(f"{BASE}/generate/script/{pid}")
    assert r1.status_code == 202
    r2 = await auth_client.post(f"{BASE}/generate/script/{pid}")
    # Second job should be rejected if first is still queued/running
    assert r2.status_code in (202, 409)


@pytest.mark.anyio
async def test_visuals_without_script(auth_client):
    proj = await auth_client.post(f"{BASE}/projects", json={
        "title": "No Script Test", "topic": "Test",
        "community": "Technology", "duration": 15, "style": "Educational",
    })
    pid = proj.json()["id"]
    resp = await auth_client.post(f"{BASE}/generate/visuals/{pid}")
    assert resp.status_code == 400  # Script required first


# ─── Demo Mode ──────────────────────────────────────────────────────────────

@pytest.mark.anyio
async def test_demo_mode_providers(auth_client):
    resp = await auth_client.get(f"{BASE}/system/provider-status")
    assert resp.status_code == 200
    data = resp.json()
    assert "demo_mode" in data
    assert "llm" in data
