import re
from urllib.parse import urlparse, parse_qs
import vk_api
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from vk_api.utils import get_random_id
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
import back_bot
from config import TOKEN, ПРИВЕТСТВЕННОЕ_СООБЩЕНИЕ, ID_ГРУППЫ, ССЫЛКА_НА_ПОЛУЧЕНИЕ_ТОКЕНА, ВВЕСТИ_ССЫЛКУ_НА_ПОСТ, ВВЕСТИ_ИНТЕРВАЛ, ЗАПУСК, ТРЕБУЕТСЯ_ТОКЕН, \
    НЕ_ПОНИМАЮ, ВВЕСТИ_НОМЕР_ЧАТА, ВЫБЕРИТЕ_ДЕЙСТВИЕ, ВВЕДИТЕ_КОММЕНТАРИЙ


vk_session = vk_api.VkApi(token=TOKEN)
vk = vk_session.get_api()
longpoll = VkBotLongPoll(vk_session, ID_ГРУППЫ)

USER_TOKEN =''
LINK_ON_POST=''
INTERVAL = 0
ДЕЙСТВИЯ=''
КОММЕНТАРИЙ=''

def check_token():
    if USER_TOKEN == '':
        keyboard_3 = VkKeyboard(one_time=True)
        keyboard_3.add_button('Начать', color=VkKeyboardColor.POSITIVE)
        vk.messages.send(user_id=from_id, message=ТРЕБУЕТСЯ_ТОКЕН, random_id=get_random_id(),
                         keyboard=keyboard_3.get_keyboard())

for event in longpoll.listen():

    if event.type == VkBotEventType.MESSAGE_NEW:
        peer_id = event.object.message['peer_id']
        from_id = event.object.message['from_id']
        msg_text = event.object.message['text']
        ПОСЛЕДНЕЕ_СООБЩЕНИЕ_ОТ_БОТА = vk.messages.getHistory(count=2, peer_id= peer_id)['items'][1]['text']
        if msg_text == 'Начать':
            settings = dict(one_time=False, inline=True)
            keyboard_1 = VkKeyboard(**settings)
            vk.messages.send(user_id=from_id, message=ПРИВЕТСТВЕННОЕ_СООБЩЕНИЕ+"\n" +ССЫЛКА_НА_ПОЛУЧЕНИЕ_ТОКЕНА, random_id=get_random_id())

        elif (ПОСЛЕДНЕЕ_СООБЩЕНИЕ_ОТ_БОТА==ВВЕСТИ_ССЫЛКУ_НА_ПОСТ or\
              ПОСЛЕДНЕЕ_СООБЩЕНИЕ_ОТ_БОТА==ПРИВЕТСТВЕННОЕ_СООБЩЕНИЕ+"\n" + ССЫЛКА_НА_ПОЛУЧЕНИЕ_ТОКЕНА) and urlparse(msg_text).scheme != "":
              try:
                 parsed_url = urlparse(msg_text.replace('#', '?'))
                 USER_TOKEN = parse_qs(parsed_url.query)['access_token'][0]
                 vk.messages.send(user_id=from_id, message=ВВЕСТИ_ССЫЛКУ_НА_ПОСТ, random_id=get_random_id())
              except:
                  LINK_ON_POST = msg_text
                  vk.messages.send(user_id=from_id, message=ВВЕСТИ_ИНТЕРВАЛ, random_id=get_random_id())
        elif ПОСЛЕДНЕЕ_СООБЩЕНИЕ_ОТ_БОТА == ВВЕСТИ_ИНТЕРВАЛ and msg_text.isnumeric():
            check_token()
            INTERVAL = int(msg_text)
            vk.messages.send(user_id=from_id, message=ВВЕСТИ_НОМЕР_ЧАТА, random_id=get_random_id())
        elif ПОСЛЕДНЕЕ_СООБЩЕНИЕ_ОТ_БОТА==ЗАПУСК and msg_text == 'Запустить бота!':
            check_token()
            b = back_bot.Bot(USER_TOKEN, INTERVAL, LINK_ON_POST, CHAT_ID, vk, event, longpoll, ДЕЙСТВИЯ, КОММЕНТАРИЙ)
            b.start()
        elif ПОСЛЕДНЕЕ_СООБЩЕНИЕ_ОТ_БОТА==ВВЕСТИ_НОМЕР_ЧАТА and re.match(r'c\d+', msg_text):
            CHAT_ID = msg_text[1:]
            vk.messages.send(user_id=from_id, message=ВЫБЕРИТЕ_ДЕЙСТВИЕ, random_id=get_random_id())
        elif ПОСЛЕДНЕЕ_СООБЩЕНИЕ_ОТ_БОТА==ВЫБЕРИТЕ_ДЕЙСТВИЕ and re.match(r'[1234]', msg_text) :
            ДЕЙСТВИЯ = msg_text.split(' ')
            if '4' in ДЕЙСТВИЯ:
                vk.messages.send(user_id=from_id, message=ВВЕДИТЕ_КОММЕНТАРИЙ, random_id=get_random_id())
            else:
                keyboard_2 = VkKeyboard(one_time=True)
                keyboard_2.add_button('Запустить бота!', color=VkKeyboardColor.POSITIVE)
                vk.messages.send(user_id=from_id, message=ЗАПУСК, random_id=get_random_id(),
                                 keyboard=keyboard_2.get_keyboard())
        elif ПОСЛЕДНЕЕ_СООБЩЕНИЕ_ОТ_БОТА==ВВЕДИТЕ_КОММЕНТАРИЙ:
            КОММЕНТАРИЙ=msg_text
            keyboard_2 = VkKeyboard(one_time=True)
            keyboard_2.add_button('Запустить бота!', color=VkKeyboardColor.POSITIVE)
            vk.messages.send(user_id=from_id, message=ЗАПУСК, random_id=get_random_id(),
                             keyboard=keyboard_2.get_keyboard())
        else:
            vk.messages.send(user_id=from_id, message=НЕ_ПОНИМАЮ, random_id=get_random_id())
            vk.messages.send(user_id=from_id, message=ПОСЛЕДНЕЕ_СООБЩЕНИЕ_ОТ_БОТА, random_id=get_random_id())

# сообщения, информация, друзья,
