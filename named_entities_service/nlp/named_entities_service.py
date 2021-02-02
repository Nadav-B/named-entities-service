"""
 Text Analyser is responsible for NLP Model and the pipelines of our service.
"""

import logging

import spacy

# Pipelines
from nlp.nlp_manager import NLPManager
from nlp.pipelines.abbreviation_recognizer import DreiPcAbbreviationDetector
from nlp.pipelines.entity_linker.entity_linker import CustomEntityLinker
from nlp.pipelines.entity_recognizer import EntityRecognizer
from nlp.pipelines.knowledge_base.konwledge_base import CustomKnowledgeBase
from nlp.pipelines.entity_linker.wikidata_entity_linker import WikidataEntityLinker
from nlp.pipelines.knowledge_base.wikidata_knowledge_base import WikidataKnowledgeBase

from nlp.pipelines.text_preprocessing.html_parser import HtmlToTextParser

# Helpers
from nlp.pipelines.sentiment_analyser.sentiment_analyser import SentimentAnalyser
from nlp.pipelines.text_preprocessing.text_preprocessing import TextPreprocessing
from resources.resources_manager import ResourcesManager


class NamedEntitiesService:
    __MODEL_NAME = "de_core_news_lg"

    # TODO Gpu with Knowledge Base fix
    def __init__(self, resources_config: dict = None):
        logging.info(
            'Named Entities Service is starting with spaCy v' + spacy.__version__)
        spacy.prefer_gpu()
        self.nlp = NLPManager.load_language_model(self.__MODEL_NAME)
        resources_manager = ResourcesManager(resources_config)
        """
        # Custom EL
        self.custom_kb = CustomKnowledgeBase(self.nlp, resources_manager)
        self.custom_nel = CustomEntityLinker(self.nlp, resources_manager)
        self.ner = EntityRecognizer(self.nlp)
        """
        # Wiki EL
        self.wiki_kb = WikidataKnowledgeBase(self.nlp, resources_manager)
        self.wiki_nel = WikidataEntityLinker(self.nlp, resources_manager)

        self.abbreviation = DreiPcAbbreviationDetector(self.nlp)
        self.sentiment = SentimentAnalyser(self.nlp)

    def analyse_text(self, html_text):
        html_text = TextPreprocessing.default_html_cleaning(html_text)
        # ner_text to use as well for entity linker pipe
        ner_text, sentiment_text = self.text_preprocessing(html_text)
        # named_entities = self.ner.ner_new(ner_text)
        # sentiment_score = self.sentiment.text(sentiment_text)
        # abbreviation_entities = self.abbreviation.html(html_text, ner_text)
        wiki_linked_named_entities = self.wiki_nel.new_nel(ner_text)

        return wiki_linked_named_entities

    @staticmethod
    def text_preprocessing(html_content: str):
        parser = HtmlToTextParser()  # a list of text with the deleted position
        parser.feed(html_content)
        content = parser.data  # including the orginal position of the text.

        named_entity_content = []
        sentiment_content = []
        for text, start, end, tag in content:  # tag relates to HTML Tags
            text = TextPreprocessing.default_text_cleaning(text)
            text = TextPreprocessing.replace_with_whitespace(
                text, r'[^a-zA-züöäÖÄÜßèé0-9\s\-\&\/\(\)\.:@€%*\{\}\[\]]')
            sentiment = TextPreprocessing.replace_with_whitespace(
                text, r'[^a-zA-züöäÖÄÜß]').lower().strip()
            sentiment = TextPreprocessing.remove_multi_whitespace(
                sentiment)  # Normal cleaning without the text positions

            text, position_map = TextPreprocessing.whitespace_to_position_map_handling(
                text)
            sentiment_content.append(sentiment)
            named_entity_content.append(
                (text, start, end, tag, position_map))  # named_entity_content usage for entity linker

        sentiment_text = '\n'.join(sentiment_content)
        return named_entity_content, sentiment_text
