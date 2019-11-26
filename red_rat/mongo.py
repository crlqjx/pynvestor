from pymongo import MongoClient


class MongoConnector:
    def __init__(self):
        host = 'localhost'
        port = 27017
        self._mongo_client = MongoClient(host, port)

    def find_document(self, database_name: str, collection_name: str, **fields):
        collection = getattr(getattr(self._mongo_client, database_name), collection_name)
        return collection.find_one(fields)

    def insert_documents(self, database_name: str, collection_name: str, documents: list):
        collection = getattr(getattr(self._mongo_client, database_name), collection_name)
        collection.insert_many(documents=documents, ordered=False)

    def update_document(self, database_name,  collection_name: str, document_id: str, data_to_update: dict, **query):
        collection = getattr(getattr(self._mongo_client, database_name), collection_name)
        collection.update_one(query, {"$set": data_to_update})
