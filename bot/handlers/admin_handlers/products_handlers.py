from aiogram import Router, types, F
from main import bot
from ulits.filters import IsAdmin
from aiogram.fsm.context import FSMContext
from keyboards.admin_keyboards import (
    get_admin_catalog_keyboard,
    get_admin_products_keyboard,
    edit_product_keyboard,
    cancel_button,
    edit_options_keyboard,
    payment_type_keyboard,
    admin_keyboard,
)
from database.admin_db import (
    get_all_categories,
    add_new_product,
    get_max_category_id,
    get_category_type,
    delete_product_from_db,
    update_product_name,
    update_product_description,
    update_product_price,
    update_product_payment_type,
    get_product_payment_type,
)
from database.client_db import get_product_by_id
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from Content.texts import get_calendar_emoji_html, get_premium_emoji
from ulits.admin_states import AddProduct, EditProduct
from ulits.admin_functions import format_message_text
from aiogram.types import CallbackQuery
import os
from datetime import datetime
import logging


router = Router()


@router.message(IsAdmin(), F.text == "Управління товарами")
async def support(message: types.Message):
    await message.answer(
        "<b>Оберіть категорію товару для редагування</b>",
        parse_mode="HTML",
        reply_markup=get_admin_catalog_keyboard(),
    )


@router.callback_query(F.data.startswith("admincategory_"))
async def show_products(callback: types.CallbackQuery):
    catalog_id = int(callback.data.split("_")[1])
    await callback.message.edit_text(
        text="<b>Оберіть товар для редагування</b>",
        parse_mode="HTML",
        reply_markup=get_admin_products_keyboard(catalog_id),
    )


@router.callback_query(F.data.startswith("adminproduct_"))
async def show_product_info(callback: types.CallbackQuery):
    product_id = int(callback.data.split("_")[1])

    product = get_product_by_id(product_id)
    if not product:
        await callback.answer("Продукт не знайдено!", show_alert=True)
        return
    product_name, description, price, photo = product

    payment_type = get_product_payment_type(product_id)
    payment_type_text = (
        f"{get_calendar_emoji_html()} Модель підписки" if payment_type == "subscription" else f"{get_premium_emoji('card')} Одноразова оплата"
    )

    tariffs = [t.strip() for t in price.split(",")] if "," in price else [price]
    formatted_tariffs = []

    for tariff in tariffs:
        months, price_value = tariff.split("-")
        months = months.strip()
        price_value = price_value.strip()
        month_word = (
            "місяць"
            if months == "1"
            else "місяці"
            if months in ["2", "3", "4"]
            else "місяців"
        )
        formatted_tariffs.append(f"• {months} {month_word} - {price_value}₴")

    message_text = (
        f"<b>{product_name}</b>\n\n"
        f"{description}\n\n"
        f"<b>Тип оплати:</b> {payment_type_text}\n\n"
        f"<b>Тарифи:</b>\n"
        f"{chr(10).join(formatted_tariffs)}"
    )
    await callback.message.edit_text(
        text=message_text,
        reply_markup=edit_product_keyboard(product_id),
        parse_mode="HTML",
    )

    await callback.answer()


@router.callback_query(F.data == "back_to_admin_products")
async def back_to_categories(callback: types.CallbackQuery):
    await callback.message.edit_text(
        text="<b>Оберіть категорію товару для редагування:</b>",
        parse_mode="HTML",
        reply_markup=get_admin_catalog_keyboard(),
    )


@router.message(F.text == "➕ Додати товар")
async def add_product(message: types.Message, state: FSMContext):
    categories = get_all_categories()

    keyboard = []
    for category_id, category_type in categories:
        keyboard.append(
            [
                InlineKeyboardButton(
                    text=category_type,
                    callback_data=f"addproduct_category_{category_id}",
                )
            ]
        )

    keyboard.append(
        [
            InlineKeyboardButton(
                text="➕ Додати нову категорію",
                callback_data="add_new_category",
            )
        ]
    )

    await message.answer(
        "Оберіть категорію для нового товару або створіть нову:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
    )
    await state.set_state(AddProduct.waiting_for_category)


