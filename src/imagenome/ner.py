# ----------------------------------------------------------------------------------------------------------------------
# Copyright (C) 2023 Pablo Jané
#
# imagenome is free software: you can redistribute it and/or modify it under the terms of the GNU Affero General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any
# later version.
#
# imagenome is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied
# warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Affero General Public License for more
# details.
#
# You should have received a copy of the GNU Affero General Public License along with imagenome. If not, see
# <http://www.gnu.org/licenses/>.
# ----------------------------------------------------------------------------------------------------------------------

import json
import random
import os.path
import en_ner_jnlpba_md
from spacy.scorer import Scorer
from spacy.gold import GoldParse
from spacy.util import minibatch, compounding

from .utils import timer


def custom_optimizer(optimizer, learn_rate=0.001, beta1=0.9, beta2=0.999, eps=1e-8, L2=1e-6, max_grad_norm=1.0):
    """
    Function to customize spaCy's default optimizer
    """

    optimizer.learn_rate = learn_rate
    optimizer.beta1 = beta1
    optimizer.beta2 = beta2
    optimizer.eps = eps
    optimizer.L2 = L2
    optimizer.max_grad_norm = max_grad_norm

    return optimizer


class Ner:
    """
    A class to train a Named Entity Recognition model
    """

    def __init__(self):
        """
        Constructor method.
        """

        #Load nlp model and initialise attributes.
        self.model = en_ner_jnlpba_md.load()
        self.output_path = None
        self.ner = self.model.get_pipe("ner")
        self.train_data = None
        self.test_data = None
        self.losses = {}
        self.scores = {}
        self.metrics = {}

    @timer('Loading NER training data... ')
    def load_train_data(self, input_path):
        """
        Loads training data from .json file

        :param input_path: path to .json file containing training data
        :type input_path: str
        """

        json_to_train_ents = []
        with open(input_path, "r") as f:
            json_list = list(f)
            for json_str in json_list:
                result = json.loads(json_str)
                json_to_train_ents.append(result)
        self.train_data = json_to_train_ents[0]

    @timer('Loading NER test data... ')
    def load_test_data(self, input_path):
        """
        Loads test data from .json file

        :param input_path: path to .json file containing test data
        :type input_path: str
        """

        json_to_test_ents = []
        with open(input_path, "r") as f:
            json_list = list(f)
            for json_str in json_list:
                result = json.loads(json_str)
                json_to_test_ents.append(result)
        self.test_data = json_to_test_ents[0]

    @timer('Training NER model...\n')
    def train(self, n_iter=20):
        """
        Trains spaCy's NER model

        :param n_iter: number of iterations for the model training, defaults to 20
        :type n_iter: int, optional
        """

        # add labels

        self.ner.add_label("RADIOTRACER_S")
        self.ner.add_label("RADIOTRACER_L")

        # Get names of other pipes to disable them during training
        pipe_exceptions = ["ner", "trf_wordpiecer", "trf_tok2vec"]
        other_pipes = [pipe for pipe in self.model.pipe_names if pipe not in pipe_exceptions]
        with self.model.disable_pipes(*other_pipes):

            if self.model is None:
                self.optimizer = self.model.begin_training(component_cfg={"ner": {"conv_window": 3}})
                self.optimizer = custom_optimizer(self.optimizer, learn_rate=0.001)
            else:
                self.optimizer = self.model.resume_training(component_cfg={"ner": {"conv_window": 3}})
                self.optimizer = custom_optimizer(self.optimizer, learn_rate=0.001)


            print('\t\t\t\t\t{:^5}\t\t\t\t{:^5}\t\t\t\t\t{:^5}\t\t'.format('RADIOTRACER_S', 'RADIOTRACER_L', 'TOTAL'))
            print('\t{:^5}\t\t{:^5}\t{:^5}\t{:^5}\t\t{:^5}\t{:^5}\t{:^5}\t\t{:^5}\t{:^5}\t{:^5}'.format('LOSS',
                                                                                                        'P', 'R', 'F',
                                                                                                        'P', 'R', 'F',
                                                                                                        'P', 'R', 'F'))

            # Initialise training performance metrics dict
            self.metrics = {'losses': list(),
                            'RADIOTRACER': {'precision': list(),
                                            'recall': list(),
                                            'fscore': list()},
                            'RADIOTRACER_S': {'precision': list(),
                                              'recall': list(),
                                              'fscore': list()},
                            'RADIOTRACER_L': {'precision': list(),
                                              'recall': list(),
                                              'fscore': list()}}

            for itn in range(n_iter):
                random.shuffle(self.train_data)
                self.losses = {}

                # Batch up the examples using spaCy's minibatch
                batches = minibatch(self.train_data, size=compounding(4, 32, 1.001))
                for batch in batches:
                    texts, annotations = zip(*batch)
                    self.model.update(
                        texts,        # batch of texts
                        annotations,  # batch of annotations
                        drop=0.2,
                        sgd=self.optimizer,
                        losses=self.losses,
                    )

                self.evaluate()
                print('\t{:.2e}\t{:.3f}\t{:.3f}\t{:.3f}\t\t{:.3f}\t{:.3f}\t{:.3f}\t\t{:.3f}\t{:.3f}\t{:.3f}'
                      .format(self.losses['ner'],
                              self.scores['RADIOTRACER_S']['precision'],
                              self.scores['RADIOTRACER_S']['recall'],
                              self.scores['RADIOTRACER_S']['fscore'],
                              self.scores['RADIOTRACER_L']['precision'],
                              self.scores['RADIOTRACER_L']['recall'],
                              self.scores['RADIOTRACER_L']['fscore'],
                              self.scores['RADIOTRACER']['precision'],
                              self.scores['RADIOTRACER']['recall'],
                              self.scores['RADIOTRACER']['fscore']
                              ))

                # Store performance metrics for current training iteration
                self.metrics['losses'].append(self.losses['ner'])
                for label in ['RADIOTRACER', 'RADIOTRACER_S', 'RADIOTRACER_L']:
                    for metric in ['precision', 'recall', 'fscore']:
                        self.metrics[label][metric].append(self.scores[label][metric])

    def evaluate(self):
        """
        Computes and stores the training results of the model
        """

        labels = ['RADIOTRACER_S', 'RADIOTRACER_L']
        for label in labels:
            self.scores[label] = {}

        tp = 0.0
        fp = 1e-8
        fn = 1e-8

        scorer = Scorer()
        for input_, annot in self.test_data:
            doc_gold_text = self.model.make_doc(input_)
            gold = GoldParse(doc_gold_text, entities=annot["entities"])
            pred_value = self.model(input_)
            scorer.score(pred_value, gold)

        # Update RADIOTRACER entity scores (only)
        for label in labels:
            if label in scorer.ner_per_ents:
                self.scores[label]['precision'] = scorer.ner_per_ents[label].precision
                self.scores[label]['recall'] = scorer.ner_per_ents[label].recall
                self.scores[label]['fscore'] = scorer.ner_per_ents[label].fscore

                tp += scorer.ner_per_ents[label].tp
                fp += scorer.ner_per_ents[label].fp
                fn += scorer.ner_per_ents[label].fn

        precision = tp / (tp + fp)
        recall = tp / (tp + fn)
        if (precision + recall) == 0:
            fscore = 0.0
        else:
            fscore = 2 * (precision * recall) / (precision + recall)

        self.scores['RADIOTRACER'] = {'precision': precision,
                                      'recall': recall,
                                      'fscore': fscore}

    @timer('Saving NER model to disk... ')
    def savemodel(self, output_path='ner_model'):
        """
        Saves the model to an output directory

        :param output_path: path to the directory that will contain the NER model files
        :type output_path: str
        """

        self.output_path = os.path.abspath(output_path)
        self.model.to_disk(self.output_path)