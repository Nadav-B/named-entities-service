# https://www.freelancer.com/community/articles/crud-operations-in-mongodb-using-python
# https://github.com/markqiu/fastapi-mongodb-realworld-example-app
from typing import  Optional

from bson import ObjectId
from bson.errors import InvalidId
from pydantic import Field, validator

from models.mongo_model import MongoModel


class ObjectIdStr(str):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        try:
            return ObjectId(str(v))
        except InvalidId:
            raise ValueError("Not a valid ObjectId")


class KnowledgeBase(MongoModel):
    id: Optional[ObjectId] = Field(alias="_id")
    type: str
    knowledge_base_id: Optional[str]
    link: Optional[str]
    source: Optional[str]

    class Config:
        arbitrary_types_allowed = True
        allow_population_by_field_name = True
        json_encoders = {ObjectId: lambda x: str(x)}

    @validator("id")
    def validate_id(cls, id):
        if id:
            return str(id)
