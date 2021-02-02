from typing import Optional

from bson import ObjectId
from bson.errors import InvalidId
from pydantic import validator, Field

from models.mongo_model import MongoModel
#  from proto.dreipc.asset.namedentities import NamedEntityProto


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


class NamedEntity(MongoModel):
    id: Optional[ObjectId] = Field(alias="_id")
    page_id: str
    literal: str
    start_pos: int
    end_pos: int
    type: str
    knowledge_base_id: Optional[str]
    link: Optional[str]

    class Config:
        arbitrary_types_allowed = True
        allow_population_by_field_name = True
        json_encoders = {ObjectId: lambda x: str(x)}

    @validator("id")
    def validate_id(cls, id):
        if id:
            return str(id)

    def __lt__(self, other):
        return self.start_pos < other.start_pos

    def proto(self):
        return NamedEntityProto(id=str(self.id),
                                page_id=self.page_id,
                                literal=self.literal,
                                type=self.type,
                                start_pos=self.start_pos,
                                end_pos=self.end_pos,
                                knowledge_base_id=self.knowledge_base_id,
                                link=self.link)
