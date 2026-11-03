from datetime import datetime

from aiogram import F, Router, types
from aiogram.fsm.context import FSMContext

from database.client_db import get_product_full
from database.promo_db import (
    create_promo_code,
    delete_promo,
    get_all_promos,
    get_promo_by_id,
    get_promo_stats_text,
    promo_status,
)
from keyboards.admin_keyboards import (
    admin_keyboard,
    cancel_button,
    get_promo_code_input_keyboard,
    get_promo_create_type_keyboard,
    get_promo_delete_confirm_keyboard,
    get_promo_expiry_keyboard,
    get_promo_free_months_keyboard,
    get_promo_max_uses_keyboard,
    get_promo_products_keyboard,
    get_promo_usage_keyboard,
    get_promo_view_keyboard,
    get_promos_keyboard,
)
from ulits.admin_states import PromoStates
from ulits.filters import IsAdmin

router = Router()


def _promos_list_text() -> str:
    return (
        "<b>🎟 Промокоди</b>\n\n"
        "• <b>Безкоштовний доступ</b> — одноразовий і лише на вибраний товар.\n"
        "• <b>Знижка у %</b> — одноразовий або багаторазовий."
    )


async def _show_promos_list(message: types.Message, *, edit: bool = False):
    promos = get_all_promos()
    text = _promos_list_text()
    markup = get_promos_keyboard(promos)
    if edit:
        await message.edit_text(text, parse_mode="HTML", reply_markup=markup)
    else:
        await message.answer(text, parse_mode="HTML", reply_markup=markup)


@router.message(IsAdmin(), F.text == "Промокоди")
async def manage_promos(message: types.Message, state: FSMContext):
    await state.clear()
    await _show_promos_list(message)


