from aiogram.fsm.state import State, StatesGroup


class MainSG(StatesGroup):
    """
    Finite State Machine groups for Dialogs.
    """
    menu = State()                # Main menu (My Tasks, New Task)
    task_list = State()           # Viewing list of tasks
    task_create = State()         # Inputting title for new task
    task_category = State()       # Inputting title for new category
    task_detail = State()         # Task details
    task_edit_title = State()     # Edit title
    settings = State()
    
class SetupSG(StatesGroup):
    """
    States for the Onboarding Wizard.
    """
    timezone = State()            # Waiting for location/timezone input
    

class CategorySG(StatesGroup): 
    list = State()                # Viewing list of categories
    create = State()              # Create a new category
    detail = State()              # Category details
    edit = State()                # Edit category