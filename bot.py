from telegram import Update, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters
import sqlite3
import os
from dotenv import load_dotenv
load_dotenv()

# Constants
LANGUAGES = ['en', 'fr', 'ar']
LEVELS = ['beginner', 'intermediate', 'advanced']

# Internationalization example (for demo purposes)
LANG_TEXTS = {
    'en': {
        'welcome': "Welcome to Ija T3alllem Python!",
        'menu': "Choose an option:",
        'learn': "📘 Learn Python",
        'progress': "🧪 My Progress",
        'lang': "🌐 Change Language",
        'ide': "💻 Try Python (IDE)",
        'help': "📋 Help",
        'choose_level': "Choose your level:",
        'lessons_locked': "🔒 Locked - Complete previous lessons",
        'lessons_list': "📚 Lessons for {level}:",
        'quiz_locked': "🔒 You need to score 5/5 on previous lessons to unlock.",
        'lesson_names': {
            'beginner': [
                "Introduction to Python",
                "Variables and Data Types",
                "Control Flow: If/Else Statements",
                "Loops: For and While",
                "Functions and Modules"
            ],
            'intermediate': [
                "Data Structures: Lists and Tuples",
                "Dictionaries and Sets",
                "File Handling",
                "Error Handling and Exceptions",
                "Object-Oriented Programming (OOP)"
            ],
            'advanced': [
                "Advanced Python Data Structures",
                "Decorators and Generators",
                "Regular Expressions (Regex)",
                "Multithreading and Multiprocessing",
                "Working with APIs and Web Scraping"
            ]
        },
        'final_quiz': "🧪 Final Quiz",
        'back': "🔙 Back",
        'home': "🏠 Home",
    },
    'fr': {
        'welcome': "Bienvenue à Ija T3alllem Python!",
        'menu': "Choisissez une option:",
        'learn': "📘 Apprendre Python",
        'progress': "🧪 Mon Progrès",
        'lang': "🌐 Changer de langue",
        'ide': "💻 Essayer Python (IDE)",
        'help': "📋 Aide",
        'choose_level': "Choisissez votre niveau:",
        'lessons_locked': "🔒 Verrouillé - Terminez les leçons précédentes",
        'lessons_list': "📚 Leçons pour {level}:",
        'quiz_locked': "🔒 Vous devez obtenir 5/5 pour débloquer.",
        'lesson_names': {
            'beginner': [
                "Introduction à Python",
                "Variables et types de données",
                "Contrôle de flux: Instructions If/Else",
                "Boucles: For et While",
                "Fonctions et Modules"
            ],
            'intermediate': [
                "Structures de données: Listes et Tuples",
                "Dictionnaires et Ensembles",
                "Gestion des fichiers",
                "Gestion des erreurs et exceptions",
                "Programmation orientée objet (POO)"
            ],
            'advanced': [
                "Structures de données avancées en Python",
                "Décorateurs et générateurs",
                "Expressions régulières (Regex)",
                "Multithreading et Multiprocessing",
                "Travail avec les API et le Web Scraping"
            ]
        },
        'final_quiz': "🧪 Quiz final",
        'back': "🔙 Retour",
        'home': "🏠 Accueil",
    },
    'ar': {
        'welcome': "مرحبًا بك في Ija T3alllem Python!",
        'menu': "اختر خيارًا:",
        'learn': "📘 تعلم بايثون",
        'progress': "🧪 تقدمي",
        'lang': "🌐 تغيير اللغة",
        'ide': "💻 جرب بايثون",
        'help': "📋 مساعدة",
        'choose_level': "اختر مستواك:",
        'lessons_locked': "🔒 مغلق - أكمل الدروس السابقة",
        'lessons_list': "📚 الدروس لـ {level}:",
        'quiz_locked': "🔒 تحتاج إلى 5/5 لفتح التالي.",
        'lesson_names': {
            'beginner': [
                "مقدمة في بايثون",
                "المتغيرات وأنواع البيانات",
                "التدفق الشرطي: جمل If/Else",
                "الحلقات: For و While",
                "الدوال والوحدات"
            ],
            'intermediate': [
                "الهياكل البيانية: القوائم وال tuples",
                "القواميس والمجموعات",
                "التعامل مع الملفات",
                "معالجة الأخطاء والاستثناءات",
                "البرمجة الكائنية التوجه (OOP)"
            ],
            'advanced': [
                "هياكل البيانات المتقدمة في بايثون",
                "الزخارف والمولدات",
                "التعبيرات العادية (Regex)",
                "المعالجة المتعددة والخيوط المتعددة",
                "العمل مع APIs وجمع البيانات من الإنترنت"
            ]
        },
        'final_quiz': "🧪 الاختبار النهائي",
        'back': "🔙 العودة",
        'home': "🏠 الرئيسية",
    }
}