@router.callback_query(IsAdmin(), F.data == "promo_back_list")
async def promo_back_list(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await _show_promos_list(callback.message, edit=True)
    await callback.answer()


@router.callback_query(IsAdmin(), F.data.startswith("promo_view_"))
async def promo_view(callback: types.CallbackQuery):
    promo_id = int(callback.data.split("_")[-1])
    promo = get_promo_by_id(promo_id)
    if not promo:
        await callback.answer("Промокод не знайдено", show_alert=True)
        return
    can_delete = promo_status(promo) != "used"
    await callback.message.edit_text(
        get_promo_stats_text(promo),
        parse_mode="HTML",
        reply_markup=get_promo_view_keyboard(promo_id, can_delete=can_delete),
    )
    await callback.answer()


@router.callback_query(IsAdmin(), F.data.startswith("promo_delete_"))
async def promo_delete_ask(callback: types.CallbackQuery):
    promo_id = int(callback.data.split("_")[-1])
    await callback.message.edit_text(
        "❗️ Видалити цей промокод?\nЦю дію неможливо відмінити.",
        reply_markup=get_promo_delete_confirm_keyboard(promo_id),
    )
    await callback.answer()


@router.callback_query(IsAdmin(), F.data.startswith("promo_confirm_delete_"))
async def promo_delete_confirm(callback: types.CallbackQuery):
    promo_id = int(callback.data.split("_")[-1])
    promo = get_promo_by_id(promo_id)
    if promo and promo_status(promo) == "used":
        await callback.answer("Не можна видалити використаний промокод", show_alert=True)
        return
    try:
        delete_promo(promo_id)
    except ValueError as exc:
        await callback.answer(str(exc), show_alert=True)
        return
    await _show_promos_list(callback.message, edit=True)
    await callback.answer("Видалено")


@router.callback_query(IsAdmin(), F.data == "promo_create")
async def promo_create_start(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(
        "<b>Створення промокоду</b>\n\nОберіть тип:",
        parse_mode="HTML",
        reply_markup=get_promo_create_type_keyboard(),
    )
    await callback.answer()


@router.callback_query(IsAdmin(), F.data == "promo_type_percent")
async def promo_type_percent(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(PromoStates.waiting_for_percent)
    await state.update_data(promo_type="percent", product_id=None, max_uses=1)
    await callback.message.answer(
        "Введіть розмір знижки у % (від 1 до 100):",
        reply_markup=cancel_button(),
    )
    await callback.answer()


def _is_cancel(text: str | None) -> bool:
    return (text or "").strip() in ("Скасувати", "❌ Скасувати")


@router.message(IsAdmin(), PromoStates.waiting_for_percent)
async def promo_percent_input(message: types.Message, state: FSMContext):
    if _is_cancel(message.text):
        await state.clear()
        await message.answer("Відміна", reply_markup=admin_keyboard())
        await _show_promos_list(message)
        return
    try:
        value = float((message.text or "").replace(",", ".").strip())
    except ValueError:
        await message.answer("Введіть число від 1 до 100:")
        return
    if not (1 <= value <= 100):
        await message.answer("Знижка має бути від 1 до 100%:")
        return
    await state.update_data(discount_percent=value, promo_type="percent")
    await message.answer(
        f"Знижка: <b>{value:.0f}%</b>\n\nСкільки разів можна використати код?",
        parse_mode="HTML",
        reply_markup=get_promo_usage_keyboard(),
    )


@router.callback_query(IsAdmin(), F.data == "promo_usage_once")
async def promo_usage_once(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(max_uses=1)
    await callback.message.edit_text(
        "Використання: <b>одноразовий</b>\n\nОберіть термін дії:",
        parse_mode="HTML",
        reply_markup=get_promo_expiry_keyboard(),
    )
    await callback.answer()


@router.callback_query(IsAdmin(), F.data == "promo_usage_multi")
async def promo_usage_multi(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "Багаторазовий код.\nОберіть ліміт використань:",
        reply_markup=get_promo_max_uses_keyboard(),
    )
    await callback.answer()


@router.callback_query(IsAdmin(), F.data.startswith("promo_max_"))
async def promo_max_uses_pick(callback: types.CallbackQuery, state: FSMContext):
    suffix = callback.data.replace("promo_max_", "", 1)
    if suffix == "custom":
        await state.set_state(PromoStates.waiting_for_max_uses)
        await callback.message.answer(
            "Введіть максимальну кількість використань (число ≥ 2):",
            reply_markup=cancel_button(),
        )
        await callback.answer()
        return
    try:
        max_uses = int(suffix)
    except ValueError:
        await callback.answer("Невірне значення", show_alert=True)
        return
    if max_uses < 0:
        await callback.answer("Невірне значення", show_alert=True)
        return
    await state.update_data(max_uses=max_uses)
    label = "без ліміту" if max_uses == 0 else f"до {max_uses} разів"
    await callback.message.edit_text(
        f"Використання: <b>{label}</b>\n\nОберіть термін дії:",
        parse_mode="HTML",
        reply_markup=get_promo_expiry_keyboard(),
    )
    await callback.answer()


@router.message(IsAdmin(), PromoStates.waiting_for_max_uses)
async def promo_max_uses_input(message: types.Message, state: FSMContext):
    if _is_cancel(message.text):
        await state.clear()
        await message.answer("Відміна", reply_markup=admin_keyboard())
        await _show_promos_list(message)
        return
    try:
        value = int((message.text or "").strip())
    except ValueError:
        await message.answer("Введіть ціле число ≥ 2:")
        return
    if value < 2:
        await message.answer("Для багаторазового коду мінімум 2:")
        return
    await state.update_data(max_uses=value)
    await message.answer(
        f"Використання: <b>до {value} разів</b>\n\nОберіть термін дії:",
        parse_mode="HTML",
        reply_markup=get_promo_expiry_keyboard(),
    )


@router.callback_query(IsAdmin(), F.data == "promo_type_free")
async def promo_type_free(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(promo_type="free", max_uses=1, product_id=None)
    await callback.message.edit_text(
        "<b>Безкоштовний доступ</b>\n\nОберіть період:",
        parse_mode="HTML",
        reply_markup=get_promo_free_months_keyboard(),
    )
    await callback.answer()


@router.callback_query(IsAdmin(), F.data.startswith("promo_free_"))
async def promo_free_months(callback: types.CallbackQuery, state: FSMContext):
    months = int(callback.data.split("_")[-1])
    if months not in (1, 3, 6, 12):
        await callback.answer("Невірний період", show_alert=True)
        return
    await state.update_data(promo_type="free", free_months=months, max_uses=1)
    await callback.message.edit_text(
        f"Період: <b>{months} міс.</b>\n\nОберіть товар для цього промокоду:",
        parse_mode="HTML",
        reply_markup=get_promo_products_keyboard(0),
    )
    await callback.answer()


@router.callback_query(IsAdmin(), F.data.startswith("promo_prodpage_"))
async def promo_product_page(callback: types.CallbackQuery, state: FSMContext):
    page = int(callback.data.split("_")[-1])
    data = await state.get_data()
    months = data.get("free_months") or "?"
    await callback.message.edit_text(
        f"Період: <b>{months} міс.</b>\n\nОберіть товар для цього промокоду:",
        parse_mode="HTML",
        reply_markup=get_promo_products_keyboard(page),
    )
    await callback.answer()


@router.callback_query(IsAdmin(), F.data.startswith("promo_pickprod_"))
async def promo_product_pick(callback: types.CallbackQuery, state: FSMContext):
    product_id = int(callback.data.split("_")[-1])
    product = get_product_full(product_id)
    if not product:
        await callback.answer("Товар не знайдено", show_alert=True)
        return
    await state.update_data(product_id=product_id)
    name = product.get("product_name") or f"#{product_id}"
    await callback.message.edit_text(
        f"Товар: <b>{name}</b>\n\nОберіть термін дії промокоду:",
        parse_mode="HTML",
        reply_markup=get_promo_expiry_keyboard(),
    )
    await callback.answer()


@router.callback_query(IsAdmin(), F.data == "promo_expiry_none")
async def promo_expiry_none(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(expires_at=None)
    await callback.message.edit_text(
        "Термін: <b>безстроковий</b>\n\nЯк створити код?",
        parse_mode="HTML",
        reply_markup=get_promo_code_input_keyboard(),
    )
    await callback.answer()


@router.callback_query(IsAdmin(), F.data == "promo_expiry_date")
async def promo_expiry_date_ask(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(PromoStates.waiting_for_expiry_date)
    await callback.message.answer(
        "Введіть дату закінчення у форматі <b>ДД.ММ.РРРР</b>\nНаприклад: <code>31.12.2026</code>",
        parse_mode="HTML",
        reply_markup=cancel_button(),
    )
    await callback.answer()


@router.message(IsAdmin(), PromoStates.waiting_for_expiry_date)
async def promo_expiry_date_input(message: types.Message, state: FSMContext):
    if _is_cancel(message.text):
        await state.clear()
        await message.answer("Відміна", reply_markup=admin_keyboard())
        await _show_promos_list(message)
        return
    raw = (message.text or "").strip()
    try:
        dt = datetime.strptime(raw, "%d.%m.%Y")
    except ValueError:
        await message.answer("Невірний формат. Введіть дату як ДД.ММ.РРРР:")
        return
    expires_at = dt.strftime("%Y-%m-%d")
    await state.update_data(expires_at=expires_at)
    await message.answer(
        f"Термін до: <b>{raw}</b>\n\nЯк створити код?",
        parse_mode="HTML",
        reply_markup=get_promo_code_input_keyboard(),
    )


@router.callback_query(IsAdmin(), F.data == "promo_code_auto")
async def promo_code_auto(callback: types.CallbackQuery, state: FSMContext):
    await _finalize_promo_create(callback, state, code=None)


@router.callback_query(IsAdmin(), F.data == "promo_code_custom")
async def promo_code_custom_ask(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(PromoStates.waiting_for_custom_code)
    await callback.message.answer(
        "Введіть свій код (латиниця/цифри, без пробілів):",
        reply_markup=cancel_button(),
    )
    await callback.answer()


@router.message(IsAdmin(), PromoStates.waiting_for_custom_code)
async def promo_code_custom_input(message: types.Message, state: FSMContext):
    if _is_cancel(message.text):
        await state.clear()
        await message.answer("Відміна", reply_markup=admin_keyboard())
        await _show_promos_list(message)
        return
    code = (message.text or "").strip().upper()
    if not code or " " in code or len(code) > 32:
        await message.answer("Код має бути без пробілів і до 32 символів:")
        return
    try:
        promo = await _create_from_state(state, code=code, created_by=message.from_user.id)
    except ValueError as exc:
        await message.answer(f"❌ {exc}\nСпробуйте інший код:")
        return
    await state.clear()
    await message.answer("✅ Промокод створено!", reply_markup=admin_keyboard())
    await message.answer(
        get_promo_stats_text(promo),
        parse_mode="HTML",
        reply_markup=get_promos_keyboard(get_all_promos()),
    )


async def _finalize_promo_create(callback: types.CallbackQuery, state: FSMContext, code: str | None):
    try:
        promo = await _create_from_state(state, code=code, created_by=callback.from_user.id)
    except ValueError as exc:
        await callback.answer(str(exc), show_alert=True)
        return
    await state.clear()
    await callback.message.answer("✅ Промокод створено!", reply_markup=admin_keyboard())
    await callback.message.edit_text(
        f"✅ Промокод створено!\n\n{get_promo_stats_text(promo)}",
        parse_mode="HTML",
        reply_markup=get_promos_keyboard(get_all_promos()),
    )
    await callback.answer()


async def _create_from_state(state: FSMContext, *, code: str | None, created_by: int):
    data = await state.get_data()
    promo_type = data.get("promo_type")
    if promo_type not in ("percent", "free"):
        raise ValueError("Спочатку оберіть тип промокоду")
    return create_promo_code(
        promo_type=promo_type,
        discount_percent=data.get("discount_percent"),
        free_months=data.get("free_months"),
        expires_at=data.get("expires_at"),
        code=code,
        created_by=created_by,
        product_id=data.get("product_id"),
        max_uses=int(data.get("max_uses") if data.get("max_uses") is not None else 1),
    )
