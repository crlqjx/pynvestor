from red_rat.app.data_providers import EuronextClient, ReutersClient
from red_rat.app.mongo_connector import MongoConnector

euronext = EuronextClient()
reuters = ReutersClient()
mongo = MongoConnector()
