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
    for product in products:
        markup.add(types.InlineKeyboardButton(product['name'] + ' ' + str(product['size']), callback_data='product_' + product['name']))
    bot.send_message(message.chat.id, "Выберите продукт:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('product_'))
def show_product(call):
    product_name = call.data.split('_')[1]
    product = next((item for item in products if item['name'] == product_name), None)
    if product:
        prompt1 = chat.send_message("Write a short description of only 20 words (Approximately). Add to the description: the Popularity scale (from 0 to 10), which style is combined with Strength (from 0 to 10). Answer only in Russian.")
        response = chat.send_message(f"Описание товара {product['name']}")
        description = response._result.candidates[0].content.parts[0].text

        bot.send_photo(call.message.chat.id, product['photo'], caption=f"{product['name']}\nРазмер: {product['size']}\nЦена: {product['price']}\nОписание: {description}")
    else:
        bot.answer_callback_query(call.id, 'Товар не найден')

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
