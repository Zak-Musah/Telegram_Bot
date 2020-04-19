
import requests
import json
import os
from os.path import join, dirname
from dotenv import load_dotenv
import datetime
dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)
GRAPHQL_TOKEN = os.environ.get("GRAPHQL_TOKEN")


graphql_token = GRAPHQL_TOKEN

headers = {"Authorization": "Bearer {}".format(graphql_token),
           "Content-type": "application/json"}


# A simple function make requests to the API


def run_query(query):
    request = requests.post(
        'https://calchub.otc.roundeasy.ru/query', json={'query': query}, headers=headers)
    if request.status_code == 200:

        return request.json()
    else:
        raise Exception("Query failed to run by returning code of {}. {}".format(
            request.status_code, query))


# The GraphQL query
def get_services():
    query = """
    {
    services {
        id
        description
    }
    }
    """

    result = run_query(query)  # Execute the query

    list_of_services = []
    for service in result["data"]["services"]:
        list_of_services.append(service['id'])
    return list_of_services


def get_token():
    query = """mutation {
  login(loginData: {username: "bot", password: "usrp"}) {
    token
  }
}
"""
    result = run_query(query)
    token = result["data"]["login"]["token"]
    return token


def get_workers():
    query = """{
  workers {
    service {
      id
    }
    user {
      id
    }
    lastActiveElapsed
    isBusy
  }
}"""
    result = run_query(query)
    return result


result = get_workers()

intervals = (
    ('weeks', 604800),  # 60 * 60 * 24 * 7
    ('days', 86400),    # 60 * 60 * 24
    ('hours', 3600),    # 60 * 60
    ('minutes', 60),
    ('seconds', 1),
)


def display_time(seconds, granularity=2):
    result = []
    for name, count in intervals:
        value = seconds // count
        if value:
            seconds -= value * count
            if value == 1:
                name = name.rstrip('s')
            result.append("{} {}".format(value, name))
    return ', '.join(result[:granularity])


def availability_str(elapsed):
    elapsed
    if elapsed < 0:
        return "offline"
    if elapsed < 10:
        return "online"
    else:
        return "offline %s" % elapsed


time = 0


def worker_status():
    workers = ''
    for worker in result["data"]["workers"]:
        try:
            availability = worker["lastActiveElapsed"]
            service_id = worker["service"]['id']
            worker_id = worker["user"]['id']
            available = display_time(availability)
            workers += '\nThe Service {0} has {1} worker(s): \n'.format(
                service_id, len(worker['user']))
            workers += 'Worker {0} is {1} - for the past {2} \n'.format(
                worker_id, availability_str(availability), available)
        except Exception as err:
            print(err)
    return workers