@router.callback_query(F.data == "add_new_category")
async def process_new_category(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer(
        "Введіть назву нової категорії:", reply_markup=cancel_button()
    )
    await state.set_state(AddProduct.waiting_for_new_category)


@router.message(AddProduct.waiting_for_new_category)
async def process_new_category_name(message: types.Message, state: FSMContext):
    if message.text == "❌ Скасувати" or message.text == "/start":
        await state.clear()
        await message.answer(
            "Додавання категорії скасовано, повертаю в головне меню",
            reply_markup=admin_keyboard(),
        )
        return

    new_category_id = get_max_category_id() + 1
    await state.update_data(category_id=new_category_id, product_type=message.text)
    await message.answer("Введіть назву товару:", reply_markup=cancel_button())
    await state.set_state(AddProduct.waiting_for_name)


@router.callback_query(F.data.startswith("addproduct_category_"))
async def process_category_selected(callback: types.CallbackQuery, state: FSMContext):
    if callback.data == "❌ Скасувати" or callback.data == "/start":
        await state.clear()
        await callback.message.answer(
            "Додавання категорії скасовано, повертаю в головне меню",
            reply_markup=admin_keyboard(),
        )
        return

    category_id = int(callback.data.split("_")[2])
    categories = get_all_categories()
    category_type = next((type_ for id_, type_ in categories if id_ == category_id), None)

    await state.update_data(category_id=category_id, product_type=category_type)
    await callback.message.answer(
        "Введіть назву товару:", reply_markup=cancel_button()
    )
    await state.set_state(AddProduct.waiting_for_name)


@router.message(AddProduct.waiting_for_name)
async def process_name(message: types.Message, state: FSMContext):
    if message.text == "❌ Скасувати" or message.text == "/start":
        await state.clear()
        await message.answer(
            "Додавання товару скасовано, повертаю в головне меню",
            reply_markup=admin_keyboard(),
        )
        return

    product_name = format_message_text(message) or message.text or ""
    await state.update_data(product_name=product_name)
    await message.answer("Введіть опис товару:")
    await state.set_state(AddProduct.waiting_for_description)


@router.message(AddProduct.waiting_for_description)
async def process_description(message: types.Message, state: FSMContext):
    if message.text == "❌ Скасувати" or message.text == "/start":
        await state.clear()
        await message.answer(
            "Додавання товару скасовано, повертаю в головне меню",
            reply_markup=admin_keyboard(),
        )
        return

    description = format_message_text(message) or message.text or ""
    await state.update_data(description=description)
    await message.answer(
        "Введіть тарифи у форматі:\n"
        "<code>1 - 150, 3 - 400, 12 - 1100</code>\n\n"
        "Де перше число - кількість місяців, друге - ціна.\n"
        "Якщо кілька тарифів - розділяйте їх комою.",
        parse_mode="HTML",
    )
    await state.set_state(AddProduct.waiting_for_price)


@router.message(AddProduct.waiting_for_price)
async def process_price(message: types.Message, state: FSMContext):
    if message.text == "❌ Скасувати" or message.text == "/start":
        await state.clear()
        await message.answer(
            "Додавання товару скасовано, повертаю в головне меню",
            reply_markup=admin_keyboard(),
        )
        return

    try:
        tariffs = message.text.split(",")
        for tariff in tariffs:
            months, price = tariff.strip().split("-")
            months = int(months.strip())
            price = float(price.strip())
    except Exception:
        await message.answer(
            "Неправильний формат тарифів. Спробуйте ще раз.\n"
            "Приклад: <code>1 - 150, 3 - 400, 12 - 1100</code>",
            parse_mode="HTML",
        )
        return

    await state.update_data(price=message.text)
    await message.answer("Надішліть фото товару:", reply_markup=cancel_button())
    await state.set_state(AddProduct.waiting_for_photo)


@router.message(AddProduct.waiting_for_photo, F.photo)
async def process_photo(message: types.Message, state: FSMContext):
    photo = message.photo[-1]
    await state.update_data(photo_id=photo.file_id)

    await message.answer(
        "Оберіть тип оплати для товару:",
        reply_markup=payment_type_keyboard(),
    )
    await state.set_state(AddProduct.waiting_for_payment_type)


@router.callback_query(
    AddProduct.waiting_for_payment_type, F.data.startswith("payment_type_")
)
async def process_payment_type(callback: types.CallbackQuery, state: FSMContext):
    payment_type = callback.data.split("_")[2]

    await state.update_data(payment_type=payment_type)

    data = await state.get_data()

    payment_type_text = (
        "📅 Модель підписки"
        if payment_type == "subscription"
        else f"{get_premium_emoji('card')} Одноразова оплата"
    )

    preview_message = (
        f"<b>Попередній перегляд товару:</b>\n\n"
        f"<b>Категорія:</b> {data['product_type']}\n"
        f"<b>Назва:</b> {data['product_name']}\n"
        f"<b>Опис:</b> {data['description']}\n"
        f"<b>Тип оплати:</b> {payment_type_text}\n\n"
        f"<b>Тарифи:</b>"
    )

    keyboard = []
    tariffs = data["price"].split(",")
    for tariff in tariffs:
        months, price = tariff.strip().split("-")
        keyboard.append(
            [
                InlineKeyboardButton(
                    text=f"{months.strip()} місяців - {price.strip()}₴",
                    callback_data="preview_tariff",
                )
            ]
        )
    keyboard.append(
        [
            InlineKeyboardButton(
                text="✅ Підтвердити", callback_data="confirm_product"
            ),
            InlineKeyboardButton(
                text="❌ Відхилити", callback_data="cancel_product"
            ),
        ]
    )

    await callback.message.answer_photo(
        photo=data["photo_id"],
        caption=preview_message,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
        parse_mode="HTML",
    )
    await state.set_state(AddProduct.waiting_for_confirm)
    await callback.answer()


@router.callback_query(
    AddProduct.waiting_for_payment_type, F.data == "cancel_payment_type"
)
async def cancel_payment_type(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("❌ Додавання товару скасовано")
    await callback.message.answer(
        "Головне меню", reply_markup=admin_keyboard()
    )
    await callback.answer()


@router.callback_query(AddProduct.waiting_for_confirm, F.data == "confirm_product")
async def confirm_product(callback: types.CallbackQuery, state: FSMContext):
    if callback.data == "❌ Скасувати" or callback.data == "/start":
        await state.clear()
        await callback.message.answer(
            "Додавання товару скасовано, повертаю в головне меню",
            reply_markup=admin_keyboard(),
        )
        return

    data = await state.get_data()

    try:
        from config import CONTENT_PRODUCTS_DIR
        if not os.path.exists(CONTENT_PRODUCTS_DIR):
            os.makedirs(CONTENT_PRODUCTS_DIR)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_name_local = os.path.join(CONTENT_PRODUCTS_DIR, f"product_{timestamp}.jpg")
        file_name_for_db = f"Content/products/product_{timestamp}.jpg"

        await bot.download(data["photo_id"], destination=file_name_local)

        result = add_new_product(
            category_id=data["category_id"],
            product_type=data["product_type"],
            name=data["product_name"],
            description=data["description"],
            price=data["price"],
            photo_path=file_name_for_db,
            payment_type=data.get("payment_type", "subscription"),
        )

        if result:
            await callback.message.edit_caption(
                caption=f"{get_premium_emoji('check')} Товар успішно додано!",
                parse_mode="HTML",
                reply_markup=None,
            )
            await callback.message.answer(
                "Головне меню", reply_markup=admin_keyboard()
            )
        else:
            if os.path.exists(file_name_local):
                os.remove(file_name_local)

            await callback.message.edit_caption(
                caption="❌ Помилка при додаванні товару. Спробуйте ще раз.",
                reply_markup=None,
            )
            await callback.message.answer(
                "Головне меню", reply_markup=admin_keyboard()
            )

    except Exception as e:
        logging.error(f"Помилка при збереженні товару: {e}")
        await callback.message.edit_caption(
            caption="❌ Помилка при збереженні товару. Спробуйте ще раз.",
            reply_markup=None,
        )
        await callback.message.answer(
            "Головне меню", reply_markup=admin_keyboard()
        )

    await state.clear()
    await callback.answer()


@router.callback_query(AddProduct.waiting_for_confirm, F.data == "cancel_product")
async def cancel_product(callback: types.CallbackQuery, state: FSMContext):
    if callback.data == "❌ Скасувати" or callback.data == "/start":
        await state.clear()
        await callback.message.answer(
            "Додавання товару скасовано, повертаю в головне меню",
            reply_markup=admin_keyboard(),
        )
        return

    await callback.message.edit_text("❌ Додавання товару скасовано")
    await callback.message.answer(
        "Головне меню", reply_markup=admin_keyboard()
    )
    await state.clear()
    await callback.answer()


@router.callback_query(F.data.startswith("delete_product_"))
async def confirm_delete_product(callback: CallbackQuery):
    product_id = int(callback.data.split("_")[2])
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Так, видалити",
                    callback_data=f"confirm_delete_{product_id}",
                ),
                InlineKeyboardButton(
                    text="❌ Ні, залишити",
                    callback_data=f"cancel_delete_{product_id}",
                ),
            ]
        ]
    )

    await callback.message.edit_text(
        "❗️ Ви впевнені, що хочете видалити цей товар?",
        reply_markup=keyboard,
    )


