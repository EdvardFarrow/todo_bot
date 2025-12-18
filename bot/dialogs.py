from aiogram_dialog import Dialog, Window, StartMode
from aiogram_dialog.widgets.text import Const, Format
from aiogram_dialog.widgets.kbd import Button, Row, ScrollingGroup, Select, Start
from aiogram_dialog.widgets.input import TextInput, MessageInput
from aiogram.types import CallbackQuery, Message
from aiogram.enums import ContentType
from utils.parser import parse_task_text
from states.state import CategorySG, MainSG, SetupSG
from getters import get_categories, get_my_tasks
from timezonefinder import TimezoneFinder


# Handlers
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
    client = manager.middleware_data.get("api_client")
    
    try:
        await client.create_category(name=text)
        await message.answer(f"📂 Category <b>«{text}»</b> created!")
        await manager.switch_to(CategorySG.list)
        
    except Exception as e:
        await message.answer(f"❌ <b>Error:</b>\n<code>{e}</code>")


async def on_task_selected(callback: CallbackQuery, widget, manager, item_id: str):
    """
    Placeholder handler for clicking on a specific task in the list.
    Future implementation: Open task details window.
    """
    await callback.answer(f"Selected task ID: {item_id}")
    # await manager.switch_to(MainSG.task_detail)
    
    
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


main_menu_window = Window(
    Format("👋 Hello, <b>{username}</b>!\n\nYour personal Task Tracker is ready."),
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
    Button(Const("🔙 Cancel"), id="btn_cancel", on_click=lambda c, b, m: m.switch_to(MainSG.menu)),
    state=MainSG.task_create,
)


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
            on_click=lambda c,w,m,id: c.answer(f"Cat ID: {id}")
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
    Button(Const("🔙 Cancel"), id="cancel_cat_create", on_click=lambda c,b,m: m.switch_to(CategorySG.list)),
    state=CategorySG.create,
)


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
)

category_dialog = Dialog(
    cat_list_window,
    cat_create_window, 
)

setup_dialog = Dialog(
    setup_window,
)
