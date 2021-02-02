import logging
import random

from models.named_entity import NamedEntity
from nlp.nlp_manager import NLPManager
from nlp.pipelines.text_preprocessing.text_preprocessing import TextPreprocessing
from wikipedia.entity_linker_evaluation import measure_performance
from tqdm import tqdm

from wikipedia import wikipedia_processor
from spacy.util import compounding, minibatch
from wikipedia.kb_creator import read_kb
from resources.resources_manager import ResourcesManager


# Todo make sure to disable custom pipelines.

class WikidataEntityLinker(object):
    nlp_model_name = "wiki_el"
    entity_linker = None
    other_pipes = []
    kb = None  # Loading Wikidata KnowledgeBase For training.

    epochs = 10  # Number of training iterations (default 10)
    dropout = 0.5  # Dropout to prevent overfitting (default 0.5)
    lr: float = 0.005  # Learning rate (default 0.005)
    l2: float = 1e-6  # L2 regularization
    labels_discard = None  # NER labels to discard (default None)

    # Limitations
    train_articles = 1000  # Training articles (for all articles set: None)
    dev_articles: int = 100  # Dev test articles (for all articles set: None)

    wikidata_link = "https://www.wikidata.org/wiki/"  # link to training_files website.

    def __init__(self, nlp, resources_manager: ResourcesManager):
        self.__nlp = nlp
        self.kb_path = resources_manager.get_model_path("wiki_kb")
        self.training_path = resources_manager.get_wiki_training_path("wiki_training_entities")
        self.nlp_manager = NLPManager(resources_manager)
        self.create_pipe()

        try:
            self.__nlp.add_pipe(self.entity_linker)
            self.load_nlp_model()
        except FileNotFoundError:
            self.progress_bar: tqdm = self.create_progress_bar(5, "Initializing Entity Linker")
            # Entity Linker Pipelines
            self.load_dependent_models()  # 1.Step
            self.read_training_dataset_from_kb()  # 2.Step
            self.prepare_pipe_for_training()  # 3.Step
            self.start_training()  # 4.Step
            self.save_nlp_model()  # 5.Step

    def create_pipe(self):
        self.entity_linker = self.__nlp.create_pipe(
            name="entity_linker",
            config={
                "pretrained_vectors": self.__nlp.vocab.vectors.name,
                "labels_discard": self.labels_discard,
            },
        )

    def load_dependent_models(self):
        self.print_progress_bar("Step 1: Loading Dependent Entity Linker Models", True)

        self.nlp_manager.check_pretrained_ner(self.__nlp)
        self.nlp_manager.check_pretrained_word_vectors(self.__nlp)
        self.kb = read_kb(self.__nlp, self.kb_path)
        logging.info("Loaded Knowledge Base from '%s'" % self.kb_path)

    def read_training_dataset_from_kb(self):
        """ This method creates two lists of indices into the training file: one with indices for the
         training examples, and one for the dev examples."""
        self.print_progress_bar("Step 2: Reading training & dev dataset from {}".format(self.training_path), True)

        self.train_indices, self.dev_indices = wikipedia_processor.read_training_indices(
            self.training_path
        )
        logging.info(
            "Training set has {} articles, limit set to roughly {} articles per epoch".format(
                len(self.train_indices), self.train_articles if self.train_articles else "all"
            )
        )
        logging.info(
            "Dev set has {} articles, limit set to rougly {} articles for evaluation_service".format(
                len(self.dev_indices), self.dev_articles if self.dev_articles else "all"
            )
        )
        if self.dev_articles:
            self.dev_indices = self.dev_indices[0:self.dev_articles]

    def prepare_pipe_for_training(self):
        self.print_progress_bar("Step 3: Creating Wikidata Entity Linker pipe", True)
        if self.labels_discard:
            labels_discard = [x.strip() for x in self.labels_discard.split(",")]
            logging.info(
                "Discarding {} NER types: {}".format(len(labels_discard), labels_discard)
            )
        else:
            self.labels_discard = []
        self.entity_linker.set_kb(self.kb)  # Applying KB to entity linker
        self.__nlp.add_pipe(self.entity_linker, last=True)
        self.other_pipes = [pipe for pipe in self.__nlp.pipe_names if pipe != "entity_linker"]

    def start_training(self):
        self.print_progress_bar("Step 4: Creating and training an Entity Linking pipe for {} epochs".format(
            self.epochs
        ), True)

        with self.__nlp.disable_pipes(*self.other_pipes):  # only train Entity Linking
            optimizer = self.__nlp.begin_training()
            optimizer.learn_rate = self.lr
            optimizer.L2 = self.l2

        logging.info("Dev Baseline Accuracies:")
        dev_data = wikipedia_processor.read_el_docs_golds(
            nlp=self.__nlp,
            entity_file_path=self.training_path,
            dev=True,
            line_ids=self.dev_indices,
            kb=self.kb,
            labels_discard=self.labels_discard,
        )

        measure_performance(
            dev_data, self.kb, self.entity_linker, baseline=True, context=False, dev_limit=len(self.dev_indices)
        )
        self.iterate_over_epochs(optimizer)
        # Saving model with Wikidata entity linker

    def iterate_over_epochs(self, optimizer):
        logging.info("STEP 3.B Iterating over Epochs")
        for itn in range(self.epochs):
            random.shuffle(self.train_indices)
            losses = {}
            batches = minibatch(self.train_indices, size=compounding(8.0, 128.0, 1.001))
            batchnr = 0
            articles_processed = 0

            # we either process the whole training file, or just a part each epoch
            bar_total = len(self.train_indices)
            if self.train_articles:
                bar_total = self.train_articles

            # Iterate over the training but without entity linker pipe
            with tqdm(total=bar_total, leave=False, desc="Epoch " + str(itn)) as pbar:
                for batch in batches:
                    if not self.train_articles or articles_processed < self.train_articles:
                        with self.__nlp.disable_pipes("entity_linker"):
                            train_batch = wikipedia_processor.read_el_docs_golds(
                                nlp=self.__nlp,
                                entity_file_path=self.training_path,
                                dev=False,
                                line_ids=batch,
                                kb=self.kb,
                                labels_discard=self.labels_discard,
                            )
                            try:
                                docs, golds = zip(*train_batch)
                            except ValueError:
                                continue
                        try:
                            # With disable other pipe only entity linker is trained.
                            with self.__nlp.disable_pipes(*self.other_pipes):
                                self.__nlp.update(
                                    docs=docs,
                                    golds=golds,
                                    sgd=optimizer,
                                    drop=self.dropout,
                                    losses=losses,
                                )
                                batchnr += 1
                                articles_processed += len(docs)
                                pbar.update(len(docs))
                        except Exception as e:
                            logging.error("Error updating batch:" + str(e))
            if batchnr > 0:
                logging.info(
                    "Epoch {} trained on {} articles, train loss {}".format(
                        itn, articles_processed, round(losses["entity_linker"] / batchnr, 2)
                    )
                )
                # re-read the dev_data (data is returned as a generator)
                dev_data = wikipedia_processor.read_el_docs_golds(
                    nlp=self.__nlp,
                    entity_file_path=self.training_path,
                    dev=True,
                    line_ids=self.dev_indices,
                    kb=self.kb,
                    labels_discard=self.labels_discard,
                )
                measure_performance(
                    dev_data,
                    self.kb,
                    self.entity_linker,
                    baseline=False,
                    context=True,
                    dev_limit=len(self.dev_indices),
                )

    @staticmethod
    def create_progress_bar(steps: int, desc: str):
        return tqdm(total=steps, desc=desc, bar_format='{l_bar}{bar}{n_fmt}/{total_fmt}')

    def print_progress_bar(self, description, increase_level: bool = False):
        self.progress_bar.set_description(desc=description)
        if increase_level:
            self.progress_bar.update()

    def save_nlp_model(self):
        self.print_progress_bar("Step 5: Saving Wikidata Entity Linker nlp Model", True)
        self.nlp_manager.save_nlp_model(self.__nlp, self.nlp_model_name)

    def load_nlp_model(self):
        self.__nlp = self.nlp_manager.load_saved_nlp_model(self.__nlp, self.nlp_model_name)

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
                                page_id="",
                                start_pos=start_pos,
                                end_pos=end_pos,
                                knowledge_base_id=entity.kb_id_,
                                link=self.wikidata_link + entity.kb_id_)
                )

            counter += 1

        return entities
