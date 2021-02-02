import logging

from bson import ObjectId

from models.named_entity import NamedEntity


class DemoNamedEntitiesService(object):

    def __init__(self, resources_config: dict = None):
        print("demo")

    def analyse_text(text: str, page_id: str):
        logging.info("receiving test")
        named_entity = NamedEntity(id=ObjectId(),
                                   literal="Hanna Arendt",
                                   page_id=page_id,
                                   type="PERSON",
                                   start_pos=3,
                                   end_pos=4,
                                   knowledge_base_id="Q64",
                                   link="https://www.wikidata.org/wiki/Q60025")
        return [named_entity, named_entity]
