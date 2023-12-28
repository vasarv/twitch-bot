from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters.command import Command
from aiogram import Bot, Dispatcher, types

import requests
import json
import asyncio
from time import sleep
import multiprocessing

Private = False  # False - публичный режим | True - приватный режим

#### DATA ####
DataFile = 'data.json'  # Файл с данными
Config = json.load(open(DataFile))  # Загружаем данные в Config

#### TWITCH ####
TOKEN = Config["api"]['token']  # Токен доступа
client_secret = Config["api"]['client_secret']  # Секретный ключ
client_id = Config["api"]["client_id"]  # ID клиента

#### TG BOT Config ####
owners_id = []  # ID владельцев бота (Учитываются, если Private == True)
bot = Bot(token=Config["tg-bot"]["token"])  # Токен бота
dp = Dispatcher(bot=bot)  # Диспетчер


def DataUpdate(data, file: str = DataFile) -> None:
    """Функция обновляет данные в БД"""

    with open(file, 'w') as f:
        json.dump(data, f)  # записываем все изменения в файл с данными


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

    Config["api"]["token"] = TOKEN = GetToken()  # сохраняем новый токен
    DataUpdate(Config)


def GetButton(url: str) -> InlineKeyboardMarkup:
    """Функция создает и возвращает кнопку"""

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text='СМОТРЕТЬ СТРИМ', url=url)  # Кнопка
        ]
    ])  # создаем саму клавиатуру

    return keyboard


def is_owner(message):
    id = message.chat.id
    return True if (Private and id in owners_id) or (Private == False) else False


def is_valid(channel: str):
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

    # Если имя канала не существует (400 - Неверный запрос)
    if response.status_code == 400:
        return False
    else:
        return True


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


@dp.message(Command('add_sub'))
async def add_sub(message: types.Message):
    if is_owner(message):
        channel = str(message.text[9:])
        try:
            if channel == "":
                await message.reply(f"Укажите название канала!")
                return
            elif not is_valid(channel):
                await message.reply(f"Данного канала не существет!")
            elif channel in Config["users"][str(message.chat.id)]:
                await message.reply(f"Данный канал уже в ваших подписках!")
            else:
                try:
                    Config["users"][str(message.chat.id)].append(message.text[9:])
                    DataUpdate(Config)

                    await message.reply(f"Канал успешно добавлен!")
                except Exception as e:
                    await message.reply(f"sub adding error! {e}")
        except KeyError:
            Config["users"][str(message.chat.id)] = list()
            await message.reply("Список подписок не найден! Создан новый!")


@dp.message(Command('rm_sub'))
async def rm_sub(message: types.Message):
    if is_owner(message):
        channel = str(message.text[8:])
        try:
            if channel == "":
                await message.reply(f"Укажите название канала!")
                return
            elif not channel in Config["users"][str(message.chat.id)]:
                await message.reply(f"Данного канала нет в вашем списке подписок!")
            else:
                try:
                    Config["users"][str(message.chat.id)].remove(f"{message.text[8:]}")
                    DataUpdate(Config)

                    await message.reply(f"Канал успешно удалён!")
                except Exception as error:
                    await message.reply(f"sub [{message.text[8:]}] removing error! {error}")
        except KeyError:
            Config["users"][str(message.chat.id)] = list()
            await message.reply("Список подписок не найден! Создан новый!")


@dp.message(Command('list_sub'))
async def list_sub(message: types.Message):
    if is_owner(message):
        try:
            lst = Config["users"][str(message.chat.id)]

            if lst == []:
                await message.reply("Список подписок пуст!")
            else:
                await message.reply("\n".join(lst))
        except KeyError:
            Config["users"][str(message.chat.id)] = list()
            await message.reply("Список подписок не найден! Создан новый!")


async def tg_bot():
    print("TG Bot Started!")
    await dp.start_polling(bot)


async def twitch_watch():
    online = list()
    print("Twitch Sendler Sarted!")
    while True:
        Config = json.load(open(DataFile))
        for user_id, subs in Config["users"].items():
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

        await asyncio.sleep(1 * 60)


async def main():
    await asyncio.gather(twitch_watch(), tg_bot())
    exit()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Пока!")
        exit()
