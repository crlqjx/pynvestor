from red_rat import logger

from pymongo import MongoClient
from pymongo.errors import BulkWriteError


class MongoConnector:
    def __init__(self):
        host = 'localhost'
        port = 27017
        self._mongo_client = MongoClient(host, port)

    @property
    def mongo_client(self):
        return self._mongo_client

    def find_document(self, database_name: str, collection_name: str, **fields):
        collection = getattr(getattr(self._mongo_client, database_name), collection_name)
        return collection.find_one(fields)

    def find_documents(self, database_name: str, collection_name: str, **fields) -> list:
        collection = getattr(getattr(self._mongo_client, database_name), collection_name)
        documents = collection.find(fields)
        return [document for document in documents]

    def insert_documents(self, database_name: str, collection_name: str, documents: list):
        collection = getattr(getattr(self._mongo_client, database_name), collection_name)
        try:
            result = collection.insert_many(documents=documents, ordered=False)
            logger.log.info(f"inserted {len(result.inserted_ids)} in {database_name}.{collection_name}")
        except BulkWriteError as bulk_write_error:
            """when the attribute "ordered" is set to False, according to pymongo documentation:
            ordered (optional): If True (the default) documents will be inserted on the server serially,
            in the order provided. If an error occurs all remaining inserts are aborted. If False, documents
            will be inserted on the server in arbitrary order, possibly in parallel, and all document inserts
            will be attempted.
            However, the bulk error will still appear
            https://stackoverflow.com/questions/44610106/pymongo-insert-many-unique-index"""

            logger.log.warning(f"bulk insert in {database_name}.{collection_name} with already existing key: inserted "
                               f"{bulk_write_error.details['nInserted']} documents, encountered "
                               f"{len(bulk_write_error.details['writeErrors'])} write errors")
