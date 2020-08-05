from red_rat.logger import Logger
from red_rat.app.data_providers import EuronextClient, ReutersClient
from red_rat.app.mongo_connector import MongoConnector
from red_rat.app.helpers import Helpers


logger = Logger()
euronext = EuronextClient()
reuters = ReutersClient()
mongo = MongoConnector()
helpers = Helpers()