@router.callback_query(F.data.startswith("confirm_delete_"))
async def delete_product(callback: CallbackQuery):
    product_id = int(callback.data.split("_")[2])

    if delete_product_from_db(product_id):
        await callback.message.edit_text(
            f"{get_premium_emoji('check')} Товар успішно видалено!",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="← Назад до товарів",
                            callback_data="back_to_admin_products",
                        )
                    ]
                ]
            ),
        )
    else:
        await callback.message.edit_text(
            "❌ Помилка при видаленні товару!",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="← Назад до товарів",
                            callback_data="back_to_admin_products",
                        )
                    ]
                ]
            ),
        )


@router.callback_query(F.data.startswith("cancel_delete_"))
async def cancel_delete_product(callback: CallbackQuery):
    product_id = int(callback.data.split("_")[2])

    product = get_product_by_id(product_id)
    if not product:
        await callback.message.edit_text("❌ Помилка: товар не знайдено")
        return

    product_name, description, price, photo = product

    payment_type = get_product_payment_type(product_id)
    payment_type_text = (
        "📅 Модель підписки"
        if payment_type == "subscription"
        else f"{get_premium_emoji('card')} Одноразова оплата"
    )

    tariffs = [t.strip() for t in price.split(",")] if "," in price else [price]
    formatted_tariffs = []

    for tariff in tariffs:
        months, price_value = tariff.split("-")
        months = months.strip()
        price_value = price_value.strip()
        month_word = (
            "місяць"
            if months == "1"
            else "місяці"
            if months in ["2", "3", "4"]
            else "місяців"
        )
        formatted_tariffs.append(f"• {months} {month_word} - {price_value}₴")

    message_text = (
        f"<b>{product_name}</b>\n\n"
        f"{description}\n\n"
        f"<b>Тип оплати:</b> {payment_type_text}\n\n"
        f"<b>Тарифи:</b>\n"
        f"{chr(10).join(formatted_tariffs)}"
    )

    await callback.message.edit_text(
        text=message_text,
        reply_markup=edit_product_keyboard(product_id),
        parse_mode="HTML",
    )


