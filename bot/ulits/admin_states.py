from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
    
class Mailing(StatesGroup):
    content = State()
    media = State()
    description = State()
    url_buttons = State()
    
    
class AddProduct(StatesGroup):
    waiting_for_category = State()
    waiting_for_new_category = State()
    waiting_for_name = State()
    waiting_for_description = State()
    waiting_for_price = State()
    waiting_for_photo = State()  # Новий стан
    waiting_for_payment_type = State()  # Новий стан для вибору типу оплати
    waiting_for_confirm = State()
    

class EditProduct(StatesGroup):
    waiting_for_name = State()
    waiting_for_description = State()
    waiting_for_price = State()
    waiting_for_payment_type = State()  # Новий стан для редагування типу оплати


class SearchSubscription(StatesGroup):
    waiting_for_query = State()