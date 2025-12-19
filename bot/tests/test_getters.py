from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from bot import getters


@pytest.fixture
def mock_client():
    client = AsyncMock()
    client.get_profile = AsyncMock(return_value={"timezone": "UTC"})
    client.get_tasks = AsyncMock(return_value=[])
    client.get_categories = AsyncMock(return_value=[])
    return client


@pytest.fixture
def mock_manager(mock_client):
    manager = AsyncMock()
    manager.middleware_data = {"api_client": mock_client}
    manager.dialog_data = {}

    user = SimpleNamespace(first_name="Tester", username="tester_login")
    manager.event.from_user = user
    return manager


def test_format_user_time_success():
    """Test formatting with a valid timezone."""
    iso_date = "2025-12-17T12:00:00Z"
    tz = "Europe/Moscow"
    # 12:00 UTC + 3 hours = 15:00
    result = getters.format_user_time(iso_date, tz)
    assert result == "17.12 15:00"


def test_format_user_time_naive_datetime():
    """Test formatting a naive datetime string (no Z). Should localize to UTC first."""
    iso_date = "2025-12-17 12:00:00"
    tz = "UTC"
    result = getters.format_user_time(iso_date, tz)
    assert result == "17.12 12:00"


def test_format_user_time_invalid_tz():
    """Test fallback to default timezone on unknown timezone error."""
    iso_date = "2025-12-17T12:00:00Z"
    tz = "Mars/City"
    result = getters.format_user_time(iso_date, tz)
    assert result == "17.12 12:00"


def test_format_user_time_empty():
    """Test empty input returns empty string."""
    assert getters.format_user_time(None, "UTC") == ""
    assert getters.format_user_time("", "UTC") == ""


def test_format_user_time_parse_exception():
    """Test exception handling for unparsable strings."""
    result = getters.format_user_time("not-a-date", "UTC")
    assert result == "not-a-date"


def test_format_user_time_general_exception():
    """Test general exception handling (e.g., passing non-string that parser rejects)."""
    # parser.parse(123) raises TypeError
    result = getters.format_user_time(123, "UTC")
    assert result == 123


@pytest.mark.asyncio
async def test_get_my_tasks_full_logic(mock_manager, mock_client):
    """
    Test detailed task formatting logic:
    - Profile fetches custom timezone.
    - Task 1: Completed (Checking Checkmark).
    - Task 2: Deadline (Checking Alarm and Time conversion).
    - Task 3: No Deadline, Not Completed (Standard).
    - Edge Case: Category is not a dict.
    """
    mock_client.get_profile.return_value = {"timezone": "Europe/Berlin"}  # UTC+1

    mock_client.get_tasks.return_value = [
        {
            "id": 1,
            "title": "Done Task",
            "created_at": "2025-01-01T10:00:00Z",
            "deadline": None,
            "is_completed": True,
            "category": {"title": "Work"},
        },
        {
            "id": 2,
            "title": "Due Task",
            "created_at": "2025-01-01T10:00:00Z",
            "deadline": "2025-01-01T12:00:00Z",  # 13:00 Berlin
            "is_completed": False,
            "category": None,
        },
        {
            "id": 3,
            "title": "Simple Task",
            "created_at": "2025-01-01T10:00:00Z",
            "deadline": None,
            "is_completed": False,
            "category": "Invalid Type",
        },
    ]

    data = await getters.get_my_tasks(mock_manager)

    assert data["count"] == 3
    tasks = data["tasks"]

    assert "✅ Done Task" in tasks[0]["title"]
    assert tasks[0]["category"] == "Work"

    assert "⏰ Due Task" in tasks[1]["title"]
    assert "13:00" in tasks[1]["title"]
    assert tasks[1]["deadline"] == "01.01 13:00"

    assert tasks[2]["title"] == "Simple Task"
    assert tasks[2]["category"] == ""


