from typing import List

from ariadne import QueryType, MutationType
from ariadne_extensions import federation

from database.repos.named_entitites_result_repository import NamedEntitiesResultRepository
from resolver.resolver import GraphQLResolver
from nlp.named_entities_service import NamedEntitiesService


class NamedEntitiesResolver(GraphQLResolver):
    document_type = federation.FederatedObjectType("NamedEntity")
    detect_entities_query = QueryType()
    get_page_entities_query = QueryType()
    verify_named_entities_query = MutationType()

    service = None
    repository = None

    def __init__(self, _service: NamedEntitiesService):
        super(NamedEntitiesResolver, self).__init__()
        NamedEntitiesResolver.service = _service

    @detect_entities_query.field('detectEntities')
    def detect_entities(self, info, **kwargs):
        text = kwargs.get("text")
        # html_text = unicode(text, "utf8")
        named_entities = NamedEntitiesResolver.service.analyse_text(text)
        return named_entities

    @get_page_entities_query.field('getPageEntities')
    def get_page_entities(self, info, **kwargs):
        page_id = kwargs.get("page_id")
        return NamedEntitiesResolver.repository.get_page_entities(page_id)

    @verify_named_entities_query.field('verifyNamedEntities')
    def verify_named_entities(self, info, **kwargs):
        named_entities = kwargs.get("entities")
        for entity in named_entities:
            NamedEntitiesResolver.repository.store(entity)
        return named_entities

    def get_schemas(self) -> List:
        return [self.document_type,
                self.detect_entities_query,
                self.get_page_entities_query,
                self.verify_named_entities_query,
                ]
