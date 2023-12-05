from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher
from aiogram.utils import executor
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
owners_id = [437660082, 1710515030]  # ID владельцев бота (Максим, Вика)
bot = Bot(token='6164927415:AAEXyT-bYBfjghxdOCiw0YPd5THdwM_FGqQ')  # Токен бота
dp = Dispatcher(bot) # Диспетчер

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

    keyboard = InlineKeyboardMarkup() # создаем саму клавиатуру
    button = InlineKeyboardButton('СМОТРЕТЬ СТРИМ', url=url)
    keyboard.add(button)

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
        return status, data['data'] if status == True else None

    # Если имя канала не существует (400 - Неверный запрос)
    elif response.status_code == 400:
        return NameError('Несуществующее имя канала')
    # Если токен устарел (401 - Ошибка авторизации/не авторизован)
    elif response.status_code == 401:
        UpdateToken()  # Обновляем токен
    else:
        return Warning('Неизвестная ошибка')

# await bot.send_message(chat_id=owner_id, text=text, parse_mode="HTML", disable_web_page_preview=True, reply_markup=keyboard)

def main():
    while True:
        for user_id, subs in config["users"].items():
            user_id = int(user_id)
            if not subs == []:
                for sub in subs:
                    status, info = is_online(sub)
                    if len(data['data']) > 0 and sub not in status:
                        status.append(sub)
                        await bot.send_message(user_id, text, keyboard = GetButton(f"https://twitch.tv/{info[user_name]}"))
                    elif len(data['data']) == 0 and sub in status:
                        status.remove(sub)
                    # Если стример онлайн и не в списке online:
                    #     Говорим, что стрим начался, добавляем кнопку
                    #     Добавляем в список online
                    # Если стример не стримит, но есть в online:
                    #     Удаляем из списка стримящих
#                     info["title"] - Название стрима
# info["user_name"] - ник стримера
# info["'game_name'"] - тема стрима     
            else:
                continue
