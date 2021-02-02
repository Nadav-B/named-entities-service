"""
 App includes all the code regarding our Rest Controller with the help of flask
"""
import logging
import threading

from ariadne.asgi import GraphQL
from py_config.application_config import YamlConfig

from database.repos.named_entitites_result_repository import NamedEntitiesResultRepository
from infrastructure.fastapi import FastAPIServer
from infrastructure.graphql import GraphQLConfiguration
from infrastructure.mongo_db import MongoDB
from infrastructure.rabbitmq import RabbitMQ
from messaging.detection_listener import NamedEntitiesRabbitListener
from nlp.named_entities_service import NamedEntitiesService
from resolver.knowledge_base_resolver import KnowledgeBaseResolver
from resolver.named_entities_resolver import NamedEntitiesResolver

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')


class NamedEntitiesService:

    print(
        '''
         _____            
        |___ / _ __   ___ 
          |_ \| '_ \ / __|
         ___) | |_) | (__   
        |____/| .__/ \___|    
              |_| 3pc GmbH Neue Kommunikation  
        '''
    )

    app_config = YamlConfig.load()
    text_analyser = NamedEntitiesService(app_config['resources'])
    webserver = FastAPIServer(app_config['server'])

    # MongoDB
    mongodb = MongoDB(app_config['mongodb'])
    ne_repository = NamedEntitiesResultRepository(mongodb, 'named_entities_results')
    kb_repository = NamedEntitiesResultRepository(mongodb, 'knowledge_bases')

    webserver.startup_event(mongodb.connect)

    # GraphQL
    entities_resolver = NamedEntitiesResolver(text_analyser, ne_repository)
    kb_resolver = KnowledgeBaseResolver(text_analyser, kb_repository)

    schema = GraphQLConfiguration(entities_resolver).schema()
    webserver.register_endpoint("/graphql",
                                GraphQL(schema, error_formatter=GraphQLConfiguration.dreipc_error_formatter))

    # RabbitMQ
    rabbitmq = RabbitMQ(app_config['rabbitmq'])
    rabbit_listener = NamedEntitiesRabbitListener(rabbitmq.amqp_url, text_analyser, ne_repository)
    thread = threading.Thread(target=rabbit_listener.run, daemon=True)
    thread.start()

    webserver.shutdown_event(rabbit_listener.stop)
    webserver.shutdown_event(thread.join)
    webserver.shutdown_event(mongodb.disconnect)
    webserver.start()
