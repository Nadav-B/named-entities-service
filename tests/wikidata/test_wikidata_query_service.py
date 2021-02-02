import unittest
from unittest import TestCase
import json
from named_entities_service.wikipedia.wikidata_query_service import WikidataQueryService

class TestWikiEntityMapping(TestCase):
    wiki_emap = WikidataQueryService()
    ENTITIES = ['Q454564', 'Q42', 'Q64', 'Q23']

    def test_query(self):
        result = self.wiki_emap.get_wikidata_entity('Q64')
        jsonStr = json.dumps(result)
        print(jsonStr)


    def test_get_wikidata_entity(self):
        self.wiki_emap.get_wikidata_entity(self.ENTITIES[0])

    def test_get_wikidata_entities(self):
        results = self.wiki_emap.get_wikidata_entities(self.ENTITIES)
        self.assertTrue(len(results), "check internet connection and write Wikidata Ids.")

    def test_get_wikidata_entities_empty(self):
        results = self.wiki_emap.get_wikidata_entities([])
        self.assertTrue(len(results) == 0, "check if file is located and with content")

    def test_parsed_entites_from_wiki(self):
        title_to_id, id_to_descr, id_to_alias = self.wiki_emap.get_parsed_entities(self.ENTITIES)
        self.print("title_to_id", title_to_id)
        self.print("id_to_descr", id_to_descr)
        self.print("id_to_alias", id_to_alias)
        self.assertTrue(len(title_to_id) & len(id_to_alias) & len(id_to_descr),
                        "Can't retrive results from api")

    def print(self, list_name, info_list):
        print(list_name + ":")
        print(info_list)