# SQLite Setup
conn = sqlite3.connect('bot.db', check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, lang TEXT DEFAULT 'en', level TEXT DEFAULT 'beginner', lesson INTEGER DEFAULT 1, progress INTEGER DEFAULT 0)''')
conn.commit()

def get_user(user_id):
    c.execute("SELECT * FROM users WHERE id=?", (user_id,))
    user = c.fetchone()
    if not user:
        c.execute("INSERT INTO users (id) VALUES (?)", (user_id,))
        conn.commit()
        return get_user(user_id)
    return user

def update_lang(user_id, lang):
    c.execute("UPDATE users SET lang=? WHERE id=?", (lang, user_id))
    conn.commit()

def main_menu(lang):
    return ReplyKeyboardMarkup(
        [
            [
                KeyboardButton(LANG_TEXTS[lang]['learn']),
                KeyboardButton(LANG_TEXTS[lang]['progress'])
            ],
            [
                KeyboardButton(LANG_TEXTS[lang]['lang']),
                KeyboardButton(LANG_TEXTS[lang]['ide'])
            ],
            [
                KeyboardButton(LANG_TEXTS[lang]['help'])
            ]
        ],
        resize_keyboard=True,
        one_time_keyboard=False,
        input_field_placeholder=LANG_TEXTS[lang]['menu']
    )

def level_menu(lang, user_progress):
    def status(level_index):
        return "✅" if user_progress >= level_index * 100 else "🔒"
    return ReplyKeyboardMarkup(
        [
            [KeyboardButton(f"{status(0)} Beginner")],
            [KeyboardButton(f"{status(1)} Intermediate")],
            [KeyboardButton(f"{status(2)} Advanced")]
        ],
        resize_keyboard=True,
        one_time_keyboard=False
    )

def lessons_list(lang, level, user_progress):
    lesson_names = LANG_TEXTS[lang]['lesson_names'][level]
    lessons = []
    
    for i, lesson in enumerate(lesson_names):
        if i == 0 or user_progress >= (i * 100):
            lessons.append(KeyboardButton(lesson))  # Unlocked button
        else:
            lessons.append(KeyboardButton(f"🔒 {lesson}"))  # Locked text button (not tappable)
    
    if user_progress >= 500:  # Final quiz unlocked only after 5 lessons
        lessons.append(KeyboardButton(LANG_TEXTS[lang]['final_quiz']))
    
    # Organize into rows of 2 for better design
    rows = [lessons[i:i+2] for i in range(0, len(lessons), 2)]
    
    # Adding left menu buttons (Back, Change Lang, Home)
    rows.insert(0, [
        KeyboardButton(LANG_TEXTS[lang]['back']),
        KeyboardButton(LANG_TEXTS[lang]['home']),
        KeyboardButton(LANG_TEXTS[lang]['lang'])
    ])

    return f"{LANG_TEXTS[lang]['lessons_list'].format(level=level.title())}\n\n", ReplyKeyboardMarkup(rows, resize_keyboard=True, one_time_keyboard=False)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user = get_user(user_id)
    lang = user[1]
    await update.message.reply_text(
        LANG_TEXTS[lang]['welcome'] + f"\n\n{LANG_TEXTS[lang]['menu']}",
        reply_markup=main_menu(lang)
    )

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user = get_user(user_id)
    lang = user[1]
    text = update.message.text

    if text == LANG_TEXTS[lang]['learn']:
        await update.message.reply_text(
            LANG_TEXTS[lang]['choose_level'],
            reply_markup=level_menu(lang, user[4])
        )
    elif "Beginner" in text or "Intermediate" in text or "Advanced" in text:
        level = text.split()[1].lower()
        level_text, reply_markup = lessons_list(lang, level, user[4])
        await update.message.reply_text(level_text, reply_markup=reply_markup)
    elif text == LANG_TEXTS[lang]['lang']:
        flags = {
            'en': '🇬🇧',
            'fr': '🇫🇷',
            'ar': '🇹🇳'
        }
        langs = [[KeyboardButton(f"{flags[l]} {l.upper()}")] for l in LANGUAGES]
        reply_markup = ReplyKeyboardMarkup(langs, resize_keyboard=True, one_time_keyboard=True)
        await update.message.reply_text("Choose your language:", reply_markup=reply_markup)
    elif any(text.endswith(l.upper()) for l in LANGUAGES):
        chosen_lang = text[-2:].lower()
        update_lang(user_id, chosen_lang)
        await update.message.reply_text(LANG_TEXTS[chosen_lang]['welcome'], reply_markup=main_menu(chosen_lang))
    elif text == LANG_TEXTS[lang]['back']:
        await start(update, context)  # Navigate back to the main menu
    elif text == LANG_TEXTS[lang]['home']:
        
        await start(update, context)  # Navigate back to the home screen
    else:
        await update.message.reply_text(f"You selected: {text}")

if __name__ == '__main__':
    app = ApplicationBuilder().token(os.getenv("TELEGRAM_BOT_TOKEN")).build()

    app.add_handler(CommandHandler('start', start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    
    # print("Bot running...")
    # app.run_polling()   
    # keep your print
print("Bot running...")

# set your public URL and port
PORT = int(os.environ.get("PORT", 5000))
WEBHOOK_URL = "https://<your-render-app>.onrender.com/webhook"

# tell Telegram where to send updates
await app.bot.set_webhook(WEBHOOK_URL)

# start webhook listener instead of polling
app.run_webhook(
    listen="0.0.0.0",
    port=PORT,
    url_path="webhook",
    webhook_url=WEBHOOK_URL
)
