import pytest
from aioresponses import aioresponses
from bot.client import APIClient
from aiohttp import ClientError
import logging

@pytest.fixture
def base_url():
    return "http://testserver"

@pytest.fixture
async def api_client(base_url):
    client = APIClient(base_url)
    await client.create_session()
    yield client
    await client.close()

@pytest.fixture
def mock_aioresponse():
    with aioresponses() as m:
        yield m
        
        
        

async def test_create_session(api_client):
    assert api_client.session is not None
    await api_client.close()
    assert api_client.session.closed

async def test_login_success(api_client, mock_aioresponse, base_url):
    url = f"{base_url}/users/auth/telegram/"
    fake_response = {"token": "test_token_123", "user_id": 1}
    
    mock_aioresponse.post(url, payload=fake_response)
    
    data = await api_client.login(12345, "user", "User", "en")
    
    assert data["token"] == "test_token_123"
    assert api_client.token == "test_token_123"

async def test_login_fail(api_client, mock_aioresponse, base_url):
    url = f"{base_url}/users/auth/telegram/"
    mock_aioresponse.post(url, status=500)
    
    with pytest.raises(ClientError):
        await api_client.login(12345, "user", "User")

async def test_get_headers_fail_no_token(api_client):
    api_client.token = None
    with pytest.raises(PermissionError) as exc:
        api_client._get_headers()
    assert "Login first" in str(exc.value)

async def test_get_profile_list_response(api_client, mock_aioresponse, base_url):
    api_client.token = "token"
    url = f"{base_url}/users/profile/"
    
    mock_aioresponse.get(url, payload=[{"id": 1, "language": "ru"}])
    
    profile = await api_client.get_profile()
    assert profile["id"] == 1
    assert profile["language"] == "ru"

async def test_get_profile_dict_results_response(api_client, mock_aioresponse, base_url):
    api_client.token = "token"
    url = f"{base_url}/users/profile/"
    
    mock_aioresponse.get(url, payload={"results": [{"id": 2, "language": "en"}]})
    
    profile = await api_client.get_profile()
    assert profile["id"] == 2

async def test_get_profile_fail_no_token(api_client):
    api_client.token = None
    with pytest.raises(PermissionError):
        await api_client.get_profile()

async def test_update_profile_success(api_client, mock_aioresponse, base_url):
    api_client.token = "token"
    
    mock_aioresponse.get(f"{base_url}/users/profile/", payload=[{"id": 99}])
    
    mock_aioresponse.patch(f"{base_url}/users/profile/99/", payload={"status": "ok"})
    
    resp = await api_client.update_profile(language="ru", timezone="UTC")
    assert resp["status"] == "ok"

async def test_update_profile_no_id(api_client, mock_aioresponse, base_url):
    api_client.token = "token"
    mock_aioresponse.get(f"{base_url}/users/profile/", payload=[{}])
    
    with pytest.raises(ValueError, match="Could not fetch profile id"):
        await api_client.update_profile(language="ru")

# Tasks
async def test_get_tasks(api_client, mock_aioresponse, base_url):
    api_client.token = "token"
    mock_aioresponse.get(f"{base_url}/tasks/", payload=[{"id": 1, "title": "Test"}])
    
    tasks = await api_client.get_tasks()
    assert len(tasks) == 1
    assert tasks[0]["title"] == "Test"

async def test_get_tasks_no_auth(api_client):
    api_client.token = None
    with pytest.raises(PermissionError):
        await api_client.get_tasks()

async def test_create_task(api_client, mock_aioresponse, base_url):
    api_client.token = "token"
    mock_aioresponse.post(f"{base_url}/tasks/", payload={"id": 1, "title": "New"})
    
    task = await api_client.create_task("New", deadline="2025-01-01", category_id="5")
    assert task["id"] == 1

async def test_create_task_no_auth(api_client):
    api_client.token = None
    with pytest.raises(PermissionError):
        await api_client.create_task("Title")

async def test_delete_task(api_client, mock_aioresponse, base_url):
    api_client.token = "token"
    mock_aioresponse.delete(f"{base_url}/tasks/1/", status=204)
    await api_client.delete_task("1")

async def test_update_task(api_client, mock_aioresponse, base_url):
    api_client.token = "token"
    mock_aioresponse.patch(f"{base_url}/tasks/1/", payload={"title": "Updated"})
    res = await api_client.update_task("1", {"title": "Updated"})
    assert res["title"] == "Updated"

async def test_get_task_detail(api_client, mock_aioresponse, base_url):
    api_client.token = "token"
    mock_aioresponse.get(f"{base_url}/tasks/1/", payload={"id": 1})
    res = await api_client.get_task("1")
    assert res["id"] == 1

# Categories
async def test_get_categories_success(api_client, mock_aioresponse, base_url):
    api_client.token = "token"
    mock_aioresponse.get(f"{base_url}/categories/", payload=[{"name": "Work"}])
    cats = await api_client.get_categories()
    assert len(cats) == 1

async def test_get_categories_exception(api_client, mock_aioresponse, base_url):
    api_client.token = "token"
    mock_aioresponse.get(f"{base_url}/categories/", exception=Exception("Boom"))
    
    cats = await api_client.get_categories()
    assert cats == []

async def test_create_category(api_client, mock_aioresponse, base_url):
    api_client.token = "token"
    mock_aioresponse.post(f"{base_url}/categories/", payload={"id": 1, "name": "New"})
    res = await api_client.create_category("New")
    assert res["name"] == "New"

async def test_create_category_no_token(api_client):
    api_client.token = None
    with pytest.raises(PermissionError):
        await api_client.create_category("New")

async def test_delete_category(api_client, mock_aioresponse, base_url):
    api_client.token = "token"
    mock_aioresponse.delete(f"{base_url}/categories/1/", status=204)
    await api_client.delete_category("1")

async def test_update_category_success(api_client, mock_aioresponse, base_url):
    api_client.token = "token"
    mock_aioresponse.patch(f"{base_url}/categories/1/", payload={"name": "Upd"})
    res = await api_client.update_category("1", "Upd")
    assert res["name"] == "Upd"

async def test_update_category_400_logging(api_client, mock_aioresponse, base_url, caplog):
    api_client.token = "token"
    
    with caplog.at_level(logging.ERROR):
        mock_aioresponse.patch(
            f"{base_url}/categories/1/", 
            status=400, 
            body="Bad name"
        )
        
        with pytest.raises(ClientError):
            await api_client.update_category("1", "Bad")
        
        assert "❌ 400 BAD REQUEST" in caplog.text

async def test_get_category_success(api_client, mock_aioresponse, base_url):
    api_client.token = "token"
    mock_aioresponse.get(f"{base_url}/categories/1/", payload={"name": "Cat"})
    res = await api_client.get_category("1")
    assert res["name"] == "Cat"

async def test_get_category_fail(api_client, mock_aioresponse, base_url, caplog):
    api_client.token = "token"
    with caplog.at_level(logging.ERROR):
        mock_aioresponse.get(f"{base_url}/categories/1/", exception=Exception("Fail"))
        
        with pytest.raises(Exception):
            await api_client.get_category("1")
        
        assert "Request failed: Fail" in caplog.text