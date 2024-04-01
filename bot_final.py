import telebot
from telebot import types
import textwrap
import google.generativeai as genai
from IPython.display import Markdown

TOKEN = '6789423516:AAHC13p6eIEIRc-gOW1-eTS7BJWI8fAWLH0'
bot = telebot.TeleBot(TOKEN)

def to_markdown(text):
    text = text.replace('•', '  *')
    return Markdown(textwrap.indent(text, '> ', predicate=lambda _: True))

genai.configure(api_key='AIzaSyDIOSatO3GiSGEhdqxkVDvtCn6GKLRP45M')

model = genai.GenerativeModel('gemini-pro')
chat = model.start_chat(history=[])



response = chat.send_message("Привет ты будешь консультантом по обуви, если ты меня понял просто напиши 'Принял!'")
result_text = response._result.candidates[0].content.parts[0].text
print(result_text)


# Предполагается, что данные о товарах загружены заранее и хранятся в списке словарей
products = [
    {'name': 'Тапочки Gucci', 'size': 'EU 37', 'price': '15000', 'photo': 'https://storage.yandexcloud.net/cdn-prod.viled.kz/v3/original/2500129NiTj.jpeg'},
    # Добавьте остальные продукты по аналогии
]

@bot.message_handler(commands=['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton("Каталог")
    btn2 = types.KeyboardButton('Консультант')
    markup.add(btn1, btn2)
    bot.send_message(message.chat.id, "Выберите опцию", reply_markup=markup)

@bot.message_handler(func=lambda message: message.text == "Каталог")
def catalog(message):
    markup = types.InlineKeyboardMarkup()
    for product in products:
        markup.add(types.InlineKeyboardButton(product['name'], callback_data='product_' + product['name']))
    bot.send_message(message.chat.id, "Выберите продукт:", reply_markup=markup)

@bot.message_handler(func=lambda message: message.text == "Консультант")
def consul(message):
    user_input = message.text
    response = chat.send_message(user_input)
    result_text = response._result.candidates[0].content.parts[0].text
    bot.reply_to(message, result_text)


@bot.callback_query_handler(func=lambda call: call.data.startswith('product_'))
def show_product(call):
    product_name = call.data.split('_')[1]
    product = next((item for item in products if item['name'] == product_name), None)
    if product:
        bot.send_photo(call.message.chat.id, product['photo'], caption=f"{product['name']}\nРазмер: {product['size']}\nЦена: {product['price']}")
    else:
        bot.answer_callback_query(call.id, 'Товар не найден')

bot.polling(none_stop=True, interval=0)