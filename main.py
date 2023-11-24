import requests
import json

#### TWITCH ####
TOKEN = config["api"]['token']
client_secret = config["api"]['client_secret']
client_id = config["api"]["client_id"]

def get_token() -> str:
  """Функция делает запрос в твич-апи и выозвращает """

    response = requests.post(
        'https://id.twitch.tv/oauth2/token',
        data={
            'client_id': client_id,
            'client_secret': client_secret,
            'grant_type': 'client_credentials'
            }
    )

    if response.status_code == 200:
        response_json = response.json()
        TOKEN = response_json['access_token']
    
    return TOKEN
