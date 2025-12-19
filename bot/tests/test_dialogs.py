import pytest
from unittest.mock import AsyncMock, MagicMock
from bot import dialogs
from bot.states.state import MainSG, CategorySG, SetupSG

@pytest.fixture
def mock_client():
    client = AsyncMock()
    client.get_profile = AsyncMock(return_value={"timezone": "UTC"})
    client.create_task = AsyncMock()
    client.delete_task = AsyncMock()
    client.update_task = AsyncMock()
    client.create_category = AsyncMock()
    client.delete_category = AsyncMock()
    client.update_category = AsyncMock()
    client.update_profile = AsyncMock()
    return client

@pytest.fixture
def mock_manager(mock_client):
    manager = AsyncMock()
    manager.switch_to = AsyncMock()
    manager.start = AsyncMock()
    manager.current_context = MagicMock()
    manager.dialog_data = {}
    manager.middleware_data = {"api_client": mock_client}
    return manager

@pytest.fixture
def mock_message():
    message = AsyncMock()
    message.answer = AsyncMock()
    message.from_user = MagicMock(id=123, is_bot=False, first_name="Test")
    message.chat = MagicMock(id=123, type="private")
    message.location = None 
    message.voice = MagicMock(file_id="voice_123")
    return message

@pytest.fixture
def mock_callback(mock_message):
    callback = AsyncMock()
    callback.answer = AsyncMock()
    callback.message = mock_message
    return callback


@pytest.mark.asyncio
async def test_to_create_task(mock_callback, mock_manager):
    await dialogs.to_create_task(mock_callback, None, mock_manager)
    mock_manager.switch_to.assert_called_once_with(MainSG.task_create)

@pytest.mark.asyncio
async def test_on_task_created_success(mock_message, mock_manager):
    text = "Buy milk tomorrow"
    await dialogs.on_task_created(mock_message, None, mock_manager, text)
    assert mock_manager.dialog_data["temp_title"] == "Buy milk"
    assert "temp_deadline" in mock_manager.dialog_data
    mock_manager.switch_to.assert_called_once_with(MainSG.task_category)

@pytest.mark.asyncio
async def test_on_task_selected(mock_callback, mock_manager):
    item_id = "555"
    await dialogs.on_task_selected(mock_callback, None, mock_manager, item_id)
    assert mock_manager.dialog_data["selected_task_id"] == item_id
    mock_manager.switch_to.assert_called_once_with(MainSG.task_detail)

@pytest.mark.asyncio
async def test_delete_task_handler_success(mock_callback, mock_manager):
    mock_manager.dialog_data["selected_task_id"] = "10"
    client = mock_manager.middleware_data["api_client"]
    await dialogs.delete_task_handler(mock_callback, None, mock_manager)
    client.delete_task.assert_called_once_with("10")
    mock_callback.answer.assert_called_with("🗑 Task deleted")
    mock_manager.switch_to.assert_called_once_with(MainSG.task_list)

@pytest.mark.asyncio
async def test_on_category_selected_with_id(mock_callback, mock_manager):
    mock_manager.dialog_data = {"temp_title": "Test Task", "temp_deadline": None}
    client = mock_manager.middleware_data["api_client"]
    cat_id = "42"
    await dialogs.on_category_selected(mock_callback, None, mock_manager, cat_id)
    client.create_task.assert_called_once_with(
        title="Test Task", deadline=None, category_id="42"
    )
    mock_callback.message.answer.assert_called() 
    mock_manager.switch_to.assert_called_once_with(MainSG.task_list)

@pytest.mark.asyncio
async def test_on_category_selected_skip(mock_callback, mock_manager):
    mock_manager.dialog_data = {"temp_title": "Test Task", "temp_deadline": None}
    client = mock_manager.middleware_data["api_client"]
    await dialogs.on_category_selected(mock_callback, None, mock_manager, "None")
    client.create_task.assert_called_once_with(
        title="Test Task", deadline=None, category_id=None
    )
    mock_manager.switch_to.assert_called_once_with(MainSG.task_list)

