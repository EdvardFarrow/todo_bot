from magic_filter import F
from aiogram_dialog import Dialog, Window, StartMode
from aiogram_dialog.widgets.text import Const, Format
from aiogram_dialog.widgets.kbd import Button, Row, ScrollingGroup, Select, Start
from aiogram_dialog.widgets.input import TextInput, MessageInput
from aiogram.types import CallbackQuery, Message
from aiogram.enums import ContentType
from utils.transcriber import transcribe_voice
from utils.parser import parse_task_text
from states.state import CategorySG, MainSG, SetupSG
from getters import get_categories, get_my_tasks, get_task_data, get_category_data
from timezonefinder import TimezoneFinder


# --- HANDLERS ---

# TASKS
async def to_create_task(callback: CallbackQuery, button: Button, manager):
    """
    Switch context to the Task Creation window.
    """
    await manager.switch_to(MainSG.task_create)


async def on_task_created(message: Message, widget, manager, text: str):
    """
    Triggered when the user submits text for a new task.
    Parses deadline from text and sends request to API.
    """    
    client = manager.middleware_data.get("api_client")
    
    user_tz = "UTC"
    try:
        profile = await client.get_profile()
        user_tz = profile.get("timezone", "UTC")
    except Exception:
        pass
    
    title, deadline_dt = parse_task_text(text, user_timezone=user_tz)
    
    manager.dialog_data["temp_title"] = title
    manager.dialog_data["temp_deadline"] = deadline_dt.isoformat() if deadline_dt else None
    
    await manager.switch_to(MainSG.task_category)
    
    
async def on_task_selected(callback: CallbackQuery, widget, manager, item_id: str):
    """Click on the task in the list -> Save the ID and go to details"""
    manager.dialog_data["selected_task_id"] = item_id
    await manager.switch_to(MainSG.task_detail)


async def delete_task_handler(callback: CallbackQuery, widget, manager):
    """Delete a task"""
    client = manager.middleware_data.get("api_client")
    task_id = manager.dialog_data.get("selected_task_id")
    try:
        await client.delete_task(task_id)
        await callback.answer("🗑 Task deleted")
        await manager.switch_to(MainSG.task_list)
    except Exception as e:
        await callback.message.answer(f"Error: {e}")
        

async def toggle_complete_handler(callback: CallbackQuery, widget, manager):
    """
    Marks the selected task as completed via API and returns to the task list.
    """
    client = manager.middleware_data.get("api_client")
    task_id = manager.dialog_data.get("selected_task_id")
    try:
        # We explicitly set it to True (Mark as Done)
        await client.update_task(task_id, {"is_completed": True})
        await callback.answer("✅ Task completed!")
        await manager.switch_to(MainSG.task_list)
    except Exception as e:
        await callback.message.answer(f"Error: {e}")
        

async def on_task_edit_submit(message: Message, widget, manager, text: str):
    """Save a new task title"""
    client = manager.middleware_data.get("api_client")
    task_id = manager.dialog_data.get("selected_task_id")
    
    try:
        await client.update_task(task_id, {"title": text})
        await message.answer("✅ Title updated")
        await manager.switch_to(MainSG.task_detail)
    except Exception as e:
        await message.answer(f"Error: {e}")


# CATEGORIES

async def on_category_selected(callback: CallbackQuery, widget, manager, item_id: str):
    """Category selected -> save task"""
    client = manager.middleware_data.get("api_client")
    title = manager.dialog_data.get("temp_title")
    deadline = manager.dialog_data.get("temp_deadline")
    
    # "None" — Reserved string for category skip button
    cat_id = item_id if item_id != "None" else None
    
    try:
        await client.create_task(title=title, deadline=deadline, category_id=cat_id)
        await callback.message.answer(f"✅ Task <b>«{title}»</b> created!")
        await manager.switch_to(MainSG.task_list)
    except Exception as e:
        await callback.message.answer(f"❌ API Error: <code>{e}</code>")


