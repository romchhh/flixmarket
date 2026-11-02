from datetime import datetime

from aiogram import F, Router, types
from aiogram.fsm.context import FSMContext

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
    get_promo_view_keyboard,
    get_promos_keyboard,
)
from ulits.admin_states import PromoStates
from ulits.filters import IsAdmin

router = Router()


def _promos_list_text() -> str:
    return (
        "<b>🎟 Промокоди</b>\n\n"
        "Кожен код унікальний і одноразовий.\n"
        "Можна створити знижку у % або безкоштовний доступ на 1/3/6/12 міс."
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
    delete_promo(promo_id)
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
    await state.update_data(promo_type="percent")
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
    await state.update_data(discount_percent=value)
    await message.answer(
        f"Знижка: <b>{value:.0f}%</b>\n\nОберіть термін дії:",
        parse_mode="HTML",
        reply_markup=get_promo_expiry_keyboard(),
    )


@router.callback_query(IsAdmin(), F.data == "promo_type_free")
async def promo_type_free(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(promo_type="free")
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
    await state.update_data(promo_type="free", free_months=months)
    await callback.message.edit_text(
        f"Період: <b>{months} міс.</b>\n\nОберіть термін дії промокоду:",
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
    )
