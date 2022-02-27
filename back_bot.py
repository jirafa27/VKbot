import json
import re
import time
import requests
import vk_api
from vk_api.bot_longpoll import VkBotEventType
from vk_api.longpoll import VkLongPoll, VkEventType
import threading
from vk_api.utils import get_random_id


class Bot:
    """
    Базовый класс бота ВКонтакте
    """

    # текущая сессия ВКонтакте
    vk_session = None
    # доступ к API ВКонтакте
    vk_api_access = None
    # авторизован ли юзер
    authorized = False
    # токен пользователя
    USER_TOKEN = ""
    # интервал постинга
    INTERVAL = 0
    # ссылка для постинга
    LINK_FOR_POSTING = ""
    # Идентификатор чата для постинга
    CHAT_ID = 0
    # лонгпул бэкенд бота
    long_poll = None
    # сессия главного бота
    SESSION_OF_MAIN_BOT = ""
    # событие от главного бота
    EVENT = ""
    # лонгпул главного бота
    LONGPOLL = ''
    # что нужно сделать бекэнд боту
    ДЕЙСТВИЯ = []
    # коммент для постинга
    КОММЕНТАРИЙ = ''

    def __init__(self, user_token, interval, link_for_posting, chat_id, session_of_main_bot, event, longpoll, действия,
                 комментарий):
        """
        Инициализация бота при помощи получения доступа к API ВКонтакте
        """
        # авторизация
        self.USER_TOKEN = user_token
        self.INTERVAL = interval
        self.LINK_FOR_POSTING = link_for_posting
        self.vk_api_access = self.do_auth()
        if self.vk_api_access is not None:
            self.authorized = True
        self.long_poll = VkLongPoll(self.vk_session)
        self.SESSION_OF_MAIN_BOT = session_of_main_bot
        self.EVENT = event
        self.LONGPOLL = longpoll
        self.CHAT_ID = int(chat_id)
        self.ДЕЙСТВИЯ = действия
        self.КОММЕНТАРИЙ = комментарий

    def do_auth(self):
        """
        Авторизация за пользователя (не за группу или приложение)
        Использует переменную, хранящуюся в файле настроек окружения .env в виде строки ACCESS_TOKEN="1q2w3e4r5t6y7u8i9o..."
        :return: возможность работать с API
        """
        try:
            self.vk_session = vk_api.VkApi(token=self.USER_TOKEN)
            return self.vk_session.get_api()
        except Exception as error:
            print(error)
            return None

    def send_message(self, chat_id, message_text: str = "тестовое сообщение"):
        """Отправка сообщения от имени пользователя"""
        if not self.authorized:
            print("Unauthorized. Check if ACCESS_TOKEN is valid")
            return

        try:
            self.vk_api_access.messages.send(message=message_text, random_id=get_random_id(), chat_id=chat_id)
            print(f"Сообщение отправлено для ID {chat_id} с текстом: {message_text}")
        except Exception as error:
            print(error)

    def send_captcha(self, captcha):
        """Отправка капчи в от имени главного бота в личку юзеру"""
        data = self.SESSION_OF_MAIN_BOT.photos.getMessagesUploadServer(user_id=self.EVENT.object.message['from_id'])
        upload_url = data["upload_url"]
        p = requests.get(captcha.get_url())
        out = open("img.jpg", "wb")
        out.write(p.content)
        out.close()
        files = {'photo': open("img.jpg", 'rb')}

        response = requests.post(upload_url, files=files)
        result = json.loads(response.text)
        uploadResult = self.vk_api_access.photos.saveMessagesPhoto(server=result["server"],
                                                                   photo=result["photo"],
                                                                   hash=result["hash"])
        captcha_key = ""
        for event in self.LONGPOLL.listen():
            if event.type == VkBotEventType.MESSAGE_NEW:
                captcha_key = event.object.message['text']
                break
        return captcha_key

        self.SESSION_OF_MAIN_BOT.messages.send(user_id=self.EVENT.object.message['from_id'],
                                               message="randomTextMessage",
                                               attachment='photo' + str(
                                                   self.EVENT.object.message['from_id']) + '_' + str(
                                                   uploadResult[0]["id"]), random_id=0)

    def check_frequency(self):
        history = self.vk_api_access.messages.getHistory(count=20, peer_id=2000000000 + self.CHAT_ID)
        count = 0
        for m in history['items']:
            print(m['from_id'])
            if count == 5:
                return False
            if m['from_id'] == self.EVENT.object.message['from_id']:
                print('Есть моя запись')
                print(m['from_id'], self.EVENT.object.message['from_id'])
                return True
            if str(m['from_id'])[0] != '-':
                count += 1
        return False

    def do(self):
        while self.check_frequency():
            print('Ждем 5 минут')
            time.sleep(300)
        self.send_message(self.CHAT_ID, self.LINK_FOR_POSTING)
        try:
            for event in self.long_poll.listen():
                if event.type == VkEventType.MESSAGE_NEW:
                    if event.peer_id % 1000 == self.CHAT_ID:
                        if event.to_me:
                            text = event.text
                            if '1' or '2' in self.ДЕЙСТВИЯ:
                                if '@club' in text:
                                    groups = re.findall(r"@club\d+", text)
                                    for group in groups:
                                        try:
                                            if '1' in self.ДЕЙСТВИЯ:
                                                try:
                                                    self.vk_api_access.groups.join(group_id=group[5:])
                                                    print("Вступление в группу " + group)
                                                except vk_api.exceptions.Captcha as captcha:
                                                    captcha_key = self.send_captcha(captcha)
                                                    self.vk_api_access.groups.join(group_id=group[5:],
                                                                                   captcha_sid=captcha.sid,
                                                                                   captcha_key=captcha_key)
                                                    time.sleep(5)
                                        except Exception as Error:
                                            print(Error)
                                            if '2' in self.ДЕЙСТВИЯ:
                                                records = self.vk_api_access.wall.get(owner_id=int("-" + group[5:]))[
                                                    'items']
                                                for i in range(10):
                                                    print('Лайк на пост ', records[i]['id'])
                                                    time.sleep(2)
                                                    try:
                                                        self.vk_api_access.likes.add(owner_id=int("-" + group[5:]),
                                                                                     item_id=records[i]['id'],
                                                                                     type='post')
                                                    except vk_api.exceptions.Captcha as captcha:
                                                        captcha_key = self.send_captcha(captcha)
                                                        self.vk_api_access.likes.add(owner_id=int("-" + group[5:]),
                                                                                     item_id=records[i]['id'],
                                                                                     type='post',
                                                                                     captcha_sid=captcha.sid,
                                                                                     captcha_key=captcha_key)
                                                        time.sleep(5)
                                                    except Exception as Error:
                                                        print(Error)
                                        except Exception as error:
                                            print(error)
                            if '3' in self.ДЕЙСТВИЯ:

                                if 'wall' in text:
                                    links = re.findall(r'wall-?\d+_\d+', text)
                                    print(links)
                                    for link in links:
                                        owner_id = int(link[link.find('wall') + 4: link.find('_')])
                                        item_id = int(link.split("_")[1])
                                        print("item_id ", item_id)
                                        print('owner_id', owner_id)
                                        self.vk_api_access.likes.add(item_id=item_id, type='post', owner_id=owner_id)
                                        print('Поставлен лайк, владелец: ' + str(owner_id) + " пост " + str(item_id))

                            if '4' in self.ДЕЙСТВИЯ:

                                if 'wall' in text:
                                    links = re.findall(r'wall-?\d+_\d+', text)
                                    print(links)
                                    for link in links:
                                        owner_id = int(link[link.find('wall') + 4: link.find('_')])
                                        item_id = int(link.split("_")[1])
                                        print("item_id ", item_id)
                                        print('owner_id', owner_id)
                                        self.vk_api_access.wall.createComment(post_id=item_id, owner_id=owner_id,
                                                                              message=self.КОММЕНТАРИЙ,
                                                                              guid=get_random_id())
                                        print('Добавлен комментарий, владелец: ' + str(owner_id) + " пост " + str(
                                            item_id) + " текст " + self.КОММЕНТАРИЙ)

                            while self.check_frequency():
                                print('Ждем 5 минут')
                                time.sleep(300)
                            self.send_message(self.CHAT_ID, self.LINK_FOR_POSTING)
        except Exception as Error:
            print(Error)

    def start(self):
        self.do()
        threading.Timer(self.INTERVAL * 60, self.do).start()

# чтобы бот показывал чей аккаунт
# команда отмена
# не отвечает не на команды
# буквы разные
# кнопки убрать
# !Взаимность в самом начале
# несколько юзеров
