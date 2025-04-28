from telegram import Update, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters
import sqlite3
import os
import subprocess
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Constants
LANGUAGES = ['en', 'fr', 'ar']
LEVELS = ['beginner', 'intermediate', 'advanced']

# Track user modes: 'menu', 'ide', 'quiz', 'lesson_list'
user_modes = {}
# For quiz mode: map user_id -> (lesson_id, correct_option)
user_quiz = {}

# Internationalization texts
LANG_TEXTS = {
    'en': {
        'welcome': "Welcome to Ija T3alllem Python!",
        'menu': "Choose an option:",
        'learn': "📘 Learn Python",
        'progress': "🧪 My Progress",
        'lang': "🌐 Change Language",
        'ide': "💻 Try Python (IDE)",
        'help': "📋 Help",
        'back': "🔙 Back",
        'home': "🏠 Home",
        'choose_level': "Choose your level:",
        'lessons_list': "📚 Lessons for {level}:",
        'quiz_question_msg': "❓ {question}",
        'quiz_correct_msg': "✅ Correct! Next lesson unlocked.",
        'quiz_incorrect_msg': "❌ Incorrect. Try again or click Home to exit.",
    },
    'fr': {
        'welcome': "Bienvenue à Ija T3alllem Python!",
        'menu': "Choisissez une option:",
        'learn': "📘 Apprendre Python",
        'progress': "🧪 Mon Progrès",
        'lang': "🌐 Changer de langue",
        'ide': "💻 Essayer Python (IDE)",
        'help': "📋 Aide",
        'back': "🔙 Retour",
        'home': "🏠 Accueil",
        'choose_level': "Choisissez votre niveau:",
        'lessons_list': "📚 Leçons pour {level}:",
        'quiz_question_msg': "❓ {question}",
        'quiz_correct_msg': "✅ Correct! Leçon suivante débloquée.",
        'quiz_incorrect_msg': "❌ Incorrect. Réessayez ou cliquez sur Accueil.",
    },
    'ar': {
        'welcome': "مرحبًا بك في Ija T3alllem Python!",
        'menu': "اختر خيارًا:",
        'learn': "📘 تعلم بايثون",
        'progress': "🧪 تقدمي",
        'lang': "🌐 تغيير اللغة",
        'ide': "💻 جرب بايثون",
        'help': "📋 مساعدة",
        'back': "🔙 العودة",
        'home': "🏠 الرئيسية",
        'choose_level': "اختر مستواك:",
        'lessons_list': "📚 الدروس لـ {level}:",
        'quiz_question_msg': "❓ {question}",
        'quiz_correct_msg': "✅ صحيح! تم فتح الدرس التالي.",
        'quiz_incorrect_msg': "❌ خطأ. حاول مرة أخرى أو انقر على الرئيسية.",
    }
}

# SQLite setup
conn = sqlite3.connect('bot.db', check_same_thread=False)
c = conn.cursor()
# Users table
c.execute('''CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY,
    lang TEXT DEFAULT 'en',
    level TEXT DEFAULT 'beginner',
    lesson INTEGER DEFAULT 1,
    progress INTEGER DEFAULT 0
)''')
# Lessons table
c.execute('''CREATE TABLE IF NOT EXISTS lessons (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    level TEXT,
    number INTEGER,
    title TEXT,
    explanation TEXT,
    example TEXT
)''')
# Quizzes table
c.execute('''CREATE TABLE IF NOT EXISTS quizzes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    lesson_id INTEGER,
    question TEXT,
    option_a TEXT,
    option_b TEXT,
    option_c TEXT,
    option_d TEXT,
    correct_option TEXT,
    FOREIGN KEY(lesson_id) REFERENCES lessons(id)
)''')
conn.commit()

# Helper functions
def get_user(user_id):
    c.execute("SELECT * FROM users WHERE id=?", (user_id,))
    user = c.fetchone()
    if not user:
        c.execute("INSERT INTO users (id) VALUES (?)", (user_id,))
        conn.commit()
        return get_user(user_id)
    return user

def get_lesson(level, number):
    c.execute("SELECT id, title, explanation, example FROM lessons WHERE level=? AND number=?", (level, number))
    return c.fetchone()

