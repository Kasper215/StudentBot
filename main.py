import asyncio
import os
from datetime import datetime
from dotenv import load_dotenv

# ИМПОРТЫ AIOGRAM
from aiogram import Bot, Dispatcher, F
from aiogram.types import (
    Message, 
    FSInputFile, 
    CallbackQuery, 
    InlineKeyboardButton, 
    KeyboardButton, 
    ReplyKeyboardMarkup, 
    ReplyKeyboardRemove
)
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.utils.keyboard import InlineKeyboardBuilder # ВОТ ЭТА СТРОКА БЫЛА ПРОПУЩЕНА

# ЛОКАЛЬНЫЕ ИМПОРТЫ
from database.core import init_db
from database.requests import set_user, log_conversion
from services.processing import convert_images_to_pdf, clean_up_files

load_dotenv()

bot = Bot(token=os.getenv('BOT_TOKEN'))
dp = Dispatcher()
TEMP_DIR = "temp"

# Состояния
class PDFForm(StatesGroup):
    collecting_photos = State()
    naming_file = State()

# Клава "ГОТОВО" (Inline - под сообщением)
def get_done_keyboard():
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="✅ ГОТОВО, СОБРАТЬ PDF", callback_data="done"))
    return builder.as_markup()

# Клава выбора имени (Reply - вместо букв)
def get_naming_keyboard():
    kb = [
        [KeyboardButton(text="📅 Оставить стандартное (Дата)")],
        [KeyboardButton(text="✏️ Ввести своё название")]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True, one_time_keyboard=True)

# --- ОБРАБОТЧИКИ ---

@dp.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    await set_user(message.from_user.id, message.from_user.username, message.from_user.full_name)
    await message.answer("Присылай фото по одному или альбомом. Когда отправишь все — жми кнопку ниже!", reply_markup=ReplyKeyboardRemove())
    await state.set_state(PDFForm.collecting_photos)
    await state.update_data(photo_paths=[])

@dp.message(PDFForm.collecting_photos, F.photo)
async def handle_photos(message: Message, state: FSMContext):
    data = await state.get_data()
    photo_paths = data.get("photo_paths", [])

    # Создаем личную папку юзера
    user_dir = os.path.join(TEMP_DIR, str(message.from_user.id))
    os.makedirs(user_dir, exist_ok=True)

    # Скачиваем фото
    file_id = message.photo[-1].file_id
    path = os.path.join(user_dir, f"{file_id}.jpg")
    
    file = await bot.get_file(file_id)
    await bot.download_file(file.file_path, path)
    
    photo_paths.append(path)
    await state.update_data(photo_paths=photo_paths)

    # Показываем кнопку "Готово"
    await message.answer(f"📸 Принято фото №{len(photo_paths)}", reply_markup=get_done_keyboard())

@dp.callback_query(F.data == "done")
async def process_done(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    if not data.get("photo_paths"):
        await callback.answer("Сначала пришлете фото!", show_alert=True)
        return

    await callback.message.answer("Как назовем PDF-файл?", reply_markup=get_naming_keyboard())
    await state.set_state(PDFForm.naming_file)
    await callback.answer()

@dp.message(PDFForm.naming_file)
async def process_naming(message: Message, state: FSMContext):
    data = await state.get_data()
    photo_paths = data.get("photo_paths")
    
    if message.text == "📅 Оставить стандартное (Дата)":
        filename = f"PDF_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    elif message.text == "✏️ Ввести своё название":
        await message.answer("Введите название файла (без .pdf):", reply_markup=ReplyKeyboardRemove())
        return 
    else:
        # Если пользователь ввел текст сам
        filename = f"{message.text}.pdf"

    status_msg = await message.answer(f"⏳ Начинаю сборку {filename}...", reply_markup=ReplyKeyboardRemove())
    
    user_dir = os.path.join(TEMP_DIR, str(message.from_user.id))
    output_pdf = os.path.join(user_dir, filename)

    # Конвертация
    success = convert_images_to_pdf(photo_paths, output_pdf)

    if success:
        await log_conversion(message.from_user.id, f"img_to_pdf_{len(photo_paths)}")
        await message.answer_document(FSInputFile(output_pdf), caption=f"Успешно! Страниц: {len(photo_paths)}")
    else:
        await message.answer("Произошла ошибка при сборке PDF.")

    # Чистка и сброс состояния
    clean_up_files(photo_paths + [output_pdf])
    await state.clear()
    await status_msg.delete()
    await message.answer("Готов к новому файлу! Просто присылай фото.")

async def main():
    await init_db()
    print("Бот запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Выход")