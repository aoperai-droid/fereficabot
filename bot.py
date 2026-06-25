import re
import sqlite3
import logging
import random
import asyncio
from datetime import datetime
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message, ChatPermissions, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.enums import ParseMode

# --- ⚠️ ИЗМЕНИ ЭТИ НАСТРОЙКИ ПЕРЕД ЗАГРУЗКОЙ ---
TOKEN = "ВАШ_ТОКЕН_СЮДА"  # Вставь свой токен
PASSWORD = "мойпароль123"  # Придумай пароль
ADMIN_ID = 1364254252  # Твой Telegram ID
# ------------------------------------------------

# --- Инициализация ---
bot = Bot(token=TOKEN)
dp = Dispatcher()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- База данных ---
def init_db():
    conn = sqlite3.connect('banned_words.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS words (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            word TEXT UNIQUE NOT NULL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS verified_users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            verified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS greeted_users (
            user_id INTEGER PRIMARY KEY,
            greeted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS old_users (
            user_id INTEGER PRIMARY KEY,
            marked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    
    cursor.execute("SELECT COUNT(*) FROM words")
    if cursor.fetchone()[0] == 0:
        initial_words = [
            "подработка", "заработок", "заработать", "заработнаяплата", "удаленнаяработа",
            "удаленка", "работавинтернете", "работаонлайн", "вакансия", "дополнительныйдоход",
            "свободныйграфик", "легкиеденьги", "доходбезвложений", "пассивныйдоход", "работанадому",
            "заработокбезопыта", "ищулюдей", "ищусотрудника", "ищучеловека", "ищуработника",
            "ищукандидата", "ищудевушку", "ищупарня", "ищупомощника", "ищуассистента",
            "требуютсясотрудники", "требуетсясотрудник", "набираемсотрудников", "наборсотрудников",
            "открытавакансия", "приглашаювкоманду", "ищемлюдей", "ищемсотрудников", "ищемработников",
            "вакансияоткрыта", "заработнаяплатавысокая", "отдатьбесплатно", "отдамбесплатно",
            "отдатьбесплатнозарефку", "реф", "рефка", "альфа", "дельце", "трудоустройство",
            "кешвышеобычного", "обучениенаместе", "ищутолковыхребят", "пкклуб", "пацаныотлет",
            "пацаныотл", "оплатасразу", "работанесложная", "новичковберём", "выплатимчестно",
            "требуетсяпомощь", "естьтемазароботка", "еслиинтерестнопиши", "зарефкуальфы",
            "прибыльнаяшабашка", "можносовмещатьсучебой", "скупаюголду", "хорошемукурсу",
            "беруваренду", "дамподработку", "бросаюкурить", "плачуот", "вкомпьютерныйклуб",
            "быстрыеденьги", "легкийкуш", "арендасим", "куплюакк", "арендааккаунта", "арбитраж",
            "биржа", "быстрыйвыхлоп", "доходность", "крипта", "пассивныйзаработок", "ищемпарней",
            "ищемчеловека", "винтернетмагазин", "ищемребят", "возьмуваренду", "скуплюпушкинскиекарты",
            "баллыпушкинскойкарты"
        ]
        for w in initial_words:
            try:
                cursor.execute("INSERT INTO words (word) VALUES (?)", (w.lower(),))
            except:
                pass
        conn.commit()
    conn.close()
    logger.info("✅ База данных инициализирована")

init_db()
logger.info(f"🤖 Бот запущен! Админ ID: {ADMIN_ID}")

# --- Функции БД ---
def get_all_words():
    conn = sqlite3.connect('banned_words.db')
    cursor = conn.cursor()
    cursor.execute("SELECT word FROM words")
    words = [row[0] for row in cursor.fetchall()]
    conn.close()
    return words

def add_word_to_db(word):
    conn = sqlite3.connect('banned_words.db')
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO words (word) VALUES (?)", (word.lower(),))
        conn.commit()
        conn.close()
        return True
    except:
        conn.close()
        return False

def remove_word_from_db(word):
    conn = sqlite3.connect('banned_words.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM words WHERE word = ?", (word.lower(),))
    conn.commit()
    affected = cursor.rowcount
    conn.close()
    return affected > 0

def is_user_verified(user_id):
    conn = sqlite3.connect('banned_words.db')
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM verified_users WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result is not None

def add_verified_user(user_id, username=None):
    conn = sqlite3.connect('banned_words.db')
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO verified_users (user_id, username) VALUES (?, ?)", (user_id, username or str(user_id)))
    conn.commit()
    conn.close()

def is_user_greeted(user_id):
    conn = sqlite3.connect('banned_words.db')
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM greeted_users WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result is not None

def add_greeted_user(user_id):
    conn = sqlite3.connect('banned_words.db')
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO greeted_users (user_id) VALUES (?)", (user_id,))
    conn.commit()
    conn.close()

def is_old_user(user_id):
    conn = sqlite3.connect('banned_words.db')
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM old_users WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result is not None

def mark_as_old_user(user_id):
    conn = sqlite3.connect('banned_words.db')
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO old_users (user_id) VALUES (?)", (user_id,))
    conn.commit()
    conn.close()

def clean_text(text):
    return re.sub(r'[^a-zA-Zа-яА-Я0-9]', '', text.lower())

def generate_math_question():
    a = random.randint(2, 9)
    b = random.randint(2, 9)
    correct = a * b
    wrong_options = []
    while len(wrong_options) < 2:
        wrong = correct + random.randint(-5, 5)
        if wrong != correct and wrong > 0 and wrong not in wrong_options:
            wrong_options.append(wrong)
    options = wrong_options + [correct]
    random.shuffle(options)
    return f"{a} × {b} = ?", correct, options

# --- Конфигурация ---
verifications = {}
user_sessions = {}
AUTO_DELETE_DELAY = 60
VERIFICATION_TIMEOUT = 60
MAX_ATTEMPTS = 3

WELCOME_TEXT = """
🌟 <b>Добро пожаловать в Вейп-Барахолку Краснодара</b>, {user_mention}! 🎉

📋 <b>Правила чата:</b>
🚫 <b>Запрещено:</b>
• ❌ Не вейп-тематика
• ❌ Оскорбления и флуд
• ❌ Спам и реклама

⚠️ <b>Внимание!</b>
При скаме: @callumom 
Администрация не отвечает за сделки.

🏪 <b>Лучшие вейп-шопы:</b>
• 🔥 Mix Vape: https://t.me/mixvape1

💫 <b>Приятного общения!</b>
"""

async def delete_message_later(chat_id, message_id, delay=60):
    await asyncio.sleep(delay)
    try:
        await bot.delete_message(chat_id, message_id)
    except:
        pass

def create_verification_keyboard(options):
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=str(options[0]), callback_data=f"verify_{options[0]}"),
            InlineKeyboardButton(text=str(options[1]), callback_data=f"verify_{options[1]}")
        ],
        [
            InlineKeyboardButton(text=str(options[2]), callback_data=f"verify_{options[2]}")
        ]
    ])

