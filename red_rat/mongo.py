from pymongo import MongoClient


class MongoConnector:
    def __init__(self):
        host = 'localhost'
        port = 27017
        self.mongo_client = MongoClient(host, port)
