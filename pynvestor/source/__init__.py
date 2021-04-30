import json

from pynvestor.source.data_providers import EuronextClient, ReutersClient, YahooClient
from pynvestor.source.mongo_connector import MongoConnector


def set_env():
    with open(r"D:\Python Projects\red_rat\config.json") as f:
        environment = json.load(f).get('env')
        return environment


euronext = EuronextClient()
reuters = ReutersClient()
yahoo = YahooClient()
env = set_env()
mongo = MongoConnector(env)
