from aiogram import Bot
from aiogram import Dispatcher
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

import requests
import json
import asyncio
from time import sleep


data_file = 'data.json'  # Файл с данными
config = json.load(open(data_file))  # Загружаем данные в config

#### TWITCH ####
TOKEN = config["api"]['token']  # Токен доступа
client_secret = config["api"]['client_secret']  # Секретный ключ
client_id = config["api"]["client_id"]  # ID клиента

#### TG BOT CONFIG ####
bot = Bot(token=config["tg-bot"]["token"])  # Токен бота
dp = Dispatcher(bot = bot) # Диспетчер

def DataUpdate() -> None:
    """Функция обновляет данные"""

    with open(data_file, 'w') as f:
        json.dump(config, f)  # записываем все изменения в файл с данными

def GetToken() -> str:
    """Функция делает запрос в твич-апи и возвращает токен"""

    response = requests.post(
        'https://id.twitch.tv/oauth2/token',
        data={
            'client_id': client_id,
            'client_secret': client_secret,
            'grant_type': 'client_credentials'
        }
    )  # делаем запрос на получение токена

    # если ответ получен успешно, то сохраняем токен в переменную TOKEN
    if response.status_code == 200:
        response_json = response.json()
        TOKEN = response_json['access_token']

    return TOKEN  # возвращаем токен


def UpdateToken() -> None:
    """Функция обновляет токен доступа для твич-апи"""

    global TOKEN  # делаем TOKEN глобальной переменной

    config["api"]["token"] = TOKEN = GetToken()  # сохраняем новый токен
    DataUpdate()


def GetButton(url: str) -> InlineKeyboardMarkup:
    """Функция создает и возвращает кнопку"""

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text='СМОТРЕТЬ СТРИМ', url=url) # Кнопка
        ]
    ]) # создаем саму клавиатуру

    return keyboard


def stream_status(channel: str) -> bool and list:
    """Функция проверяет состояние стрима на канале (стримит или нет)"""

    status = bool(False)

    while (attempts := 0) < 3:
        try:
            response = requests.get(f"https://api.twitch.tv/helix/streams?user_login={channel}",
                                    headers={
                                        'Client-ID': client_id,
                                        'Authorization': 'Bearer ' + TOKEN
            }
            )  # Запрос к твич-апи (спрашиваем идет ли стрим)

            break
        # Если не получилось получить ответ, то обновляем токен
        except UnboundLocalError:
            UpdateToken()

        attempts += 1  # Увеличиваем счетчик попыток

    # Если получилось получить ответ (200 - успешный запрос и ответ получен)
    if response.status_code == 200:
        data = response.json()  # Сохраняем полученные данные

        if len(data['data']) > 0:  # Если есть данные
            if not status:
                # Действия по началу стрима
                ...
                #
            status = True
        else:
            if status:
                # Действия по окончанию стрима
                ...
                #
            status = False

        # Возвращаем статус стрима и данные если стрим идет
        return status, data['data'][0] if status == True else None

    # Если имя канала не существует (400 - Неверный запрос)
    elif response.status_code == 400:
        return NameError('Несуществующее имя канала')
    # Если токен устарел (401 - Ошибка авторизации/не авторизован)
    elif response.status_code == 401:
        UpdateToken()  # Обновляем токен
    else:
        return Warning('Неизвестная ошибка')


async def send(chat_id: int, text: str, url: str):
    keyboard = InlineKeyboardMarkup()
    button = InlineKeyboardButton('СМОТРЕТЬ СТРИМ', url=url)
    keyboard.add(button)

    await bot.send_message(chat_id=owner_id, text=text, parse_mode="HTML", disable_web_page_preview=True, reply_markup=keyboard)

async def main():
    online = list()
    while True:
        for user_id, subs in config["users"].items():
            user_id = int(user_id)
            if not subs == []:
                for sub in subs:

                    status, info = stream_status(sub)

                    if not (info is None) and sub not in online:
                        keyboard = GetButton(f"https://twitch.tv/{info['user_login']}")
                        text = f'🔸<b><i>{info["user_name"]}</i></b> стримит🔸\n<b>Название стрима:</b> {info["title"]}\n<b>Тема:</b> {"Общение" if info["game_name"] == "Just Chatting" else info["game_name"]}'

                        await bot.send_message(chat_id=user_id, text=text, parse_mode="HTML", disable_web_page_preview=True, reply_markup=keyboard)

                        online.append(sub)
                    elif info is None and sub in online:
                        online.remove(sub)
            else:
                continue

        sleep(1 * 60)

if __name__ == "__main__":
    asyncio.run(main())