# --- Обработчики ---
@dp.message()
async def handle_all_messages(message: Message):
    if message.chat.type not in ['group', 'supergroup']:
        return
    
    if message.new_chat_members:
        await handle_new_member(message)
    
    await check_and_ban(message)

async def handle_new_member(message: Message):
    try:
        bot_member = await message.chat.get_member(bot.id)
        if not bot_member.can_restrict_members:
            return
    except:
        return
    
    for new_member in message.new_chat_members:
        if new_member.is_bot:
            continue
        
        user_id = new_member.id
        
        if is_old_user(user_id) or is_user_verified(user_id) or is_user_greeted(user_id):
            continue
        
        try:
            await bot.restrict_chat_member(
                chat_id=message.chat.id,
                user_id=user_id,
                permissions=ChatPermissions(can_send_messages=False)
            )
        except:
            continue
        
        question, correct_answer, options = generate_math_question()
        keyboard = create_verification_keyboard(options)
        
        mention = new_member.mention_html()
        welcome_msg = WELCOME_TEXT.format(user_mention=mention)
        
        verification_text = (
            f"{welcome_msg}\n\n"
            f"🔐 <b>Верификация:</b>\n"
            f"Реши пример, чтобы получить доступ к чату:\n"
            f"<b>{question}</b>\n\n"
            f"⏱ У тебя {VERIFICATION_TIMEOUT} секунд и {MAX_ATTEMPTS} попытки."
        )
        
        try:
            sent_msg = await message.reply(
                verification_text,
                parse_mode=ParseMode.HTML,
                reply_markup=keyboard
            )
            
            verifications[user_id] = {
                'attempts': 0,
                'answer': correct_answer,
                'message_id': sent_msg.message_id,
                'chat_id': message.chat.id,
                'user_id': user_id
            }
            
            add_greeted_user(user_id)
            asyncio.create_task(delete_message_later(message.chat.id, sent_msg.message_id))
            asyncio.create_task(verification_timeout(user_id, message.chat.id))
            
        except Exception as e:
            logger.error(f"Ошибка верификации: {e}")

