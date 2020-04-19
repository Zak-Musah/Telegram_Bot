
import base64
import urllib
import io
import matplotlib.pyplot as plt
import telebot
from telebot import types
import time
from gp import get_services, get_token, worker_status
import datetime
import json
import requests
import numpy as np
import os
from os.path import join, dirname
from dotenv import load_dotenv
import matplotlib
from staticmap import StaticMap, CircleMarker, IconMarker
import asyncio


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

NUM_MIN_N_UES = 1
NUM_MAX_N_UES = 50
NUM_MIN_RADIUS = 800
NUM_MAX_RADIUS = 2000
REQUEST_TIMEOUT = 10  # graphql request timeout
n = []
radius = []
#######################################################################################################

user_ids = []


def check_user(message):
    chat_id = message.chat.id
    global user_ids
    if chat_id not in user_ids:
        user_ids.append(chat_id)
        return True
    else:
        return False


@bot.message_handler(commands=['start'])
def send_welcome(message):
    first_name = message.chat.first_name
    if check_user(message):
        markup = types.ReplyKeyboardMarkup(row_width=1)
        itembtn1 = types.KeyboardButton('/request_access')
        markup.add(itembtn1)
        bot.reply_to(
            message, 'Unauthorized user', reply_markup=markup)
        bot.register_next_step_handler(
            message, grant_access)
    else:
        markup = types.ReplyKeyboardMarkup(row_width=3)
        itembtn1 = types.KeyboardButton('/services')
        itembtn2 = types.KeyboardButton('/workers')
        itembtn3 = types.KeyboardButton('/current_weather')
        itembtn4 = types.KeyboardButton('/drop_ues_service')
        markup.add(itembtn1, itembtn2, itembtn3, itembtn4)
        bot.reply_to(message, 'Welcome {}.\n \nUse commands below to interact with me: '.format(first_name),
                     reply_markup=markup)


@bot.message_handler(commands=['request_access'])
def grant_access(message):
    if check_user(message):
        markup = types.ReplyKeyboardMarkup(row_width=1)
        itembtn1 = types.KeyboardButton('/request_access')
        markup.add(itembtn1)
        bot.reply_to(
            message, 'Unauthorized user - request access to use me :(', reply_markup=markup)
        bot.register_next_step_handler(
            message, grant_access)
    else:
        first_name = message.chat.first_name
        markup_auth = types.ReplyKeyboardMarkup(row_width=2)
        itembtn1 = types.KeyboardButton('/accept')
        itembtn2 = types.KeyboardButton('/deny')
        markup_auth.add(itembtn1, itembtn2)
        bot.send_message(980284317, '{} is requesting access to use the bot: '.format(first_name),
                         reply_markup=markup_auth)
#######################################################################################################
@bot.message_handler(commands=['accept'])
def accept(message):
    if check_user(message):
        markup = types.ReplyKeyboardMarkup(row_width=1)
        itembtn1 = types.KeyboardButton('/request_access')
        markup.add(itembtn1)
        bot.reply_to(
            message, 'Unauthorized user - request access to use me :(', reply_markup=markup)
        bot.register_next_step_handler(
            message, grant_access)
    else:
        if message.text == '/accept':
            bot.send_message(
                user_ids[-1], 'Access Granted: click on /start to get going')
#######################################################################################################
@bot.message_handler(commands=['deny'])
def deny(message):
    if check_user(message):
        markup = types.ReplyKeyboardMarkup(row_width=1)
        itembtn1 = types.KeyboardButton('/request_access')
        markup.add(itembtn1)
        bot.reply_to(
            message, 'Unauthorized user - request access to use me :(', reply_markup=markup)
        bot.register_next_step_handler(
            message, grant_access)
    else:
        if message.text == '/deny':
            bot.send_message(
                user_ids[-1], 'Access Denied')
        user_ids.pop()
#######################################################################################################
@bot.message_handler(commands=['current_weather'])
def ask_location(message):
    if check_user(message):
        markup = types.ReplyKeyboardMarkup(row_width=1)
        itembtn1 = types.KeyboardButton('/request_access')
        markup.add(itembtn1)
        bot.reply_to(
            message, 'Unauthorized user - request access to use me :(', reply_markup=markup)
        bot.register_next_step_handler(
            message, grant_access)
    else:
        msg = bot.reply_to(
            message, 'To see current Weather stats, please attach your current location \nusing telegram Maps')
        bot.register_next_step_handler(msg, processCurrentLoc)