@pytest.mark.asyncio
async def test_on_geo_sent_success(mock_message, mock_manager):
    mock_message.location = MagicMock(latitude=51.5, longitude=-0.12)  
    client = mock_manager.middleware_data["api_client"]
    await dialogs.on_geo_sent(mock_message, None, mock_manager)
    client.update_profile.assert_called_once()
    args, kwargs = client.update_profile.call_args
    assert kwargs['timezone'] == "Europe/London"
    mock_message.answer.assert_called()
    mock_manager.start.assert_called_once_with(state=MainSG.menu)

@pytest.mark.asyncio
async def test_on_geo_sent_no_location(mock_message, mock_manager):
    mock_message.location = None
    await dialogs.on_geo_sent(mock_message, None, mock_manager)
    mock_message.answer.assert_called()
    assert "No location data" in mock_message.answer.call_args[0][0]
    client = mock_manager.middleware_data["api_client"]
    client.update_profile.assert_not_called()
    mock_manager.start.assert_not_called()

@pytest.mark.asyncio
async def test_toggle_complete_handler_success(mock_callback, mock_manager):
    mock_manager.dialog_data["selected_task_id"] = "99"
    client = mock_manager.middleware_data["api_client"]
    await dialogs.toggle_complete_handler(mock_callback, None, mock_manager)
    client.update_task.assert_called_once_with("99", {"is_completed": True})
    mock_callback.answer.assert_called_with("✅ Task completed!")
    mock_manager.switch_to.assert_called_with(MainSG.task_list)

@pytest.mark.asyncio
async def test_on_task_edit_submit_success(mock_message, mock_manager):
    mock_manager.dialog_data["selected_task_id"] = "99"
    client = mock_manager.middleware_data["api_client"]
    new_title = "Updated Title"
    await dialogs.on_task_edit_submit(mock_message, None, mock_manager, new_title)
    client.update_task.assert_called_once_with("99", {"title": new_title})
    mock_manager.switch_to.assert_called_with(MainSG.task_detail)

@pytest.mark.asyncio
async def test_on_category_created_success(mock_message, mock_manager):
    client = mock_manager.middleware_data["api_client"]
    cat_name = "Work"
    await dialogs.on_category_created(mock_message, None, mock_manager, cat_name)
    client.create_category.assert_called_once_with(name=cat_name)
    mock_manager.switch_to.assert_called_with(CategorySG.list)

@pytest.mark.asyncio
async def test_delete_cat_handler_success(mock_callback, mock_manager):
    mock_manager.dialog_data["selected_cat_id"] = "5"
    client = mock_manager.middleware_data["api_client"]
    await dialogs.delete_cat_handler(mock_callback, None, mock_manager)
    client.delete_category.assert_called_once_with("5")
    mock_manager.switch_to.assert_called_with(CategorySG.list)

@pytest.mark.asyncio
async def test_on_cat_edit_submit_success(mock_message, mock_manager):
    mock_manager.dialog_data["selected_cat_id"] = "5"
    client = mock_manager.middleware_data["api_client"]
    new_name = "New Work"
    await dialogs.on_cat_edit_submit(mock_message, None, mock_manager, new_name)
    client.update_category.assert_called_once_with("5", new_name)
    mock_manager.switch_to.assert_called_with(CategorySG.list)

@pytest.mark.asyncio
async def test_on_task_created_profile_error(mock_message, mock_manager):
    """Ensure task parsing works even if get_profile fails."""
    client = mock_manager.middleware_data["api_client"]
    client.get_profile.side_effect = Exception("DB Error")
    
    text = "Buy milk"
    await dialogs.on_task_created(mock_message, None, mock_manager, text)
    
    assert mock_manager.dialog_data["temp_title"] == "Buy milk"
    mock_manager.switch_to.assert_called_once_with(MainSG.task_category)

@pytest.mark.asyncio
async def test_delete_task_handler_error(mock_callback, mock_manager):
    client = mock_manager.middleware_data["api_client"]
    client.delete_task.side_effect = Exception("API Error")
    
    await dialogs.delete_task_handler(mock_callback, None, mock_manager)
    
    mock_callback.message.answer.assert_called()
    assert "Error: API Error" in mock_callback.message.answer.call_args[0][0]

