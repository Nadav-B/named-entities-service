"""
 To train an entity linking model it's necessary
 to define a knowledge base (KB)
 and construct it first.

 For more details, see the documentation:
 Entity Linking: https://spacy.io/usage/linguistic-features#entity-linking
"""
import logging
import random
from tqdm import tqdm

from spacy.kb import KnowledgeBase
from spacy.util import compounding, minibatch
from spacy.vocab import Vocab

from models.named_entity import NamedEntity
from nlp.pipelines.text_preprocessing.text_preprocessing import TextPreprocessing
from nlp.nlp_manager import NLPManager
from resources.resources_manager import ResourcesManager


class CustomEntityLinker(object):
    nlp_model_name = "custom_el"
    entity_linker = []
    TRAIN_DATA = []
    TRAIN_DOCS = []
    N_ITER = 50  # Number of training iterations
    pipes = ['tagger', 'parser', ' entity_linker', 'entity_matcher']

    # construction of entity linker pipe
    # entity linker is to be preceded by entity recognition
    def __init__(self, nlp, resources_manager: ResourcesManager):
        self.__nlp = nlp
        self.resources_manager = resources_manager
        self.training_path = resources_manager.get_custom_training_path("custom_training_entities.json")
        self.entity_linker_path = resources_manager.get_custom_training_path(self.nlp_model_name)
        self.kb_path = resources_manager.get_model_path("custom_kb")
        self.__nlp.vocab = Vocab().from_disk(
            resources_manager.get_model_path("vocab"))  # Loading the vocab that trained with
        self.entity_linker = self.__nlp.create_pipe("entity_linker")
        self.load_dependent_models()
        self.__nlp.add_pipe(self.entity_linker, name='entity_linker', last=True)
        self.kb_ids = self.__nlp.get_pipe("entity_linker").kb.get_entity_strings()
        self.nlp_manager = NLPManager(resources_manager)

        try:
            self.load_nlp_model()
        except ValueError:
            self.progress_bar: tqdm = self.create_progress_bar(4, "Initializing Entity Linker")
            self.read_training_dataset_from_kb()  # Inserting texts for training
            self.prepare_data_for_train()  # Converting texts to docs
            self.start_training()
            self.save_nlp_model()

    def read_training_dataset_from_kb(self):
        self.print_progress_bar("Step 1: Reading training & dev dataset from {}".format(self.training_path), True)
        text_dict = self.resources_manager.load_json_file(self.training_path)
        for text_entity in text_dict:
            start_pos, end_pos = (
                TextPreprocessing.get_start_end_char_positions(text_entity["text"], text_entity["word"]))
            dict_1 = {(start_pos, end_pos): text_entity["probability"]}
            self.TRAIN_DATA.append((text_entity["text"], {"links": dict_1}))

    def load_dependent_models(self):
        kb = KnowledgeBase(vocab=self.__nlp.vocab)
        kb.load_bulk(self.kb_path)  # Loading the Knowledge base
        logging.info("Loaded Knowledge Base from '%s'" % self.kb_path)
        self.entity_linker.set_kb(kb)  # Applying KB to entity linker

    def prepare_data_for_train(self):
        self.print_progress_bar("Step 2: Converting the trained data texts to docs")

        for text, annotation in self.TRAIN_DATA:
            with self.__nlp.disable_pipes("entity_linker"):
                doc = self.__nlp(text)
            annotation_clean = annotation
            for offset, kb_id_dict in annotation["links"].items():
                new_dict = {}
                for kb_id, value in kb_id_dict.items():
                    if kb_id in self.kb_ids:
                        new_dict[kb_id] = value
                    else:
                        print(
                            "Removed", kb_id, "from training because it is not in the KB."
                        )
                annotation_clean["links"][offset] = new_dict
            self.TRAIN_DOCS.append((doc, annotation_clean))

    # TODO Custom Batch size
    def start_training(self):
        # get names of other pipelines to disable them during training
        self.print_progress_bar("Step 3: Creating and training an Entity Linking pipe", True)
        pipe_exceptions = ["entity_linker", "entity_matcher"]
        other_pipes = [pipe for pipe in self.__nlp.pipe_names if pipe not in pipe_exceptions]
        with self.__nlp.disable_pipes(*other_pipes):  # only train entity linker
            # reset and initialize the weights randomly
            optimizer = self.__nlp.begin_training()
            for itn in range(self.N_ITER):
                random.shuffle(self.TRAIN_DOCS)
                losses = {}
                # batch up the examples using spaCy's minibatch
                batches = minibatch(self.TRAIN_DOCS, size=compounding(4.0, 32.0, 1.001))
                for batch in batches:
                    texts, annotations = zip(*batch)
                    self.__nlp.update(
                        texts,  # batch of texts
                        annotations,  # batch of annotations
                        drop=0.2,  # dropout - make it harder to memorise data
                        losses=losses,
                        sgd=optimizer,
                    )
                print(itn, "Losses", losses)

    @staticmethod
    def create_progress_bar(steps: int, desc: str):
        return tqdm(total=steps, desc=desc, bar_format='{l_bar}{bar}{n_fmt}/{total_fmt}')

    def print_progress_bar(self, description, increase_level: bool = False):
        self.progress_bar.set_description(desc=description)
        if increase_level:
            self.progress_bar.update()

    def save_nlp_model(self):
        self.print_progress_bar("Step 4: Saving Wikidata Entity Linker nlp Model", True)
        self.nlp_manager.save_nlp_model(self.__nlp, self.nlp_model_name)
        self.entity_linker.to_disk(self.entity_linker_path)

    def load_nlp_model(self):
        logging.info("Loading saved Wikidata Entity Linker nlp Model")
        self.nlp_manager.load_saved_nlp_model(self.__nlp, self.nlp_model_name)

    def new_nel(self, contents):
        entities = []
        counter = 0

        texts = [text[0] for text in contents]
        for doc in self.__nlp.pipe(texts):  # , disable=[pipe for pipe in pipelines if pipe not in self.pipelines]):
            original_start_pos = contents[counter][1]
            position_map = contents[counter][4]
            # print("Tokens", [(t.text, t.ent_type_, t.ent_kb_id_) for t in doc])
            for entity in doc.ents:
                start_pos = TextPreprocessing.orig_text_to_cleaned_text_position(position_map, entity.start_char,
                                                                                 original_start_pos)
                end_pos = TextPreprocessing.orig_text_to_cleaned_text_position(position_map, entity.end_char,
                                                                               original_start_pos)

                entities.append(
                    NamedEntity(literal=entity.text,
                                type=entity.label_,
                                start_pos=start_pos,
                                end_pos=end_pos,
                                knowledge_base_id=entity.kb_id_,
                                )
                )

            counter += 1

        return entities