def processCurrentLoc(message):
    if check_user(message):
        markup = types.ReplyKeyboardMarkup(row_width=1)
        itembtn1 = types.KeyboardButton('/request_access')
        markup.add(itembtn1)
        bot.reply_to(
            message, 'Unauthorized user - request access to use me :(', reply_markup=markup)
        bot.register_next_step_handler(
            message, grant_access)
    else:
        expect = 'location'
        if message.content_type != expect:
            reply_msg = bot.reply_to(
                message, 'Invalid input, please attach your current location using telegram maps')
            bot.register_next_step_handler(reply_msg, processCurrentLoc)
            return
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

######################################################################################################
@bot.message_handler(commands=['services'])
def answer_msg(message):
    if check_user(message):
        markup = types.ReplyKeyboardMarkup(row_width=1)
        itembtn1 = types.KeyboardButton('/request_access')
        markup.add(itembtn1)
        bot.reply_to(
            message, 'Unauthorized user - request access to use me :(', reply_markup=markup)
        bot.register_next_step_handler(
            message, grant_access)
    else:
        texts = '\n'.join(get_services())
        bot.reply_to(
            message, 'Current List of Services:\n  \n{}'.format(texts))

#######################################################################################################
@bot.message_handler(commands=['workers'])
def worker_avail(message):
    if check_user(message):
        markup = types.ReplyKeyboardMarkup(row_width=1)
        itembtn1 = types.KeyboardButton('/request_access')
        markup.add(itembtn1)
        bot.reply_to(
            message, 'Unauthorized user - request access to use me :(', reply_markup=markup)
        bot.register_next_step_handler(
            message, grant_access)
    else:
        active_workers = worker_status()
        bot.reply_to(message, active_workers)

#######################################################################################################
@bot.message_handler(commands=['drop_ues_service'])
def ask_num_ues(message):
    if check_user(message):
        markup = types.ReplyKeyboardMarkup(row_width=1)
        itembtn1 = types.KeyboardButton('/request_access')
        markup.add(itembtn1)
        bot.reply_to(
            message, 'Unauthorized user - request access to use me :(', reply_markup=markup)
        bot.register_next_step_handler(
            message, grant_access)
    else:
        bot.reply_to(
            message, 'How many users you want to drop? Type number between {0} to {1}'.format(NUM_MIN_N_UES, NUM_MAX_N_UES))
        bot.register_next_step_handler(message, checkUes_askRadius)


def checkUes_askRadius(message):
    if int(message.text) > NUM_MAX_N_UES or int(message.text) < NUM_MIN_N_UES:
        reply_msg = bot.reply_to(message, "Number of users has to be a number between {0} and {1}. Try again".format(
            NUM_MIN_N_UES, NUM_MAX_N_UES))
        bot.register_next_step_handler(reply_msg, checkUes_askRadius)

    num_ues = int(message.text)
    n.append(num_ues)
    reply_message = bot.reply_to(
        message, 'What the simulatin radius should be? \n Type a number between {0} and {1}'.format(
            NUM_MIN_RADIUS, NUM_MAX_RADIUS))
    bot.register_next_step_handler(reply_message, checkkradius_askloc)


def checkkradius_askloc(message):
    if int(message.text) > NUM_MAX_RADIUS or int(message.text) < NUM_MIN_RADIUS:
        reply_msg = bot.reply_to(message, "Radius has to be a number between {0} and {1}".format(
            NUM_MIN_RADIUS, NUM_MAX_RADIUS))
        bot.register_next_step_handler(reply_msg, checkkradius_askloc)
        return
    num_radius = int(message.text)
    radius.append(num_radius)
    reply_message = bot.reply_to(
        message, 'Attach the location for the center of the simulation')
    bot.register_next_step_handler(reply_message, processUesLoc)


def processUesLoc(message):
    expected = 'location'
    if message.content_type != expected:
        reply_msg = bot.reply_to(
            message, 'Please attach a valid location using telegram maps')
        bot.register_next_step_handler(reply_msg, processUesLoc)
        return
    lat = str(message.location.latitude)
    lon = str(message.location.longitude)

    request_content = {
        "lat": float(lat),
        "lon": float(lon),
        "radius": int(radius[0]),
        "n": int(n[0])
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
    time.sleep(1)
    ues_request = drop_ues_request(json.dumps(request_content))
    print(ues_request)
    resp_id = ues_request["data"]["createRequest"]["id"]

    def drop_ues_response(resp_id):
        query = """{
    requests(filter: {id: "%s",serviceID: "service_drop_ues" }) {
        id
        content
        status
        response{
        id
        content
        status
        }
    }
    }""" % (resp_id)

        ues_response = run_query(query)
        return ues_response
    response = 'https://drop-ues-roundeasy.radiolab-leipzig.now.sh/scenario/%s' % resp_id

    bot.send_message(chat_id=message.chat.id, text=response)


bot.polling()

while True:
    time.sleep(.5)