@pytest.mark.asyncio
async def test_toggle_complete_handler_error(mock_callback, mock_manager):
    client = mock_manager.middleware_data["api_client"]
    client.update_task.side_effect = Exception("API Error")
    
    await dialogs.toggle_complete_handler(mock_callback, None, mock_manager)
    
    mock_callback.message.answer.assert_called()
    assert "Error: API Error" in mock_callback.message.answer.call_args[0][0]

@pytest.mark.asyncio
async def test_on_task_edit_submit_error(mock_message, mock_manager):
    client = mock_manager.middleware_data["api_client"]
    client.update_task.side_effect = Exception("Fail")
    
    await dialogs.on_task_edit_submit(mock_message, None, mock_manager, "New Title")
    
    mock_message.answer.assert_called()
    assert "Error: Fail" in mock_message.answer.call_args[0][0]

@pytest.mark.asyncio
async def test_on_category_selected_error(mock_callback, mock_manager):
    mock_manager.dialog_data = {"temp_title": "T", "temp_deadline": None}
    client = mock_manager.middleware_data["api_client"]
    client.create_task.side_effect = Exception("API Fail")
    
    await dialogs.on_category_selected(mock_callback, None, mock_manager, "1")
    
    mock_callback.message.answer.assert_called()
    assert "API Error" in mock_callback.message.answer.call_args[0][0]

@pytest.mark.asyncio
async def test_on_category_created_error(mock_message, mock_manager):
    client = mock_manager.middleware_data["api_client"]
    client.create_category.side_effect = Exception("Duplicate")
    
    await dialogs.on_category_created(mock_message, None, mock_manager, "Cat")
    
    mock_message.answer.assert_called()
    assert "Error" in mock_message.answer.call_args[0][0]

@pytest.mark.asyncio
async def test_delete_cat_handler_error(mock_callback, mock_manager):
    client = mock_manager.middleware_data["api_client"]
    client.delete_category.side_effect = Exception("Fail")
    
    await dialogs.delete_cat_handler(mock_callback, None, mock_manager)
    
    mock_callback.message.answer.assert_called()
    assert "Error: Fail" in mock_callback.message.answer.call_args[0][0]

@pytest.mark.asyncio
async def test_on_cat_edit_submit_error(mock_message, mock_manager):
    client = mock_manager.middleware_data["api_client"]
    client.update_category.side_effect = Exception("Fail")
    
    await dialogs.on_cat_edit_submit(mock_message, None, mock_manager, "New Name")
    
    mock_message.answer.assert_called()
    assert "Error: Fail" in mock_message.answer.call_args[0][0]

@pytest.mark.asyncio
async def test_on_geo_sent_timezone_not_found(mock_message, mock_manager):
    """Test when TimezoneFinder returns None."""
    mock_message.location = MagicMock(latitude=0, longitude=0)
    
    with pytest.MonkeyPatch.context() as m:
        # Mock TimezoneFinder to return None
        MockTZ = MagicMock()
        MockTZ.return_value.timezone_at.return_value = None
        m.setattr("bot.dialogs.TimezoneFinder", MockTZ)
        
        await dialogs.on_geo_sent(mock_message, None, mock_manager)
        
        mock_message.answer.assert_called()
        assert "Could not determine timezone" in mock_message.answer.call_args[0][0]

@pytest.mark.asyncio
async def test_on_geo_sent_api_error(mock_message, mock_manager):
    mock_message.location = MagicMock(latitude=50, longitude=50)
    client = mock_manager.middleware_data["api_client"]
    client.update_profile.side_effect = Exception("API Down")
    
    await dialogs.on_geo_sent(mock_message, None, mock_manager)
    
    mock_message.answer.assert_called()
    assert "API Error" in mock_message.answer.call_args[0][0]

@pytest.mark.asyncio
async def test_on_cat_mgmt_selected(mock_callback, mock_manager):
    await dialogs.on_cat_mgmt_selected(mock_callback, None, mock_manager, "101")
    
    assert mock_manager.dialog_data["selected_cat_id"] == "101"
    mock_manager.switch_to.assert_called_once_with(CategorySG.detail)

# VOICE HANDLER TESTS (ALL STATES) 

