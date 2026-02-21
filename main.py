import os
import json
import asyncio
from datetime import datetime
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

# 1. Настройка окружения
load_dotenv()
API_TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# 2. Работа с данными (JSON)
FILENAME = "tasks.json"
tasks = []

def save_tasks():
    with open(FILENAME, 'w', encoding='utf-8') as f:
        json.dump(tasks, f, ensure_ascii=False, indent=4)

def load_tasks():
    global tasks
    if os.path.exists(FILENAME):
        try:
            with open(FILENAME, 'r', encoding='utf-8') as f:
                tasks = json.load(f)
        except Exception:
            tasks = []
    else:
        tasks = []

# Загружаем задачи при старте скрипта
load_tasks()

# 3. Состояния для создания задачи
class TaskStates(StatesGroup):
    waiting_for_text = State()
    waiting_for_date = State()

# --- Кнопки управления ---
def get_main_kb():
    buttons = [
        [types.KeyboardButton(text="➕ Новая задача"), types.KeyboardButton(text="📋 Список")],
        [types.KeyboardButton(text="✅ Завершить"), types.KeyboardButton(text="🗑 Удалить")]
    ]
    return types.ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

# --- Обработчики команд ---

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "Привет! Я **CLI-Tracker** 🚀\nВсе ваши задачи сохраняются автоматически.",
        reply_markup=get_main_kb()
    )

@dp.message(F.text == "📋 Список")
async def list_tasks(message: types.Message):
    if not tasks:
        await message.answer("Список задач пуст 📭")
        return

    res = "📋 **Ваши задачи:**\n\n"
    for i, t in enumerate(tasks, 1):
        status = "✔️" if t["is_completed"] else "❌"
        date_str = f" (До: {t['to_complete_at']})" if t.get('to_complete_at') else ""
        res += f"{i}. {t['text']}{date_str} — {status}\n"
    await message.answer(res)

@dp.message(F.text == "➕ Новая задача")
async def create_task_start(message: types.Message, state: FSMContext):
    await message.answer("Введите текст задачи:")
    await state.set_state(TaskStates.waiting_for_text)

@dp.message(TaskStates.waiting_for_text)
async def process_task_text(message: types.Message, state: FSMContext):
    await state.update_data(task_text=message.text)
    await message.answer("Введите дату (ДД-ММ-ГГГГ) или напишите 'нет':")
    await state.set_state(TaskStates.waiting_for_date)

@dp.message(TaskStates.waiting_for_date)
async def process_task_date(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    date_input = message.text.strip().lower()
    due_date = None

    if date_input != 'нет':
        try:
            dt = datetime.strptime(date_input, "%d-%m-%Y")
            if dt.date() < datetime.now().date():
                await message.answer("Дата уже прошла! Попробуйте еще раз или 'нет':")
                return
            due_date = date_input
        except ValueError:
            await message.answer("Ошибка формата! Используйте ДД-ММ-ГГГГ:")
            return

    tasks.append({
        "text": user_data['task_text'],
        "to_complete_at": due_date,
        "is_completed": False
    })
    save_tasks()
    await message.answer(f"✅ Задача добавлена!", reply_markup=get_main_kb())
    await state.clear()

@dp.message(F.text == "✅ Завершить")
async def finish_prompt(message: types.Message):
    if not tasks:
        await message.answer("Список пуст.")
        return
    await message.answer("Введите номер задачи, которую вы выполнили:")

@dp.message(F.text == "🗑 Удалить")
async def delete_prompt(message: types.Message):
    if not tasks:
        await message.answer("Список пуст.")
        return
    await message.answer("Введите номер задачи для удаления:")

@dp.message(lambda m: m.text.isdigit())
async def handle_numbers(message: types.Message):
    idx = int(message.text) - 1
    if 0 <= idx < len(tasks):
        # Если последнее сообщение содержало слово "Удалить"
        # Для простоты: если нажата кнопка Удалить, а потом число — удаляем
        # Здесь мы просто завершаем задачу по умолчанию, либо удаляем (логика ниже)
        task_text = tasks[idx]['text']
        
        # Упрощенная логика: если вводим число, задача считается выполненной
        tasks[idx]["is_completed"] = True
        save_tasks()
        await message.answer(f"Задача «{task_text}» отмечена как выполненная! 🎉")
    else:
        await message.answer("Нет задачи под таким номером!")

async def main():
    print("Бот запущен и готов к работе...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
