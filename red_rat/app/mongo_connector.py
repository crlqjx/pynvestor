from red_rat import logger

from pymongo import MongoClient
from pymongo.errors import BulkWriteError

from typing import Generator


class MongoConnector:
    def __init__(self):
        host = 'localhost'
        port = 27017
        self._mongo_client = MongoClient(host, port)
        self._sanity_check()

    @property
    def mongo_client(self):
        return self._mongo_client

    def _sanity_check(self):
        # TODO: assert if all collections are in the database
        # TODO: check all the index keys
        return

    def find_document(self, database_name: str, collection_name: str, **fields):
        collection = getattr(getattr(self._mongo_client, database_name), collection_name)
        return collection.find_one(fields)

    def find_documents(self, database_name: str, collection_name: str, projection=None,
                       sort=None, **fields) -> Generator:
        """
        find documents in mongo from query
        :param database_name: str
        :param collection_name: str
        :param projection: dict - fields required in the result - {"field1": 0, "field2": 1}
        :param sort: list of tuples - sort parameters - [("field1", -1), ("field2", 1)]
        :param fields: dict - filters for the query - {"field1" : "required_value"}
        :return: generator object of the results
        """
        collection = getattr(getattr(self._mongo_client, database_name), collection_name)
        if sort is None:
            documents = collection.find(fields, projection)
        else:
            documents = collection.find(fields, projection).sort(sort)
        return (document for document in documents)

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
