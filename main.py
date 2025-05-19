import telebot
from telebot import types
from config import BOT_TOKEN
from logger import DialogLogger
from parser import NewsParser
import os

# Инициализация бота и модулей
bot = telebot.TeleBot(BOT_TOKEN)
logger = DialogLogger()
parser = NewsParser()


def create_main_keyboard():
    """Создаёт основную клавиатуру с кнопками"""
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    buttons = [
        types.KeyboardButton('📰 Последние новости'),
        types.KeyboardButton('🔍 Поиск новостей'),
        types.KeyboardButton('📂 Категории'),
        types.KeyboardButton('ℹ️ Помощь')
    ]
    keyboard.add(*buttons)
    return keyboard


def log_and_send(chat_id, text, username=None, **kwargs):
    """
    Логирует и отправляет сообщение
    :param chat_id: ID чата
    :param text: Текст сообщения
    :param username: Имя пользователя (для логирования)
    :param kwargs: Доп. параметры для send_message
    """
    try:
        # Логируем исходящее сообщение
        logger.log_message(
            user_id=chat_id,
            username="BOT",
            message=text,
            is_bot=True
        )

        # Отправляем сообщение
        return bot.send_message(chat_id, text, **kwargs)
    except Exception as e:
        print(f"Ошибка отправки сообщения: {e}")


@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    """Обработчик команд /start и /help"""
    welcome_text = """
    📰 <b>Новостной бот РБК</b> 📰

    Выберите действие:
    - 📰 Последние новости: 5 свежих новостей с rbc.ru
    - 🔍 Поиск новостей: Найти новости по теме
    - 📂 Категории: Бизнес, технологии и др.
    - ℹ️ Помощь: Как пользоваться ботом
    """

    # Логируем входящее сообщение
    logger.log_message(
        user_id=message.from_user.id,
        username=message.from_user.username,
        message=message.text
    )

    log_and_send(
        message.chat.id,
        welcome_text,
        parse_mode='HTML',
        reply_markup=create_main_keyboard()
    )


@bot.message_handler(func=lambda msg: msg.text == '📰 Последние новости')
def send_latest_news(message):
    """Обработчик кнопки последних новостей"""
    try:
        # Логируем запрос
        logger.log_message(
            user_id=message.from_user.id,
            username=message.from_user.username,
            message=message.text
        )

        bot.send_chat_action(message.chat.id, 'typing')
        news = parser.parse_rbc_news()

        if not news:
            log_and_send(
                message.chat.id,
                "😕 Не удалось загрузить новости. Попробуйте позже.",
                reply_markup=create_main_keyboard()
            )
            return

        for item in news:
            news_text = f"""
            <b>{item['title']}</b>
            <i>{item['time']}</i>\n
            {item['text']}
            <a href="{item['url']}">Читать полностью →</a>
            """
            log_and_send(
                message.chat.id,
                news_text,
                parse_mode='HTML',
                disable_web_page_preview=True
            )

        log_and_send(
            message.chat.id,
            "Выберите следующее действие:",
            reply_markup=create_main_keyboard()
        )
    except Exception as e:
        print(f"Ошибка: {e}")
        log_and_send(
            message.chat.id,
            "⚠️ Ошибка при получении новостей",
            reply_markup=create_main_keyboard()
        )


@bot.message_handler(func=lambda msg: msg.text == '🔍 Поиск новостей')
def ask_search_term(message):
    """Обработчик кнопки поиска"""
    logger.log_message(
        user_id=message.from_user.id,
        username=message.from_user.username,
        message=message.text
    )

    msg = log_and_send(
        message.chat.id,
        "🔍 Введите ключевое слово для поиска:",
        reply_markup=types.ReplyKeyboardRemove()
    )
    bot.register_next_step_handler(msg, process_search_term)