@router.callback_query(F.data.startswith("edit_product_"))
async def show_edit_options(callback: CallbackQuery):
    product_id = int(callback.data.split("_")[2])

    product = get_product_by_id(product_id)
    if not product:
        await callback.message.edit_text("❌ Помилка: товар не знайдено")
        return

    product_name, description, price, photo = product

    payment_type = get_product_payment_type(product_id)
    payment_type_text = (
        "📅 Модель підписки"
        if payment_type == "subscription"
        else f"{get_premium_emoji('card')} Одноразова оплата"
    )

    tariffs = [t.strip() for t in price.split(",")] if "," in price else [price]
    formatted_tariffs = []

    for tariff in tariffs:
        months, price_value = tariff.split("-")
        months = months.strip()
        price_value = price_value.strip()
        month_word = (
            "місяць"
            if months == "1"
            else "місяці"
            if months in ["2", "3", "4"]
            else "місяців"
        )
        formatted_tariffs.append(f"• {months} {month_word} - {price_value}₴")

    message_text = (
        f"<b>{product_name}</b>\n\n"
        f"{description}\n\n"
        f"<b>Тип оплати:</b> {payment_type_text}\n\n"
        f"<b>Тарифи:</b>\n"
        f"{chr(10).join(formatted_tariffs)}\n\n"
        f"<i>Оберіть, що хочете відредагувати:</i>"
    )

    await callback.message.edit_text(
        text=message_text,
        reply_markup=edit_options_keyboard(product_id),
        parse_mode="HTML",
    )