def get_quiz_for_lesson(lesson_id):
    c.execute("SELECT question, option_a, option_b, option_c, option_d, correct_option FROM quizzes WHERE lesson_id=?", (lesson_id,))
    return c.fetchone()

def run_python_code(code):
    try:
        with open("temp_code.py", "w", encoding="utf-8") as f:
            f.write(code)
        result = subprocess.run(["python3", "temp_code.py"], capture_output=True, text=True, timeout=5)
        output = result.stdout + result.stderr
        if not output.strip():
            output = "✅ Code ran successfully with no output."
        return output[:4000]
    except subprocess.TimeoutExpired:
        return "❗ Your code took too long to run (timeout)."
    except Exception as e:
        return f"❗ Error: {e}"

# Menu keyboards
def main_menu(lang):
    return ReplyKeyboardMarkup([
        [KeyboardButton(LANG_TEXTS[lang]['learn']), KeyboardButton(LANG_TEXTS[lang]['progress'])],
        [KeyboardButton(LANG_TEXTS[lang]['lang']), KeyboardButton(LANG_TEXTS[lang]['ide'])],
        [KeyboardButton(LANG_TEXTS[lang]['help'])]
    ], resize_keyboard=True, one_time_keyboard=False, input_field_placeholder=LANG_TEXTS[lang]['menu'])

def level_menu(lang, user_progress):
    def status(idx): return "✅" if user_progress >= idx*100 else "🔒"
    return ReplyKeyboardMarkup([
        [KeyboardButton(f"{status(0)} Beginner")],
        [KeyboardButton(f"{status(1)} Intermediate")],
        [KeyboardButton(f"{status(2)} Advanced")]
    ], resize_keyboard=True, one_time_keyboard=False)

def lessons_list(lang, level, user_progress):
    c.execute("SELECT number, title FROM lessons WHERE level=? ORDER BY number", (level,))
    items = c.fetchall()
    buttons = []
    for num, title in items:
        if num == 1 or user_progress >= (num-1):
            buttons.append(KeyboardButton(title))
        else:
            buttons.append(KeyboardButton(f"🔒 {title}"))
    rows = [buttons[i:i+2] for i in range(0, len(buttons), 2)]
    rows.insert(0, [KeyboardButton(LANG_TEXTS[lang]['back']), KeyboardButton(LANG_TEXTS[lang]['home']), KeyboardButton(LANG_TEXTS[lang]['lang'])])
    text = LANG_TEXTS[lang]['lessons_list'].format(level=level.title())
    return text, ReplyKeyboardMarkup(rows, resize_keyboard=True)

