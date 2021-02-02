from typing import List

from ariadne import QueryType, MutationType
from ariadne_extensions import federation

from database.repos.knowledge_base_repository import KnowledgeBaseRepository
from resolver.resolver import GraphQLResolver
from nlp.named_entities_service import NamedEntitiesService


class KnowledgeBaseResolver(GraphQLResolver):
    add_kbs_mutation = MutationType()
    get_kb_query = QueryType()
    document_type = federation.FederatedObjectType("KnowledgeBase")

    service = None
    repository = None

    def __init__(self, _service: NamedEntitiesService, _repository: KnowledgeBaseRepository):
        super(KnowledgeBaseResolver, self).__init__()
        KnowledgeBaseResolver.service = _service
        KnowledgeBaseResolver.repository = _repository

    @add_kbs_mutation.field('addKnowledgeBases')
    def add_kbs(self, info, **kwargs):
        kbs = kwargs.get("kbs")

        return kbs

    @get_kb_query.field('getKnowledgeBases')
    def get_kbs(self, info, **kwargs):
        return KnowledgeBaseResolver.repository.get_all_kbs()

    def get_schemas(self) -> List:
        return [self.document_type,
                self.get_kb_query,
                self.add_kbs_mutation,
                ]
