import requests
from tqdm import tqdm


class WikidataQueryService(object):
    """
    Fetching the entity ids descriptions, alias and titles from Wikidata Api
    """

    def get_wikidata_entity(self, entity_id: str):
        API_ENDPOINT = "https://www.wikidata.org/w/api.php"
        params = {
            'action': 'wbgetentities',
            'format': 'json',
            'languages': 'de',
            'uselang': 'de',
            'ids': entity_id,
        }

        request = requests.get(API_ENDPOINT, params=params)
        json = request.json()
        if not json['entities']:
            raise NameError(entity_id)
        else:
            return json['entities']

    def get_wikidata_entities(self, entity_ids: list):
        results = dict()

        pbar = tqdm(range(len(entity_ids)))
        for ent_id in pbar:
            # pbar.set_description("Requesting %s" % entity_ids[ent_id])
            try:
                results.update(self.get_wikidata_entity(entity_ids[ent_id]))
            except NameError as e:
                print(str(e) + " not found")

        return results

    def get_parsed_entities(self, entity_ids: list):
        """
        parsing entities for Wikidata knowledge bse
        :param entity_ids: list of Wikidata ids.
        :param entity_ids: list of Wikidata ids.
        :return: return aliases, description and title
        """
        title_to_id = dict()
        id_to_descr = dict()
        id_to_alias = dict()

        results = self.get_wikidata_entities(entity_ids)

        for entity_properties in results.values():
            entity_id = entity_properties['id']

            for dict_item in entity_properties['labels'].values():
                title_to_id[dict_item['value']] = entity_id

            id_to_alias[entity_id] = self.get_aliases(entity_properties['aliases'])

            for dict_item in entity_properties['descriptions'].values():
                id_to_descr[entity_id] = dict_item['value']

        return title_to_id, id_to_descr, id_to_alias

    def get_aliases(self, aliases_dict):
        aliases = []
        for aliases_list in aliases_dict.values():
            for dict_item in aliases_list:
                aliases.append(dict_item['value'])
        return aliases

    def print_entity(self, result):
        print(result)