# Bot command handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user = get_user(user_id)
    lang = user[1]
    user_modes[user_id] = 'menu'
    await update.message.reply_text(
        LANG_TEXTS[lang]['welcome'] + f"\n\n{LANG_TEXTS[lang]['menu']}",
        reply_markup=main_menu(lang)
    )

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user = get_user(user_id)
    lang = user[1]
    text = update.message.text

    # IDE mode
    if user_modes.get(user_id) == 'ide':
        if text == LANG_TEXTS[lang]['home']:
            user_modes[user_id] = 'menu'
            return await start(update, context)
        output = run_python_code(text)
        await update.message.reply_text(f"🖥️ Output:\n\n{output}")
        return

    # Quiz mode
    if user_modes.get(user_id) == 'quiz':
        lesson_id, correct = user_quiz.get(user_id, (None, None))
        choice = text.strip().upper()
        if choice == correct:
            new_lesson = user[3] + 1
            new_progress = user[4] + 1
            c.execute("UPDATE users SET lesson=?, progress=? WHERE id=?", (new_lesson, new_progress, user_id))
            conn.commit()
            await update.message.reply_text(LANG_TEXTS[lang]['quiz_correct_msg'])
        else:
            await update.message.reply_text(LANG_TEXTS[lang]['quiz_incorrect_msg'])
        user_modes[user_id] = 'menu'
        return

    # Main menu: Learn Python
    if text == LANG_TEXTS[lang]['learn']:
        await update.message.reply_text(
            LANG_TEXTS[lang]['choose_level'],
            reply_markup=level_menu(lang, user[4])
        )
        return

    # Level selected: show lessons list
    if any(level.title() in text for level in LEVELS):
        lvl = text.split()[-1].lower()
        c.execute("UPDATE users SET level=? WHERE id=?", (lvl, user_id))
        conn.commit()
        lessons_text, markup = lessons_list(lang, lvl, user[4])
        user_modes[user_id] = 'lesson_list'
        await update.message.reply_text(lessons_text, reply_markup=markup)
        return

    # Lesson selected from list
    rows = c.execute("SELECT title, id FROM lessons WHERE level=? ORDER BY number", (user[2],)).fetchall()
    titles = {title: lid for title, lid in rows}
    if text in titles:
        lid = titles[text]
        lesson = c.execute("SELECT title, explanation, example FROM lessons WHERE id=?", (lid,)).fetchone()
        title, exp, ex = lesson
        # send lesson content
        await update.message.reply_text(f"📖 {title}\n\n{exp}\n\n🧩 Example:\n{ex}")
        # send quiz
        quiz = get_quiz_for_lesson(lid)
        if quiz:
            q, a, b, c_opt, d, correct = quiz
            opts = [[KeyboardButton(o)] for o in ['A', 'B', 'C', 'D']] + [[KeyboardButton(LANG_TEXTS[lang]['home'])]]
            user_modes[user_id] = 'quiz'
            user_quiz[user_id] = (lid, correct)
            await update.message.reply_text(
                LANG_TEXTS[lang]['quiz_question_msg'].format(question=q) + f"\nA) {a}\nB) {b}\nC) {c_opt}\nD) {d}",
                reply_markup=ReplyKeyboardMarkup(opts, resize_keyboard=True)
            )
        return

    # Progress bar
    if text == LANG_TEXTS[lang]['progress']:
        level_name = user[2].title()
        total = c.execute("SELECT COUNT(*) FROM lessons WHERE level=?", (user[2],)).fetchone()[0]
        done = user[4]
        pct = int((done / total) * 100) if total else 0
        bar_len = 20
        filled = int(pct / 100 * bar_len)
        bar = '🟩' * filled + '⬜' * (bar_len - filled)
        await update.message.reply_text(
            f"📊 Progress – {level_name} Level\n{done}/{total} lessons completed\n{bar} {pct}%"
        )
        return
    # Change language
    if text == LANG_TEXTS[lang]['lang']:
        flags = {'en': '🇬🇧', 'fr': '🇫🇷', 'ar': '🇹🇳'}
        langs = [[KeyboardButton(f"{flags[l]} {l.upper()}")] for l in LANGUAGES]
        await update.message.reply_text("Choose your language:", reply_markup=ReplyKeyboardMarkup(langs, resize_keyboard=True))
        return

    # Language selected
    if any(text.endswith(l.upper()) for l in LANGUAGES):
        chosen = text[-2:].lower()
        c.execute("UPDATE users SET lang=? WHERE id=?", (chosen, user_id))
        conn.commit()
        await update.message.reply_text(LANG_TEXTS[chosen]['welcome'], reply_markup=main_menu(chosen))
        return

    # IDE mode
    if text == LANG_TEXTS[lang]['ide']:
        user_modes[user_id] = 'ide'
        await update.message.reply_text(
            "💻 Send me your Python code. I'll execute it and show the output!",
            reply_markup=ReplyKeyboardMarkup([[KeyboardButton(LANG_TEXTS[lang]['home'])]], resize_keyboard=True)
        )
        return

    # Back or Home
    if text in (LANG_TEXTS[lang]['back'], LANG_TEXTS[lang]['home']):
        user_modes[user_id] = 'menu'
        return await start(update, context)

    if text == LANG_TEXTS[lang]['help']:
        await update.message.reply_text(
            "📋 👋 Need help?  \n Follow us here: \n GitHub: https://github.com/YassinChamakhi \n Instagram: https://instagram.com/yassin_chamakhi_")
        return
    # Default fallback
    await update.message.reply_text(f"You selected: {text}")

if __name__ == '__main__':
    app = ApplicationBuilder().token(os.getenv("TELEGRAM_BOT_TOKEN")).build()
    app.add_handler(CommandHandler('start', start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    print("Bot running...")
    app.run_polling()