@pytest.mark.asyncio
async def test_get_my_tasks_profile_fail(mock_manager, mock_client):
    """Test resilience when get_profile fails (should default to UTC)."""
    mock_client.get_profile.side_effect = Exception("DB Down")
    mock_client.get_tasks.return_value = [
        {"id": 1, "title": "T", "deadline": "2025-01-01T12:00:00Z", "is_completed": False, "category": {}}
    ]

    data = await getters.get_my_tasks(mock_manager)

    assert data["count"] == 1
    # Should use UTC because profile failed
    assert data["tasks"][0]["deadline"] == "01.01 12:00"


@pytest.mark.asyncio
async def test_get_my_tasks_api_fail(mock_manager, mock_client):
    """Test graceful handling when get_tasks API fails."""
    mock_client.get_tasks.side_effect = Exception("API Error")

    data = await getters.get_my_tasks(mock_manager)

    assert data["tasks"] == []
    assert data["count"] == 0
    assert "error" in data
    assert "API Error" in data["error"]


@pytest.mark.asyncio
async def test_get_task_data_success(mock_manager, mock_client):
    """Test successful task detail fetching."""
    mock_manager.dialog_data["selected_task_id"] = "100"

    mock_client.get_task.return_value = {
        "id": 100,
        "title": "Detail Task",
        "deadline": "2025-05-05T10:00:00Z",
        "created_at": "2025-05-01T10:00:00Z",
        "category_name": "Personal",
    }

    data = await getters.get_task_data(mock_manager)
    task = data["task"]

    assert task["title"] == "Detail Task"
    assert task["deadline_fmt"] == "05.05 10:00"
    assert task["category_name"] == "Personal"


@pytest.mark.asyncio
async def test_get_task_data_profile_fail(mock_manager, mock_client):
    """Test task data retrieval when profile fetch fails."""
    mock_manager.dialog_data["selected_task_id"] = "100"
    mock_client.get_profile.side_effect = Exception("Profile Error")

    mock_client.get_task.return_value = {"id": 100, "deadline": None, "created_at": None, "category_name": None}

    data = await getters.get_task_data(mock_manager)

    assert data["task"]["deadline_fmt"] == "No deadline"


@pytest.mark.asyncio
async def test_get_task_data_api_fail(mock_manager, mock_client):
    """Test exception handling when get_task API fails."""
    mock_client.get_task.side_effect = Exception("Task Not Found")

    data = await getters.get_task_data(mock_manager)

    assert data["task"]["title"] == "Error loading task"
    assert data["task"]["description"] == "Task Not Found"


@pytest.mark.asyncio
async def test_get_categories_success(mock_manager, mock_client):
    """Test fetching categories list."""
    mock_client.get_categories.return_value = [{"id": 1, "name": "Work"}]

    data = await getters.get_categories(mock_manager)

    assert len(data["categories"]) == 1
    assert data["categories"][0]["name"] == "Work"


@pytest.mark.asyncio
async def test_get_categories_fail(mock_manager, mock_client):
    """Test failure in fetching categories."""
    mock_client.get_categories.side_effect = Exception("Network Error")

    data = await getters.get_categories(mock_manager)

    assert data["categories"] == []


@pytest.mark.asyncio
async def test_get_category_data_success(mock_manager, mock_client):
    """Test fetching single category details."""
    mock_manager.dialog_data["selected_cat_id"] = "5"
    mock_client.get_category.return_value = {"id": 5, "name": "Hobby"}

    data = await getters.get_category_data(mock_manager)

    assert data["cat_id"] == 5
    assert data["cat_name"] == "Hobby"


@pytest.mark.asyncio
async def test_get_category_data_fail(mock_manager, mock_client):
    """Test failure in fetching single category."""
    mock_manager.dialog_data["selected_cat_id"] = "5"
    mock_client.get_category.side_effect = Exception("Category Missing")

    data = await getters.get_category_data(mock_manager)

    assert data["cat_id"] == "5"
    assert data["cat_name"] == "Error loading name"
