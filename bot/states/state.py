from aiogram.fsm.state import State, StatesGroup


class MainSG(StatesGroup):
    """
    Finite State Machine groups for Dialogs.
    """
    menu = State()                # Main menu (My Tasks, New Task)
    task_list = State()           # Viewing list of tasks
    task_create = State()         # Inputting title for new task
    task_category = State()       
    task_detail = State()
    settings = State()
    
class SetupSG(StatesGroup):
    """
    States for the Onboarding Wizard.
    """
    timezone = State()            # Waiting for location/timezone input
    

class CategorySG(StatesGroup): 
    list = State()
    create = State()