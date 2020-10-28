from pynvestor.app.data_providers import EuronextClient, ReutersClient, YahooClient
from pynvestor.app.mongo_connector import MongoConnector

euronext = EuronextClient()
reuters = ReutersClient()
yahoo = YahooClient()
mongo = MongoConnector()