@router.callback_query(F.data.startswith("back_to_product_"))
async def back_to_product(callback: CallbackQuery):
    product_id = int(callback.data.split("_")[3])

    product = get_product_by_id(product_id)
    if not product:
        await callback.message.edit_text("❌ Помилка: товар не знайдено")
        return

    product_name, description, price, photo = product

    payment_type = get_product_payment_type(product_id)
    payment_type_text = (
        "📅 Модель підписки"
        if payment_type == "subscription"
        else f"{get_premium_emoji('card')} Одноразова оплата"
    )

    tariffs = [t.strip() for t in price.split(",")] if "," in price else [price]
    formatted_tariffs = []

    for tariff in tariffs:
        months, price_value = tariff.split("-")
        months = months.strip()
        price_value = price_value.strip()
        month_word = (
            "місяць"
            if months == "1"
            else "місяці"
            if months in ["2", "3", "4"]
            else "місяців"
        )
        formatted_tariffs.append(f"• {months} {month_word} - {price_value}₴")

    message_text = (
        f"<b>{product_name}</b>\n\n"
        f"{description}\n\n"
        f"<b>Тип оплати:</b> {payment_type_text}\n\n"
        f"<b>Тарифи:</b>\n"
        f"{chr(10).join(formatted_tariffs)}"
    )

    await callback.message.edit_text(
        text=message_text,
        reply_markup=edit_product_keyboard(product_id),
        parse_mode="HTML",
    )


@router.callback_query(F.data.startswith("edit_name_"))
async def start_edit_name(callback: CallbackQuery, state: FSMContext):
    product_id = int(callback.data.split("_")[2])
    await state.update_data(product_id=product_id)

    await callback.message.answer(
        "Введіть нову назву товару:",
        reply_markup=cancel_button(),
    )
    await state.set_state(EditProduct.waiting_for_name)


@router.callback_query(F.data.startswith("edit_description_"))
async def start_edit_description(callback: CallbackQuery, state: FSMContext):
    product_id = int(callback.data.split("_")[2])
    await state.update_data(product_id=product_id)

    await callback.message.answer(
        "Введіть новий опис товару:",
        reply_markup=cancel_button(),
    )
    await state.set_state(EditProduct.waiting_for_description)


@router.callback_query(F.data.startswith("edit_price_"))
async def start_edit_price(callback: CallbackQuery, state: FSMContext):
    product_id = int(callback.data.split("_")[2])
    await state.update_data(product_id=product_id)

    await callback.message.answer(
        "Введіть нові тарифи у форматі:\n"
        "<code>1 - 150, 3 - 400, 12 - 1100</code>\n\n"
        "Де перше число - кількість місяців, друге - ціна.\n"
        "Якщо кілька тарифів - розділяйте їх комою.",
        parse_mode="HTML",
        reply_markup=cancel_button(),
    )
    await state.set_state(EditProduct.waiting_for_price)


@router.callback_query(F.data.startswith("edit_payment_type_"))
async def start_edit_payment_type(callback: CallbackQuery, state: FSMContext):
    product_id = int(callback.data.split("_")[3])
    await state.update_data(product_id=product_id)

    current_payment_type = get_product_payment_type(product_id)
    payment_type_text = (
        "📅 Модель підписки"
        if current_payment_type == "subscription"
        else f"{get_premium_emoji('card')} Одноразова оплата"
    )

    await callback.message.answer(
        f"Поточний тип оплати: {payment_type_text}\n\n"
        "Оберіть новий тип оплати:",
        reply_markup=payment_type_keyboard(),
    )
    await state.set_state(EditProduct.waiting_for_payment_type)


