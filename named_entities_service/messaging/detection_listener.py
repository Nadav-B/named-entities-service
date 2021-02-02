import logging

from rabbitmq_proto_lib.reconnecting_consumer import RabbitMQConsumer

from database.repos.named_entitites_result_repository import NamedEntitiesResultRepository
from models.detection_status import DetectionStatus
from models.named_entity import NamedEntity
from proto.dreipc.asset.namedentities import NamedEntitiesProto
from proto.dreipc.q8r.proto.asset import DocumentPageProto
from nlp.named_entities_service import NamedEntitiesService

logging.root.setLevel(logging.DEBUG)


class NamedEntitiesRabbitListener(RabbitMQConsumer):
    QUEUE = 'asset.document.entities.detect'
    EXCHANGE = 'assets'

    def __init__(self, amqp_url: str, service: NamedEntitiesService, repository: NamedEntitiesResultRepository):
        super().__init__(amqp_url, queue=self.QUEUE, exchange=self.EXCHANGE, exchange_durable=True, prefetch_count=10)

        self.repository = repository
        self.service = service
        self.add_typed_on_message_callback(DocumentPageProto, self.detect_objects)

    def detect_objects(self, body: DocumentPageProto, properties):
        named_entities = []

        for entity in NamedEntitiesRabbitListener.service.analyse_text(body.html):
            entity.page_id = body.id
            named_entity: NamedEntity = NamedEntitiesRabbitListener.repository.store(entity)
            named_entities.append(named_entity.proto())

        proto_result = NamedEntitiesProto(named_entities=named_entities,
                                          status=DetectionStatus.VERIFIED,
                                          provided_by='named-entities-service')

        self.send_message("asset.document.entities.detected", self.EXCHANGE, proto_result)
