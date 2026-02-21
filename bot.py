from __future__ import annotations

import io
import os

import qrcode
from aiogram import Bot, Dispatcher, F
from aiogram.enums import ParseMode
from aiogram.filters import Command, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Message
from dotenv import load_dotenv

from tea_kitsune.keyboards import main_menu
from tea_kitsune.loyalty import next_tier, points_from_visits, tier_for_points
from tea_kitsune.storage import Storage


class NoteStates(StatesGroup):
    tea_name = State()
    taste = State()
    impression = State()


class AdminVisitStates(StatesGroup):
    waiting_code = State()


load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
ADMIN_IDS = {int(x.strip()) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip()}
storage = Storage(os.getenv("DB_PATH", "tea_kitsune.db"))

dp = Dispatcher(storage=MemoryStorage())


def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


@dp.message(Command("start"))
async def cmd_start(message: Message) -> None:
    user = storage.get_or_create_user(message.from_user.id, message.from_user.full_name)
    welcome = (
        "🦊 *Добро пожаловать в Чайную Кицунэ!*\n\n"
        "Здесь вы можете:\n"
        "• вести личный чайный блокнот;\n"
        "• накапливать визиты и бонусы;\n"
        "• показывать персональный QR для участия в акциях.\n\n"
        f"Ваш код гостя: `{user.qr_code}`"
    )
    await message.answer(welcome, parse_mode=ParseMode.MARKDOWN, reply_markup=main_menu(is_admin(message.from_user.id)))


@dp.message(F.text == "🫖 Мой профиль")
async def profile(message: Message) -> None:
    user = storage.get_or_create_user(message.from_user.id, message.from_user.full_name)
    visits = storage.visits_count(user.tg_id)
    points = points_from_visits(visits)
    tier = tier_for_points(points)
    await message.answer(
        f"👤 {user.full_name}\n"
        f"Посещений: {visits}\n"
        f"Баллы: {points}\n"
        f"Статус: {tier.name}\n"
        f"Награда уровня: {tier.reward}"
    )


@dp.message(F.text == "🎁 Лояльность")
async def loyalty(message: Message) -> None:
    visits = storage.visits_count(message.from_user.id)
    points = points_from_visits(visits)
    tier = tier_for_points(points)
    nxt = next_tier(points)
    text = f"🎁 Ваш уровень: *{tier.name}*\nБаллы: *{points}*\nТекущая награда: _{tier.reward}_"
    if nxt:
        need = nxt.min_points - points
        text += f"\n\nДо уровня *{nxt.name}* осталось {need} баллов."
    else:
        text += "\n\nВы достигли максимального уровня! ✨"
    await message.answer(text, parse_mode=ParseMode.MARKDOWN)


@dp.message(F.text == "📣 Акции")
async def promotions(message: Message) -> None:
    visits = storage.visits_count(message.from_user.id)
    points = points_from_visits(visits)
    text = (
        "📣 *Акции Чайной Кицунэ*\n"
        "• Визит до 12:00 — +5 бонусных баллов.\n"
        "• Приведи друга — получите по мини-дегустации.\n"
        "• Каждое 10-е посещение — авторский десерт в подарок.\n\n"
        f"У вас сейчас {points} баллов."
    )
    await message.answer(text, parse_mode=ParseMode.MARKDOWN)


@dp.message(F.text == "➕ Добавить заметку")
async def note_start(message: Message, state: FSMContext) -> None:
    await state.set_state(NoteStates.tea_name)
    await message.answer("Какой чай вы пили? Напишите название сорта.")


@dp.message(NoteStates.tea_name)
async def note_tea_name(message: Message, state: FSMContext) -> None:
    await state.update_data(tea_name=message.text.strip())
    await state.set_state(NoteStates.taste)
    await message.answer("Опишите вкус (например: медовый, цветочный, терпкий).")


@dp.message(NoteStates.taste)
async def note_taste(message: Message, state: FSMContext) -> None:
    await state.update_data(taste=message.text.strip())
    await state.set_state(NoteStates.impression)
    await message.answer("Какие впечатления? Что понравилось больше всего?")


@dp.message(NoteStates.impression)
async def note_done(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    storage.add_note(
        tg_id=message.from_user.id,
        tea_name=data["tea_name"],
        taste=data["taste"],
        impression=message.text.strip(),
    )
    await state.clear()
    await message.answer("Готово! 🍵 Запись добавлена в ваш чайный блокнот.")


@dp.message(F.text == "📓 Чайный блокнот")
async def notes_list(message: Message) -> None:
    notes = storage.get_notes(message.from_user.id, limit=10)
    if not notes:
        await message.answer("Пока записей нет. Нажмите «➕ Добавить заметку», чтобы начать.")
        return

    lines = ["📓 *Последние записи:*\n"]
    for idx, note in enumerate(notes, start=1):
        lines.append(
            f"{idx}. *{note['tea_name']}*\n"
            f"Вкус: {note['taste']}\n"
            f"Впечатление: {note['impression']}\n"
            f"Дата: {note['created_at'][:10]}\n"
        )
    await message.answer("\n".join(lines), parse_mode=ParseMode.MARKDOWN)


@dp.message(F.text == "🔳 Мой QR")
async def my_qr(message: Message) -> None:
    user = storage.get_or_create_user(message.from_user.id, message.from_user.full_name)
    qr = qrcode.QRCode(box_size=8, border=2)
    qr.add_data(user.qr_code)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")

    bio = io.BytesIO()
    bio.name = "kitsune_qr.png"
    img.save(bio, "PNG")
    bio.seek(0)

    await message.answer_photo(
        photo=bio,
        caption=(
            "Ваш персональный QR-код для фиксации визитов и участия в акциях.\n"
            f"Код: `{user.qr_code}`"
        ),
        parse_mode=ParseMode.MARKDOWN,
    )


@dp.message(Command("visit"))
async def admin_visit_cmd(message: Message, command: CommandObject) -> None:
    if not is_admin(message.from_user.id):
        await message.answer("Эта команда доступна только администратору.")
        return
    if not command.args:
        await message.answer("Использование: /visit KITSUNE-XXXXXXXXXXXX")
        return
    await process_visit_code(message, command.args.strip())


@dp.message(F.text == "✅ Отметить визит (админ)")
async def admin_visit_button(message: Message, state: FSMContext) -> None:
    if not is_admin(message.from_user.id):
        await message.answer("Кнопка доступна только администратору.")
        return
    await state.set_state(AdminVisitStates.waiting_code)
    await message.answer("Отправьте код гостя (или текст из QR), чтобы засчитать визит.")


@dp.message(AdminVisitStates.waiting_code)
async def admin_visit_waiting(message: Message, state: FSMContext) -> None:
    await process_visit_code(message, message.text.strip())
    await state.clear()


async def process_visit_code(message: Message, code: str) -> None:
    tg_id = storage.add_visit_by_code(code)
    if tg_id is None:
        await message.answer("Гость с таким кодом не найден. Проверьте QR-код.")
        return
    visits = storage.visits_count(tg_id)
    points = points_from_visits(visits)
    await message.answer(f"✅ Визит засчитан. Всего посещений: {visits}, баллов: {points}.")


async def main() -> None:
    if not BOT_TOKEN:
        raise RuntimeError("Укажите BOT_TOKEN в .env")
    bot = Bot(token=BOT_TOKEN)
    await dp.start_polling(bot)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