@router.message(EditProduct.waiting_for_name)
async def process_new_name(message: types.Message, state: FSMContext):
    if message.text == "❌ Скасувати" or message.text == "/start":
        await state.clear()
        await message.answer(
            "Оновлення назви скасовано, повертаю в головне меню",
            reply_markup=admin_keyboard(),
        )
        return

    data = await state.get_data()
    product_id = data["product_id"]

    new_name = format_message_text(message) or message.text or ""
    if update_product_name(product_id, new_name):
        await show_updated_product(message, product_id)
    else:
        await message.answer("❌ Помилка при оновленні назви!")

    await state.clear()


@router.message(EditProduct.waiting_for_description)
async def process_new_description(message: types.Message, state: FSMContext):
    if message.text == "❌ Скасувати" or message.text == "/start":
        await state.clear()
        await message.answer(
            "Оновлення опису скасовано, повертаю в головне меню",
            reply_markup=admin_keyboard(),
        )
        return

    data = await state.get_data()
    product_id = data["product_id"]

    new_description = format_message_text(message) or message.text or ""
    if update_product_description(product_id, new_description):
        await show_updated_product(message, product_id)
    else:
        await message.answer("❌ Помилка при оновленні опису!")

    await state.clear()


@router.message(EditProduct.waiting_for_price)
async def process_new_price(message: types.Message, state: FSMContext):
    if message.text == "❌ Скасувати" or message.text == "/start":
        await state.clear()
        await message.answer(
            "Оновлення тарифів скасовано, повертаю в головне меню",
            reply_markup=admin_keyboard(),
        )
        return

    data = await state.get_data()
    product_id = data["product_id"]

    try:
        tariffs = message.text.split(",")
        for tariff in tariffs:
            months, price = tariff.strip().split("-")
            months = int(months.strip())
            price = float(price.strip())
    except Exception:
        await message.answer(
            "Неправильний формат тарифів. Спробуйте ще раз.\n"
            "Приклад: <code>1 - 150, 3 - 400, 12 - 1100</code>",
            parse_mode="HTML",
        )
        return

    if update_product_price(product_id, message.text):
        await show_updated_product(message, product_id)
    else:
        await message.answer("❌ Помилка при оновленні тарифів!")

    await state.clear()


@router.callback_query(
    EditProduct.waiting_for_payment_type, F.data.startswith("payment_type_")
)
async def process_edit_payment_type(callback: types.CallbackQuery, state: FSMContext):
    payment_type = callback.data.split("_")[2]

    data = await state.get_data()
    product_id = data["product_id"]

    if update_product_payment_type(product_id, payment_type):
        await show_updated_product(callback.message, product_id)
    else:
        await callback.message.answer("❌ Помилка при оновленні типу оплати!")

    await state.clear()
    await callback.answer()


@router.callback_query(
    EditProduct.waiting_for_payment_type, F.data == "cancel_payment_type"
)
async def cancel_edit_payment_type(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    product_id = data["product_id"]

    await show_updated_product(callback.message, product_id)
    await state.clear()
    await callback.answer()


async def show_updated_product(message: types.Message, product_id: int):
    product = get_product_by_id(product_id)
    if not product:
        await message.answer("❌ Помилка: товар не знайдено")
        return

    product_name, description, price, photo = product

    payment_type = get_product_payment_type(product_id)
    payment_type_text = (
        "📅 Модель підписки"
        if payment_type == "subscription"
        else f"{get_premium_emoji('card')} Одноразова оплата"
    )

    tariffs = [t.strip() for t in price.split(",")] if "," in price else [price]
    formatted_tariffs = []

    for tariff in tariffs:
        months, price_value = tariff.split("-")
        months = months.strip()
        price_value = price_value.strip()
        month_word = (
            "місяць"
            if months == "1"
            else "місяці"
            if months in ["2", "3", "4"]
            else "місяців"
        )
        formatted_tariffs.append(f"• {months} {month_word} - {price_value}₴")

    message_text = (
        f"<b>{product_name}</b>\n\n"
        f"{description}\n\n"
        f"<b>Тип оплати:</b> {payment_type_text}\n\n"
        f"<b>Тарифи:</b>\n"
        f"{chr(10).join(formatted_tariffs)}"
    )

    await message.answer(
        text="Дані успішно оновлено!",
        reply_markup=admin_keyboard(),
    )

    await message.answer(
        text=message_text,
        reply_markup=edit_product_keyboard(product_id),
        parse_mode="HTML",
    )
