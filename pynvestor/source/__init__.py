from pynvestor.source.data_providers import EuronextClient, ReutersClient, YahooClient
from pynvestor.source.mongo_connector import MongoConnector

euronext = EuronextClient()
reuters = ReutersClient()
yahoo = YahooClient()
mongo = MongoConnector()