async def on_category_created(message: Message, widget, manager, text: str):
    """Creates a new category via API and switches back to the category list."""
    client = manager.middleware_data.get("api_client")
    
    try:
        await client.create_category(name=text)
        await message.answer(f"📂 Category <b>«{text}»</b> created!")
        await manager.switch_to(CategorySG.list)
        
    except Exception as e:
        await message.answer(f"❌ <b>Error:</b>\n<code>{e}</code>")


async def delete_cat_handler(callback: CallbackQuery, widget, manager):
    """
    Deletes the selected category via API and returns to the category list.
    """
    client = manager.middleware_data.get("api_client")
    cat_id = manager.dialog_data.get("selected_cat_id")
    try:
        await client.delete_category(cat_id)
        await callback.answer("🗑 Category deleted")
        await manager.switch_to(CategorySG.list)
    except Exception as e:
        await callback.message.answer(f"Error: {e}")


async def on_cat_edit_submit(message: Message, widget, manager, text: str):
    """
    Updates the category name via API and returns to the category list.
    """
    client = manager.middleware_data.get("api_client")
    cat_id = manager.dialog_data.get("selected_cat_id")
    try:
        await client.update_category(cat_id, text)
        await message.answer("✅ Category renamed")
        await manager.switch_to(CategorySG.list)
    except Exception as e:
        await message.answer(f"Error: {e}")


async def on_geo_sent(message: Message, widget, manager):
    """
    Triggered when user sends their location.
    Calculates timezone and updates the backend profile.
    """
    if not message.location:
        await message.answer("❌ <b>Error:</b> No location data received.")
        return

    tf = TimezoneFinder()
    user_timezone = tf.timezone_at(lng=message.location.longitude, lat=message.location.latitude)
    
    if not user_timezone:
        await message.answer("❌ <b>Error:</b> Could not determine timezone from these coordinates.")
        return

    client = manager.middleware_data.get("api_client")
    try:
        await client.update_profile(timezone=user_timezone)
        await message.answer(f"✅ <b>Success!</b>\nTimezone set to: <code>{user_timezone}</code>")
        
        await manager.start(state=MainSG.menu)
        
    except Exception as e:
        await message.answer(f"❌ <b>API Error:</b>\n<code>{e}</code>")


async def generic_voice_handler(message: Message, widget, manager):
    """
    Universal voice processor.
    """
    text = await transcribe_voice(message.bot, message.voice.file_id)
    if not text:
        await message.answer("🤷‍♂️ The text could not be recognized.")
        return

    client = manager.middleware_data.get("api_client")
    
    current_state = manager.current_context().state

    try:
        # Create a new category
        if current_state == CategorySG.create:
            await client.create_category(name=text)
            await message.answer(f"📂 Category <b>«{text}»</b> created!")
            await manager.switch_to(CategorySG.list)

        # Edit a category name
        elif current_state == CategorySG.edit:
            cat_id = manager.dialog_data.get("selected_cat_id")
            await client.update_category(cat_id, text)
            await message.answer(f"✅ Renamed to <b>«{text}»</b>")
            await manager.switch_to(CategorySG.list)

        # Edit a task title
        elif current_state == MainSG.task_edit_title:
            task_id = manager.dialog_data.get("selected_task_id")
            await client.update_task(task_id, {"title": text})
            await message.answer(f"✅ Title updated to <b>«{text}»</b>")
            await manager.switch_to(MainSG.task_detail)
        
        # Create a new task
        elif current_state == MainSG.task_create:
            await client.create_task(title=text) 
            await message.answer(f"✅ Task <b>«{text}»</b> created!")
            await manager.switch_to(MainSG.task_list)

    except Exception as e:
        await message.answer(f"❌ Error: {e}")
    
    
async def on_cat_mgmt_selected(callback: CallbackQuery, widget, manager, item_id: str):
    """
    Handler for selecting a category in Management Mode.
    Save ID and switch to details.
    """
    manager.dialog_data["selected_cat_id"] = item_id
    
    await manager.switch_to(CategorySG.detail)


