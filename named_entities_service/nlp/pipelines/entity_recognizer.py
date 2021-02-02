"""
 To train an entity linking model it's necessary
 to define a knowledge base (KB)
 and construct it first.

 For more details, see the documentation:
 Entity Recognizer: https://spacy.io/api/entityrecognizer#model
"""

import logging

from models.named_entity import NamedEntity

# Regex Extractor
from nlp.pipelines.text_preprocessing.text_preprocessing import TextPreprocessing
from regex_extractors.date import GermanDates
from regex_extractors.money import GermanEuros
from regex_extractors.percent import GermanPercentages
from regex_extractors.regex_matcher import RegexpBasedMatcher

# Rule Spacy Extractor
from extractors.email_extractor import EmailExtractor
from extractors.url_extractor import UrlExtractor

from spacy.pipeline import EntityRuler
from gazetter.matcher_dict import MatcherDirectory

from nlp.pipelines.german_tokenizer import german_tokenizer



class EntityRecognizer(object):
    pipes = []

    def __init__(self, nlp):
        logging.info("Initializing Entity Recognizer")

        self.__nlp = nlp

        self.pipes.append('tagger')
        self.pipes.append('parser')

        self.__nlp.tokenizer = german_tokenizer(self.__nlp)

        self.__date_matcher = RegexpBasedMatcher(self.__nlp, "DATE", GermanDates())
        self.__nlp.add_pipe(self.__date_matcher, name='regexp_dates_extractor', before='ner')
        self.pipes.append('regexp_dates_extractor')

        self.__money_matcher = RegexpBasedMatcher(self.__nlp, "MONEY", GermanEuros())
        self.__nlp.add_pipe(self.__money_matcher, name='regexp_euro_extractor', before='ner')
        self.pipes.append('regexp_euro_extractor')

        self.__percent_matcher = RegexpBasedMatcher(self.__nlp, "PERCENT", GermanPercentages())
        self.__nlp.add_pipe(self.__percent_matcher, name='regexp_percent_extractor', before='ner')
        self.pipes.append('regexp_percent_extractor')

        self.__email_extractor = EmailExtractor()
        self.__nlp.add_pipe(self.__email_extractor, name='token_email_extractor', before='ner')
        self.pipes.append('token_email_extractor')

        self.__url_extractor = UrlExtractor()
        self.__nlp.add_pipe(self.__url_extractor, name='token_url_extractor', before='ner')
        self.pipes.append('token_url_extractor')

        self.__ruler = EntityRuler(self.__nlp)
        directory = MatcherDirectory()
        self.__ruler.add_patterns(directory.all)
        self.__nlp.add_pipe(self.__ruler, name='entity_matcher', before="ner")
        self.pipes.append('entity_matcher')

        self.pipes.append('ner')

    def ner_new(self, contents):
        counter = 0
        entities = []
        texts = [text[0] for text in contents]

        pipelines = [pipe[0] for pipe in self.__nlp.pipeline]

        for doc in self.__nlp.pipe(texts, disable=[pipe for pipe in pipelines if pipe not in self.pipes]):
            original_start_pos = contents[counter][1]
            position_map = contents[counter][4]

            for entity in doc.ents:
                # if entity.start_char > 0:
                #     match = re.match(r"ß",doc.text[:entity.start_char])
                #     if match:
                #         minus_handling = len(match)
                # minus_handling = doc.text[:entity.start_char].count('ß') # ß has a length of 2 in spacy which is not correct
                start_pos = TextPreprocessing.orig_text_to_cleaned_text_position(position_map, entity.start_char,
                                                                                 original_start_pos)
                end_pos = TextPreprocessing.orig_text_to_cleaned_text_position(position_map, entity.end_char,
                                                                               original_start_pos)
                entities.append(
                    NamedEntity(
                        literal=entity.text,
                        type=entity.label_,
                        start_pos=start_pos,
                        end_pos=end_pos,
                    ))

            counter += 1

        return entities
