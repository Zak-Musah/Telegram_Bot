from dotenv import load_dotenv
import telebot
from telebot import types
import time
from gp import get_services, get_token, get_workers
import datetime
import json
import requests
import numpy as np
import matplotlib.pyplot as plt
import os
from os.path import join, dirname
from dotenv import load_dotenv

fig = plt.figure()


#######################################################################################################
dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

BOT_TOKEN = os.environ.get("BOT_TOKEN")
APPID = os.environ.get("APPID")
GRAPHQL_TOKEN = os.environ.get("GRAPHQL_TOKEN")

bot_token = BOT_TOKEN  # Telegram API token

appid = APPID  # Weather API token

graphql_token = GRAPHQL_TOKEN


headers = {"Authorization": "Bearer {}".format(graphql_token),
           "Content-type": "application/json"}

bot = telebot.TeleBot(bot_token)

#######################################################################################################


@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_name = message.chat.first_name
    markup = types.ReplyKeyboardMarkup(row_width=3)
    itembtn1 = types.KeyboardButton('/help')
    markup.add(itembtn1)
    bot.reply_to(message, 'Welcome {}.\n \n Click /help for availabe commands: '.format(user_name),
                 reply_markup=markup)


#######################################################################################################
@bot.message_handler(commands=['current_weather'])
def ask_location(message):
    msg = bot.reply_to(
        message, 'To see Current Weather, please attach your current location \nusing telegram Maps')
    bot.register_next_step_handler(msg, processCurrentLoc)


def processCurrentLoc(message):

    lat = str(message.location.latitude)
    lon = str(message.location.longitude)

    def weather_data(query):

        res = requests.get('http://api.openweathermap.org/data/2.5/weather?' +
                           query+'&units=metric')
        return res.json()

    def out_temp(result):
        temp = "{}'s temperature : {}°C ".format(
            result['name'], result['main']['temp'])
        wind = "Wind speed:{} m/s".format(result['wind']['speed'])
        weather = "Weather:{}".format(result['weather'][0]['main'])
        desc = "Description:{}".format(result['weather'][0]['description'])

        message = "\n".join([temp, wind, weather, desc])
        return message

    query = 'lat='+lat+'&lon='+lon+'&appid='+appid
    data = weather_data(query)

    temp_data = out_temp(data)

    bot.send_message(chat_id=message.chat.id,
                     text='{0}'.format(temp_data))


#######################################################################################################


@bot.message_handler(commands=['help'])
def avail_cmds(message):

    markup = types.ReplyKeyboardMarkup(row_width=3)

    itembtn1 = types.KeyboardButton('/services')
    itembtn2 = types.KeyboardButton('/workers')
    itembtn3 = types.KeyboardButton('/current_weather')
    itembtn4 = types.KeyboardButton('/drop_ues_service')
    markup.add(itembtn1, itembtn2, itembtn3, itembtn4)
    bot.reply_to(message, "Available commands:",
                 reply_markup=markup)

#######################################################################################################


@bot.message_handler(commands=['services'])
def answer_msg(message):
    texts = '\n'.join(get_services())
    bot.reply_to(message, 'Current List of Services:\n  \n{}'.format(texts))

#######################################################################################################


@bot.message_handler(commands=['workers'])
def worker_avail(message):
    active_workers = get_workers()
    bot.reply_to(message, active_workers)

#######################################################################################################


@bot.message_handler(commands=['drop_ues_service'])
def ues_location(message):
    msg = bot.reply_to(
        message, 'To use drop_ues service please attach your current location using telegram Maps')
    bot.register_next_step_handler(msg, processUesLoc)


def processUesLoc(message):

    lat = str(message.location.latitude)
    lon = str(message.location.longitude)

    request_content = {
        "lat": lat,
        "lon": lon,
        "radius": 1000,
        "n": 5
    }

    def run_query(query):
        request = requests.post(
            'https://calchub.otc.roundeasy.ru/query', json={'query': query}, headers=headers)
        if request.status_code == 200:

            return request.json()
        else:
            raise Exception("Query failed to run by returning code of {}. {}".format(
                request.status_code, query))

    def drop_ues_request(content: str):
        content = content.replace("\"", "\\\"")
        query = """mutation {
    createRequest(
        input: {
        serviceID: "service_drop_ues"
        acceptContentType: "application/json"
        contentType: "application/json"
        content: "%s"
        forceUpdate: true
        }
    ) {
        id
        status
        content
    }
    }""" % (content)

        ues_request = run_query(query)
        return ues_request

    # drop_ues_request(json.dumps(request_content))

    def drop_ues_response():
        query = """{
    requests(filter: {serviceID: "service_drop_ues" }) {
        id
        content
        status
        response{
        id
        content
        status
        }

    }
    }"""

        ues_response = run_query(query)
        return ues_response

    ues_request = drop_ues_request(json.dumps(request_content))
    ues_response = drop_ues_response()

    def content():
        for i, data in enumerate(ues_response["data"]["requests"]):
            req_id = ues_request["data"]["createRequest"]["id"]
            res_id = ues_response["data"]["requests"][i]["id"]
            status = ues_response["data"]["requests"][i]["status"]
            if req_id == res_id and status == "finished":
                results = ues_response["data"]["requests"][i]["response"]["content"]
                # return ues_response["data"]["requests"][i]["response"]["content"]
                #     results = ues_response["data"]["requests"][i]["response"]["content"]
                # return results

                print(results)
                resulting_lat = []
                resulting_lon = []
                print(resulting_lat)
                for data in results["data"]:
                    resulting_lat.append(data["lat"])
                    resulting_lon.append(data["lon"])

                    # plt.scatter(resulting_lat, resulting_lon)
                    # plt.show()

                bot.send_message(chat_id=message.chat.id,
                                 text='{0} {1}'.format(resulting_lat, resulting_lon))
        # bot.send_photo(chat_id=message.chat.id, photo=open(
        #     "C:/PERSONAL/Big Data Projects/Bot/drop_ues.png", "rb"))
#######################################################################################################


bot.polling()

while True:
    time.sleep(.5)
