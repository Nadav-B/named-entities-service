from datetime import datetime

from bson import ObjectId

from models.knowledge_base import KnowledgeBase
from models.mongo_model import MongoModel
from infrastructure.mongo_db import MongoDB


class KnowledgeBaseRepository:

    def __init__(self, database: MongoDB, collection_name: str = None):
        if not collection_name:
            raise ValueError("No Collection name given!")
        self.collection_name = collection_name
        self.database = database

    def store(self, kb: KnowledgeBase) -> KnowledgeBase:

        if kb.id is None:
            kb.created_at = datetime.now()
            kb.id = ObjectId()
            kb.id = self.__insert(kb)
        else:
            kb.updated_at = datetime.now()
            self.__update(kb)

        return kb

    def __insert(self, document: MongoModel) -> ObjectId:
        return self.database.get()[self.collection_name].insert_one(document.mongo())

    def __update(self, document: MongoModel) -> ObjectId:
        return self.database.get()[self.collection_name].update_one({'_id': ObjectId(document.id)},
                                                                    {'$set': document.mongo()}, True)

    def exists(self, id: str, project_id: str) -> MongoModel:
        return self.database.get()[self.collection_name].count_documents(
            {'project_id': project_id, '_id': ObjectId(id)}) > 0

    def get(self, id: str) -> KnowledgeBase:
        detected_result_kb = self.database.get()[self.collection_name].find_one({'_id': ObjectId(id)})
        if not detected_result_kb:
            raise ValueError(f"Detection Result with id {id} not exist!")
        return KnowledgeBase(**detected_result_kb)

    def get_all_kbs(self) -> KnowledgeBase:
        detected_result_kb = self.database.get()[self.collection_name].find({})
        if not detected_result_kb:
            raise ValueError(f"Detection Result with id {id} not exist!")
        return KnowledgeBase(**detected_result_kb)

    def delete(self, id: str):
        self.database[self.collection_name].delete_one({'_id': ObjectId(id)})
