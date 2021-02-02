import logging
import unittest

from bson import ObjectId
from py_config import YamlConfig

from database.repos.named_entitites_result_repository import NamedEntitiesResultRepository
from tests.demo_named_entities_service import DemoNamedEntitiesService
from infrastructure.mongo_db import MongoDB


# Make sure to set the working dir to ner_services.


class MongoDBTest(unittest.TestCase):
    repository = None
    text_analyser = None

    def setUp(self):
        app_config = YamlConfig.load()
        mongodb = MongoDB(app_config['mongodb'])
        mongodb.connect()
        self.repository = NamedEntitiesResultRepository(mongodb, 'named_entities_results')
        self.text_analyser = DemoNamedEntitiesService()

    def test_store_entry(self):
        page_id = "s4hg8"
        named_entities, sentiment_score = self.text_analyser.analyse_text("text_example", page_id)
        for entity in named_entities:
            entity_saved = self.repository.store(entity)
            logging.info("saved {}".format(entity_saved))
        self.assertTrue(self.repository.get_page_entities(page_id), "Entry was not saved")
        print(self.repository.get_page_entities(page_id))


if __name__ == '__main__':
    unittest.main()