@pytest.mark.asyncio
async def test_generic_voice_handler_transcribe_fail(mock_message, mock_manager):
    with pytest.MonkeyPatch.context() as m:
        async def mock_transcribe(*args): return None
        m.setattr("bot.dialogs.transcribe_voice", mock_transcribe)
        
        await dialogs.generic_voice_handler(mock_message, None, mock_manager)
        
        mock_message.answer.assert_called()
        assert "could not be recognized" in mock_message.answer.call_args[0][0]

@pytest.mark.asyncio
async def test_generic_voice_handler_create_task(mock_message, mock_manager):
    mock_context = MagicMock()
    mock_context.state = MainSG.task_create
    mock_manager.current_context = MagicMock(return_value=mock_context)
    client = mock_manager.middleware_data["api_client"]
    
    with pytest.MonkeyPatch.context() as m:
        async def mock_transcribe(*args): return "Voice Task"
        m.setattr("bot.dialogs.transcribe_voice", mock_transcribe)

        await dialogs.generic_voice_handler(mock_message, None, mock_manager)

        client.create_task.assert_called_with(title="Voice Task")
        mock_manager.switch_to.assert_called_with(MainSG.task_list)

@pytest.mark.asyncio
async def test_generic_voice_handler_create_category(mock_message, mock_manager):
    mock_context = MagicMock()
    mock_context.state = CategorySG.create
    mock_manager.current_context = MagicMock(return_value=mock_context)
    client = mock_manager.middleware_data["api_client"]
    
    with pytest.MonkeyPatch.context() as m:
        async def mock_transcribe(*args): return "Voice Cat"
        m.setattr("bot.dialogs.transcribe_voice", mock_transcribe)

        await dialogs.generic_voice_handler(mock_message, None, mock_manager)

        client.create_category.assert_called_with(name="Voice Cat")
        mock_manager.switch_to.assert_called_with(CategorySG.list)

@pytest.mark.asyncio
async def test_generic_voice_handler_edit_category(mock_message, mock_manager):
    mock_context = MagicMock()
    mock_context.state = CategorySG.edit
    mock_manager.current_context = MagicMock(return_value=mock_context)
    mock_manager.dialog_data = {"selected_cat_id": "55"}
    client = mock_manager.middleware_data["api_client"]
    
    with pytest.MonkeyPatch.context() as m:
        async def mock_transcribe(*args): return "New Voice Name"
        m.setattr("bot.dialogs.transcribe_voice", mock_transcribe)

        await dialogs.generic_voice_handler(mock_message, None, mock_manager)

        client.update_category.assert_called_with("55", "New Voice Name")
        mock_manager.switch_to.assert_called_with(CategorySG.list)

@pytest.mark.asyncio
async def test_generic_voice_handler_edit_task_title(mock_message, mock_manager):
    mock_context = MagicMock()
    mock_context.state = MainSG.task_edit_title
    mock_manager.current_context = MagicMock(return_value=mock_context)
    mock_manager.dialog_data = {"selected_task_id": "88"}
    client = mock_manager.middleware_data["api_client"]
    
    with pytest.MonkeyPatch.context() as m:
        async def mock_transcribe(*args): return "New Task Title"
        m.setattr("bot.dialogs.transcribe_voice", mock_transcribe)

        await dialogs.generic_voice_handler(mock_message, None, mock_manager)

        client.update_task.assert_called_with("88", {"title": "New Task Title"})
        mock_manager.switch_to.assert_called_with(MainSG.task_detail)

@pytest.mark.asyncio
async def test_generic_voice_handler_api_exception(mock_message, mock_manager):
    mock_context = MagicMock()
    mock_context.state = MainSG.task_create
    mock_manager.current_context = MagicMock(return_value=mock_context)
    client = mock_manager.middleware_data["api_client"]
    client.create_task.side_effect = Exception("Voice API Error")
    
    with pytest.MonkeyPatch.context() as m:
        async def mock_transcribe(*args): return "Task"
        m.setattr("bot.dialogs.transcribe_voice", mock_transcribe)

        await dialogs.generic_voice_handler(mock_message, None, mock_manager)

        mock_message.answer.assert_called()
        assert "Error: Voice API Error" in mock_message.answer.call_args[0][0]