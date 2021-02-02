from datetime import datetime

from bson import ObjectId

from models.named_entity import NamedEntity
from models.mongo_model import MongoModel
from infrastructure.mongo_db import MongoDB


class NamedEntitiesResultRepository:

    def __init__(self, database: MongoDB, collection_name: str = None):
        if not collection_name:
            raise ValueError("No Collection name given!")
        self.collection_name = collection_name
        self.database = database

    def store(self, named_entity: NamedEntity) -> NamedEntity:

        if named_entity.id is None:
            named_entity.created_at = datetime.now()
            named_entity.id = ObjectId()
            named_entity.id = self.__insert(named_entity)
        else:
            named_entity.updated_at = datetime.now()
            self.__update(named_entity)

        return named_entity

    def __insert(self, document: MongoModel) -> ObjectId:
        return self.database.get()[self.collection_name].insert_one(document.mongo())

    def __update(self, document: MongoModel) -> ObjectId:
        return self.database.get()[self.collection_name].update_one({'_id': ObjectId(document.id)},
                                                                    {'$set': document.mongo()}, True)

    def exists(self, id: str, project_id: str) -> MongoModel:
        return self.database.get()[self.collection_name].count_documents(
            {'project_id': project_id, '_id': ObjectId(id)}) > 0

    def get(self, id: str) -> NamedEntity:
        detected_result = self.database.get()[self.collection_name].find_one({'_id': ObjectId(id)})
        if not detected_result:
            raise ValueError(f"Detection Result with id {id} not exist!")
        return NamedEntity(**detected_result)

    def get_page_entities(self, page_id: str) -> NamedEntity:
        detected_result = self.database.get()[self.collection_name].find({'page_id': page_id})
        if not detected_result:
            raise ValueError(f"Detection Result with id {id} not exist!")
        return list(detected_result)

    def delete(self, id: str):
        self.database[self.collection_name].delete_one({'_id': ObjectId(id)})