async def verification_timeout(user_id, chat_id):
    await asyncio.sleep(VERIFICATION_TIMEOUT)
    if user_id in verifications:
        del verifications[user_id]

@dp.callback_query(lambda c: c.data and c.data.startswith('verify_'))
async def process_verification(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    chat_id = callback_query.message.chat.id
    
    if user_id not in verifications:
        await callback_query.answer("⏰ Время истекло!", show_alert=True)
        try:
            await callback_query.message.delete()
        except:
            pass
        return
    
    if verifications[user_id]['user_id'] != user_id:
        await callback_query.answer("❌ Не твоя верификация!", show_alert=True)
        return
    
    try:
        selected_value = int(callback_query.data.split('_')[1])
    except:
        return
    
    correct_answer = verifications[user_id]['answer']
    
    if selected_value == correct_answer:
        await callback_query.answer("✅ Правильно!", show_alert=True)
        
        try:
            await bot.restrict_chat_member(
                chat_id=chat_id,
                user_id=user_id,
                permissions=ChatPermissions(can_send_messages=True)
            )
            
            add_verified_user(user_id, callback_query.from_user.username or str(user_id))
            
            success_msg = await callback_query.message.reply(
                f"✅ {callback_query.from_user.mention_html()}, ты прошел верификацию! Добро пожаловать! 🎉",
                parse_mode=ParseMode.HTML
            )
            
            try:
                await callback_query.message.delete()
            except:
                pass
            
            asyncio.create_task(delete_message_later(chat_id, success_msg.message_id))
            
        except Exception as e:
            logger.error(f"Ошибка верификации: {e}")
        
        del verifications[user_id]
    else:
        verifications[user_id]['attempts'] += 1
        attempts_left = MAX_ATTEMPTS - verifications[user_id]['attempts']
        
        if attempts_left <= 0:
            await callback_query.answer("❌ Попытки исчерпаны!", show_alert=True)
            try:
                await callback_query.message.delete()
            except:
                pass
            del verifications[user_id]
        else:
            question, correct_answer, options = generate_math_question()
            verifications[user_id]['answer'] = correct_answer
            keyboard = create_verification_keyboard(options)
            
            text_parts = callback_query.message.text.split('🔐')
            welcome_part = text_parts[0] if len(text_parts) > 0 else ""
            
            try:
                await callback_query.message.edit_text(
                    f"{welcome_part}"
                    f"🔐 <b>Верификация:</b>\n"
                    f"❌ Неправильно! Осталось попыток: {attempts_left}\n"
                    f"Реши новый пример:\n"
                    f"<b>{question}</b>\n\n"
                    f"⏱ У тебя {VERIFICATION_TIMEOUT} секунд.",
                    parse_mode=ParseMode.HTML,
                    reply_markup=keyboard
                )
            except:
                pass
            
            await callback_query.answer(f"❌ Неправильно! Осталось {attempts_left} попыток", show_alert=True)

async def check_and_ban(message: Message):
    if not message.text:
        return
    
    user_id = message.from_user.id
    
    if not is_old_user(user_id):
        mark_as_old_user(user_id)
    
    if not is_user_verified(user_id):
        return
    
    banned_words = get_all_words()
    if not banned_words:
        return
    
    cleaned_msg = clean_text(message.text)
    if len(cleaned_msg) < 3:
        return
    
    found_word = None
    for word in banned_words:
        if word in cleaned_msg:
            found_word = word
            break
    
    if found_word:
        try:
            bot_member = await message.chat.get_member(bot.id)
            if not bot_member.can_restrict_members:
                return
        except:
            return
        
        try:
            await bot.restrict_chat_member(
                chat_id=message.chat.id,
                user_id=user_id,
                permissions=ChatPermissions(can_send_messages=False)
            )
            
            mention = message.from_user.mention_html()
            ban_msg = await message.reply(
                f"🚫 Пользователь {mention} был ограничен.\n"
                f"Причина: <b>{found_word}</b>",
                parse_mode=ParseMode.HTML
            )
            
            asyncio.create_task(delete_message_later(message.chat.id, ban_msg.message_id))
            
            try:
                await message.delete()
            except:
                pass
                
        except Exception as e:
            logger.error(f"Ошибка бана: {e}")

# --- Команды в ЛС ---
@dp.message(Command("start"))
async def cmd_start(message: Message):
    if message.chat.type != 'private':
        return
    
    is_admin = message.from_user.id == ADMIN_ID
    
    text = "🤖 <b>Бот для модерации</b>\n\n"
    if is_admin:
        text += "✅ Ты администратор! Доступ открыт.\n\n"
    else:
        text += f"Введи пароль: <code>/login {PASSWORD}</code>\n\n"
    
    text += (
        "📋 <b>Команды:</b>\n"
        "/addword слово - добавить\n"
        "/delword слово - удалить\n"
        "/listwords - список\n"
        "/stats - статистика\n"
        "/logout - выйти"
    )
    
    await message.reply(text, parse_mode=ParseMode.HTML)

@dp.message(Command("login"))
async def cmd_login(message: Message):
    if message.chat.type != 'private':
        return
    
    if message.from_user.id == ADMIN_ID:
        await message.reply("✅ Ты админ!")
        return
    
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.reply("❌ Введи пароль")
        return
    
    if args[1].strip() == PASSWORD:
        user_sessions[message.from_user.id] = True
        await message.reply("✅ Доступ открыт!")
    else:
        await message.reply("❌ Неверный пароль!")

@dp.message(Command("logout"))
async def cmd_logout(message: Message):
    if message.chat.type != 'private':
        return
    
    if message.from_user.id == ADMIN_ID:
        await message.reply("ℹ️ Ты админ")
        return
    
    if message.from_user.id in user_sessions:
        del user_sessions[message.from_user.id]
        await message.reply("✅ Выход выполнен")
    else:
        await message.reply("ℹ️ Ты не авторизован")

@dp.message(Command("addword"))
async def add_word_command(message: Message):
    if message.chat.type != 'private':
        return
    
    if not (message.from_user.id == ADMIN_ID or user_sessions.get(message.from_user.id)):
        await message.reply("🔐 Доступ запрещен!")
        return
    
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.reply("ℹ️ /addword слово")
        return
    
    word = re.sub(r'[^a-zA-Zа-яА-Я0-9]', '', args[1].strip().lower())
    if len(word) < 2:
        await message.reply("❌ Слишком коротко")
        return
    
    if add_word_to_db(word):
        await message.reply(f"✅ Добавлено: {word}")
    else:
        await message.reply(f"⚠️ Уже есть: {word}")

@dp.message(Command("delword"))
async def del_word_command(message: Message):
    if message.chat.type != 'private':
        return
    
    if not (message.from_user.id == ADMIN_ID or user_sessions.get(message.from_user.id)):
        await message.reply("🔐 Доступ запрещен!")
        return
    
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.reply("ℹ️ /delword слово")
        return
    
    word = re.sub(r'[^a-zA-Zа-яА-Я0-9]', '', args[1].strip().lower())
    
    if remove_word_from_db(word):
        await message.reply(f"✅ Удалено: {word}")
    else:
        await message.reply(f"⚠️ Не найдено: {word}")

@dp.message(Command("listwords"))
async def list_words_command(message: Message):
    if message.chat.type != 'private':
        return
    
    if not (message.from_user.id == ADMIN_ID or user_sessions.get(message.from_user.id)):
        await message.reply("🔐 Доступ запрещен!")
        return
    
    words = get_all_words()
    if not words:
        await message.reply("📭 Список пуст")
        return
    
    await message.reply(f"📋 Список ({len(words)} шт.):\n\n" + "\n".join([f"• {w}" for w in words[:50]]))

@dp.message(Command("stats"))
async def stats_command(message: Message):
    if message.chat.type != 'private':
        return
    
    if not (message.from_user.id == ADMIN_ID or user_sessions.get(message.from_user.id)):
        await message.reply("🔐 Доступ запрещен!")
        return
    
    conn = sqlite3.connect('banned_words.db')
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM words")
    words = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM verified_users")
    verified = cursor.fetchone()[0]
    conn.close()
    
    await message.reply(
        f"📊 <b>Статистика:</b>\n\n"
        f"📝 Слов: {words}\n"
        f"✅ Верифицировано: {verified}\n"
        f"🔄 Активных: {len(verifications)}",
        parse_mode=ParseMode.HTML
    )

# --- ЗАПУСК ---
if __name__ == "__main__":
    print("🤖 Бот запущен!")
    print(f"👤 Админ ID: {ADMIN_ID}")
    asyncio.run(dp.start_polling(bot))