# WINDOWS

main_menu_window = Window(
    Format("👋 Hello, <b>{username}</b>!\n\nYour personal Task Tracker is ready."),
    MessageInput(
        func=generic_voice_handler,
        content_types=[ContentType.VOICE]
    ),
    Row(
        Button(Const("📋 My Tasks"), id="btn_my_tasks", on_click=lambda c, b, m: m.switch_to(MainSG.task_list)),
        Button(Const("➕ New Task"), id="btn_new_task", on_click=to_create_task),
    ),
    Row(
        Start(Const("📂 Categories"), id="btn_cats", state=CategorySG.list),
        Button(Const("⚙️ Settings"), id="btn_settings", on_click=lambda c, b, m: m.switch_to(MainSG.settings)),
    ),
    state=MainSG.menu,
    getter=get_my_tasks, # Needed to fetch the username
)


# Tasks
task_list_window = Window(
    Format("📋 <b>Your Tasks ({count}):</b>"),
    ScrollingGroup(
        Select(
            Format("{item[title]}"),                  # Text on the button
            id="select_task",
            item_id_getter=lambda x: str(x['id']),    # ID for callback
            items="tasks",                            # Key from get_my_tasks dictionary
            on_click=on_task_selected
        ),
        id="tasks_group",
        width=1,                                      # 1 column
        height=5,                                     # 5 items per page
        hide_on_single_page=True
    ),
    Row(
        Button(Const("🔙 Menu"), id="btn_back", on_click=lambda c, b, m: m.switch_to(MainSG.menu)),
        Button(Const("➕ Add"), id="btn_add_quick", on_click=to_create_task),
    ),
    state=MainSG.task_list,
    getter=get_my_tasks,
)


task_create_window = Window(
    Const("✍️ <b>Enter task title:</b>\n\n(Or click 'Cancel')"),
    TextInput(
        id="input_task_title",
        on_success=on_task_created
    ),
    MessageInput(func=generic_voice_handler, content_types=[ContentType.VOICE]),
    Button(Const("🔙 Cancel"), id="btn_cancel", on_click=lambda c, b, m: m.switch_to(MainSG.menu)),
    state=MainSG.task_create,
)


task_detail_window = Window(
    Format("📝 <b>{task[title]}</b>"),
    Format("📅 Deadline: {task[deadline_fmt]}"),
    Format("📂 Category: {task[category_name]}", when=F["task"]["category_name"]),
    Format("🕒 Created: {task[created_at_fmt]}"),
    
    Row(
        Button(Const("✅ Complete"), id="btn_complete", on_click=toggle_complete_handler),
        Button(Const("✏️ Edit Title"), id="btn_edit_task", on_click=lambda c,b,m: m.switch_to(MainSG.task_edit_title)),
    ),
    Button(Const("🗑 Delete Task"), id="btn_del_task", on_click=delete_task_handler),
    Button(Const("🔙 Back"), id="btn_back_detail", on_click=lambda c,b,m: m.switch_to(MainSG.task_list)),
    
    state=MainSG.task_detail,
    getter=get_task_data
)


task_edit_window = Window(
    Const("✍️ <b>Enter new title:</b>"),
    TextInput(id="input_edit_task", on_success=on_task_edit_submit),
    MessageInput(func=generic_voice_handler, content_types=[ContentType.VOICE]),
    Button(Const("🔙 Cancel"), id="btn_cancel_edit", on_click=lambda c,b,m: m.switch_to(MainSG.task_detail)),
    state=MainSG.task_edit_title
)


# Categories
task_category_window = Window(
    Const("📂 <b>Select a category:</b>"),
    ScrollingGroup(
        Select(
            Format("{item[name]}"),
            id="sel_category",
            item_id_getter=lambda x: str(x['id']),
            items="categories",
            on_click=on_category_selected
        ),
        id="scroll_cats",
        width=2,
        height=4
    ),
    Button(Const("🚫 Skip (No category)"), id="btn_no_cat", on_click=lambda c, w, m: on_category_selected(c, w, m, "None")),
    state=MainSG.task_category,
    getter=get_categories,
)


