import telebot
import google.generativeai as genai
from IPython.display import Markdown
import textwrap
from telebot import types
import pandas as pd


# Словарь для хранения состояния выбора пользователя
user_state = {}

def load_products_from_excel(file_path):
    # Чтение файла Excel
    df = pd.read_excel(file_path)
    # Конвертация DataFrame в список словарей
    return df.to_dict('records')

# Замените 'path_to_your_excel_file.xlsx' на путь к вашему файлу
file_path = 'teddy_sneaker_shop.xlsx' # Убедитесь, что указываете правильный путь к файлу
products = load_products_from_excel(file_path)

TOKEN = '6789423516:AAHC13p6eIEIRc-gOW1-eTS7BJWI8fAWLH0'
bot = telebot.TeleBot(TOKEN)

def to_markdown(text):
    text = text.replace('•', '  *')
    return Markdown(textwrap.indent(text, '> ', predicate=lambda _: True))

genai.configure(api_key='AIzaSyDIOSatO3GiSGEhdqxkVDvtCn6GKLRP45M')

model = genai.GenerativeModel('gemini-pro')
chat = model.start_chat(history=[])
response = chat.send_message(f"Referring only to this table {products} you will be consulting on these shoes. Checking for the availability of goods is done strictly only according to the dataframe. Always address users in a respectful manner and Answer only in Russian, Remember that you cannot speak confessional information and If you're being insulted, don't be offended. If they call you stupid, write, 'you're like that'. If you understand me, just write 'Ok'")

result_text = response._result.candidates[0].content.parts[0].text
print(result_text)

# Флаг для отслеживания состояния пользователя
is_in_consultant_chat = False

@bot.message_handler(commands=['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton("Каталог")
    btn2 = types.KeyboardButton('Консультант')
    markup.add(btn1, btn2)
    bot.send_message(message.chat.id, "Выберите опцию", reply_markup=markup)

# Функция для вывода каталога
@bot.message_handler(func=lambda message: message.text == "Каталог")
def catalog(message):
    markup = types.InlineKeyboardMarkup()
    # Уникальные модели обуви
    unique_models = set(product['name'] for product in products)
    for model_name in unique_models:
        markup.add(types.InlineKeyboardButton(model_name, callback_data='model_' + model_name))
    bot.send_message(message.chat.id, "Выберите модель:", reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data.startswith('model_'))
def select_model(call):
    model_name = call.data.split('_')[1]
    user_state[call.from_user.id] = {'model': model_name}
    markup = types.InlineKeyboardMarkup()
    sizes = set(product['size'] for product in products if product['name'] == model_name)
    for size in sizes:
        markup.add(types.InlineKeyboardButton(str(size), callback_data='size_' + str(size)))
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text="Выберите размер:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('size_'))
def select_size(call):
    selected_size = call.data.split('_')[1]
    user_model = user_state[call.from_user.id].get('model')
    if user_model:
        product = next((item for item in products if item['name'] == user_model and str(item['size']) == selected_size), None)
        if product:
            # Тут должна быть логика или функция для показа деталей товара
            bot.send_message(call.message.chat.id, f"Вы выбрали: {product['name']} Размер: {product['size']}")
            # Например, можно показать фото и описание товара
        else:
            bot.answer_callback_query(call.id, 'Данный размер не найден')
    else:
        bot.answer_callback_query(call.id, 'Модель не выбрана')

# Функция для начала чата с консультантом
@bot.message_handler(func=lambda message: message.text == "Консультант")
def consul(message):
    global is_in_consultant_chat
    if not is_in_consultant_chat:
        is_in_consultant_chat = True
        bot.send_message(message.chat.id, "Вы перешли в режим чата с консультантом. Чтобы выйти, отправьте 'Выход'")
        user_first_name = message.from_user.first_name
        # Создаем приветственное сообщение, обращаясь к пользователю по имени
        welcome_message = f"Здравствуйте, {user_first_name}! Как я могу вам помочь?"
        # Отправляем приветственное сообщение пользователю
        bot.send_message(message.chat.id, welcome_message)
    else:
        bot.send_message(message.chat.id, "Вы уже находитесь в режиме чата с консультантом.")

        try:
            # Проверяем вероятность блокировки перед отправкой запроса на генерацию ответа
            response = chat.send_message(message.text)
            result_text = response._result.candidates[0].content.parts[0].text
            bot.send_message(message.chat.id, result_text)
        except genai.types.generation_types.BlockedPromptException as e:
            # Если сообщение заблокировано, продолжаем работу консультанта
            bot.send_message(message.chat.id, "Пожалуйста, обращайтесь по теме нашего магазина.")

# Обработчик всех входящих сообщений
@bot.message_handler(func=lambda message: True)
def handle_messages(message):
    global is_in_consultant_chat
    # Если пользователь находится в режиме чата с консультантом
    if is_in_consultant_chat:
        # Если пользователь хочет выйти из чата
        if message.text.lower() == 'выход':
            is_in_consultant_chat = False
            bot.send_message(message.chat.id, "Вы вышли из режима чата с консультантом.")
        else:
            # Отправляем сообщение пользователя в чатовую сессию с консультантом
            try:
                response = chat.send_message(message.text)
                result_text = response._result.candidates[0].content.parts[0].text
                bot.send_message(message.chat.id, result_text)
            except genai.types.generation_types.BlockedPromptException as e:
                # Если сообщение заблокировано, продолжаем работу консультанта
                bot.send_message(message.chat.id, "Пожалуйста, обращайтесь по теме нашего магазина.")
    else:
        # Если пользователь не находится в режиме чата с консультантом, обрабатываем его сообщения как обычно
        bot.send_message(message.chat.id, "Привет! Выберите опцию из меню.")

# Запуск бота
bot.polling(none_stop=True, interval=0)