def process_search_term(message):
    """Обработка поискового запроса"""
    try:
        logger.log_message(
            user_id=message.from_user.id,
            username=message.from_user.username,
            message=message.text
        )

        bot.send_chat_action(message.chat.id, 'typing')
        news = parser.get_news_by_keyword(message.text)

        if not news:
            log_and_send(
                message.chat.id,
                f"По запросу '{message.text}' ничего не найдено.",
                reply_markup=create_main_keyboard()
            )
            return

        for item in news[:3]:  # Показываем первые 3 результата
            news_text = f"""
            <b>{item['title']}</b> ({item['source']})
            {item['summary']}
            <a href="{item['url']}">Читать полностью →</a>
            """
            log_and_send(
                message.chat.id,
                news_text,
                parse_mode='HTML',
                disable_web_page_preview=True
            )

        log_and_send(
            message.chat.id,
            "Выберите следующее действие:",
            reply_markup=create_main_keyboard()
        )
    except Exception as e:
        print(f"Ошибка поиска: {e}")
        log_and_send(
            message.chat.id,
            "⚠️ Ошибка при поиске новостей",
            reply_markup=create_main_keyboard()
        )


@bot.message_handler(func=lambda msg: msg.text == '📂 Категории')
def show_categories(message):
    """Показывает категории новостей"""
    logger.log_message(
        user_id=message.from_user.id,
        username=message.from_user.username,
        message=message.text
    )

    categories = parser.get_news_categories()
    keyboard = types.InlineKeyboardMarkup(row_width=2)

    for category in categories:
        keyboard.add(
            types.InlineKeyboardButton(
                text=category.capitalize(),
                callback_data=f"cat_{category}"
            )
        )

    log_and_send(
        message.chat.id,
        "📂 Выберите категорию новостей:",
        reply_markup=keyboard
    )


@bot.callback_query_handler(func=lambda call: call.data.startswith('cat_'))
def handle_category(call):
    """Обработчик выбора категории"""
    try:
        category = call.data.split('_')[1]
        logger.log_message(
            user_id=call.from_user.id,
            username=call.from_user.username,
            message=f"Выбрана категория: {category}"
        )

        bot.answer_callback_query(call.id, f"Загружаем {category}...")
        bot.send_chat_action(call.message.chat.id, 'typing')

        news = parser.get_news_by_category(category)

        if not news:
            log_and_send(
                call.message.chat.id,
                f"Новости категории '{category}' не найдены.",
                reply_markup=create_main_keyboard()
            )
            return

        for item in news[:3]:  # Показываем первые 3 новости
            news_text = f"""
            <b>{item['title']}</b> ({item['source']})
            {item['summary']}
            <a href="{item['url']}">Читать полностью →</a>
            """
            log_and_send(
                call.message.chat.id,
                news_text,
                parse_mode='HTML',
                disable_web_page_preview=True
            )

        log_and_send(
            call.message.chat.id,
            "Выберите следующее действие:",
            reply_markup=create_main_keyboard()
        )
    except Exception as e:
        print(f"Ошибка категории: {e}")
        log_and_send(
            call.message.chat.id,
            "⚠️ Ошибка при загрузке категории",
            reply_markup=create_main_keyboard()
        )


@bot.message_handler(func=lambda msg: msg.text == 'ℹ️ Помощь')
def send_help(message):
    """Обработчик кнопки помощи"""
    help_text = """
    ℹ️ <b>Справка по использованию бота</b>

    <b>📰 Последние новости</b> - 5 свежих новостей с rbc.ru
    <b>🔍 Поиск новостей</b> - поиск по ключевому слову
    <b>📂 Категории</b> - новости по категориям

    После выполнения команды бот вернёт вас в главное меню.
    """

    logger.log_message(
        user_id=message.from_user.id,
        username=message.from_user.username,
        message=message.text
    )

    log_and_send(
        message.chat.id,
        help_text,
        parse_mode='HTML',
        reply_markup=create_main_keyboard()
    )


@bot.message_handler(func=lambda msg: True)
def log_all_messages(message):
    """Логирует все входящие сообщения"""
    logger.log_message(
        user_id=message.from_user.id,
        username=message.from_user.username,
        message=message.text
    )


if __name__ == '__main__':
    # Проверяем и создаем папку для логов
    if not os.path.exists('user_logs'):
        os.makedirs('user_logs')

    print("Бот запущен и готов к работе!")
    bot.infinity_polling()