cat_list_window = Window(
    Const("📂 <b>Manage Categories</b>"),
    ScrollingGroup(
        Select(
            Format("{item[name]}"),
            id="cat_mgm_sel",
            item_id_getter=lambda x: str(x['id']),
            items="categories",
            on_click=on_cat_mgmt_selected
        ),
        id="cat_scroll_mgm",
        width=2, height=5
    ),
    Button(Const("➕ Create Category"), id="btn_new_cat", on_click=lambda c,b,m: m.switch_to(CategorySG.create)),
    Button(Const("🔙 Back"), id="back_cat_list", on_click=lambda c,b,m: m.start(MainSG.menu, mode=StartMode.RESET_STACK)),
    state=CategorySG.list,
    getter=get_categories,
)


cat_create_window = Window(
    Const("✍️ <b>Enter new category name:</b>"),
    TextInput(
        id="input_cat_name",
        on_success=on_category_created 
    ),
    MessageInput(func=generic_voice_handler, content_types=[ContentType.VOICE]),
    Button(Const("🔙 Cancel"), id="cancel_cat_create", on_click=lambda c,b,m: m.switch_to(CategorySG.list)),
    state=CategorySG.create,
)


cat_detail_window = Window(
    Format("📂 Category ID: {cat_id}"), 
    
    Row(
        Button(Const("✏️ Rename"), id="btn_ren_cat", on_click=lambda c,b,m: m.switch_to(CategorySG.edit)),
        Button(Const("🗑 Delete"), id="btn_del_cat", on_click=delete_cat_handler),
    ),
    Button(Const("🔙 Back"), id="btn_back_cat_det", on_click=lambda c,b,m: m.switch_to(CategorySG.list)),
    
    state=CategorySG.detail,
    getter=get_category_data
)


cat_edit_window = Window(
    Const("✍️ <b>Enter new category name:</b>"),
    TextInput(id="input_ren_cat", on_success=on_cat_edit_submit),
    MessageInput(func=generic_voice_handler, content_types=[ContentType.VOICE]),
    Button(Const("🔙 Cancel"), id="btn_cancel_ren", on_click=lambda c,b,m: m.switch_to(CategorySG.detail)),
    state=CategorySG.edit
)


# Setup
setup_window = Window(
    Const("📍 <b>Timezone Setup</b>\n\nPlease send me your <b>Location</b> (📎 Attachment -> Location) so I can detect your timezone automatically.\n\n<i>Or click Skip to use UTC.</i>"),
    MessageInput(
        func=on_geo_sent,
        content_types=[ContentType.LOCATION] 
    ),
    Row(
        Button(Const("🚫 Skip (Use UTC)"), id="btn_skip_geo", on_click=lambda c,b,m: m.start(MainSG.menu)),
    ),
    state=SetupSG.timezone,
)


settings_window = Window(
    Const("⚙️ <b>Settings</b>\n\nHere you can update your location if you moved to another time zone."),
    Row(
        Button(
            Const("📍 Update Timezone"), 
            id="btn_upd_tz", 
            on_click=lambda c, b, m: m.start(SetupSG.timezone, mode=StartMode.RESET_STACK)
        ),
    ),
    Button(Const("🔙 Back"), id="btn_back_settings", on_click=lambda c, b, m: m.switch_to(MainSG.menu)),
    state=MainSG.settings,
)


main_dialog = Dialog(
    main_menu_window,
    task_list_window,
    task_create_window,
    task_category_window,
    settings_window,
    task_detail_window,
    task_edit_window,
)

category_dialog = Dialog(
    cat_list_window,
    cat_create_window,
    cat_detail_window,
    cat_edit_window
)

setup_dialog = Dialog(
    setup_window,
)
