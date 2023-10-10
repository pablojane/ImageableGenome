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

import os
import json
import random

import en_core_sci_md
import matplotlib.pyplot as plt
from spacy.util import minibatch, compounding

from .utils import preprocess_text_tc, timer


class TextClassification:

    """
    A class to train a Text Categorizer model to identify Nuclear Medicine texts
    """

    def __init__(self):
        # Load NLP model and initialise attributes.
        self.model = en_core_sci_md.load()
        self.output_path = None
        self.train_data = None
        self.test_data = None
        self.textcat = None
        self.losses = {}
        self.scores = {}
        self.metrics = {}

    @timer('Loading TC training data... ')
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

    @timer('Loading TC test data... ')
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
        (self.dev_texts, self.dev_cats) = zip(*self.test_data)

    def add_pipe(self):
        """
        Adds the Text Categorizer model to spaCy's pipe to train, including the labels 'POSITIVE_NUCL_MED' and
        'NEGATIVE_NUCL_MED'
        """
        self.textcat = self.model.create_pipe("textcat", config={"exclusive_classes": True, "architecture": "ensemble"})
        self.model.add_pipe(self.textcat, last=True)
        self.textcat.add_label("POSITIVE_NUCL_MED")
        self.textcat.add_label("NEGATIVE_NUCL_MED")

    def evaluate(self, tokenizer, textcat, texts, cats, thr=0.5):
        """
        Computes the training performance metrics of the model

        :param tokenizer: tokenizer model
        :type tokenizer: spaCy's Tokenizer object
        :param textcat: text categorizer model
        :type textcat: spaCy's TextCategorizer object
        :param texts: texts used for training metrics computation
        :type texts: list(str)
        :param cats: categories corresponding to the input texts used as gold standard to compute training metrics
        :type cats: list(str)
        :param thr: prediction score threshold for category 'POSITIVE_NUCL_MED', defaults to 0.5
        :type thr: float, optional
        """
        docs = (tokenizer(text) for text in texts)
        tp = 0.0  # True positives
        fp = 1e-8  # False positives
        fn = 1e-8  # False negatives
        tn = 0.0  # True negatives
        for i, doc in enumerate(textcat.pipe(docs)):
            gold = cats[i]["cats"]
            for label, score in doc.cats.items():
                if label not in gold:
                    continue
                if label == "NEGATIVE_NUCL_MED":
                    continue
                if score >= thr and gold[label] >= 0.5:
                    tp += 1.0
                elif score >= thr and gold[label] < 0.5:
                    fp += 1.0
                elif score < thr and gold[label] < 0.5:
                    tn += 1
                elif score < thr and gold[label] >= 0.5:
                    fn += 1
        precision = tp / (tp + fp)
        recall = tp / (tp + fn)
        specificity = tn / (tn + fp)
        if (precision + recall) == 0:
            f_score = 0.0
        else:
            f_score = 2 * (precision * recall) / (precision + recall)
        return {"textcat_p": precision, "textcat_r": recall, "textcat_f": f_score, "textcat_s": specificity}


    def get_roc_auc(self, texts, cats, delta_thr=0.01, plot_roc=False):
        """
        Computes the receiver operating characteristic (ROC) area under curve (AUC) of the model using numerical
        integration (trapezoid method)

        :param texts: texts used for training metrics computation
        :type texts: list(str)
        :param cats: categories corresponding to the input texts used as gold standard to compute training metrics
        :type cats: list(str)
        :param delta_thr: prediction score threshold resolution used to compute the points of the ROC, defaults to 0.01
        :type delta_thr: float, optional
        :param plot_roc: flag indicating whether to plot (True) the ROC or not (False), defaults to False
        :type plot_roc: bool, optional

        :return: tuple containing the ROC AUC value and the :math:`x` and :math:`y` axes of the ROC
        :rtype: tuple(float, list, list)
        """

        N = int(1/delta_thr)
        tpr = list()
        fpr = list()
        for i in reversed(range(N+1)): # Sweep classification threshold values from 1.0 to 0.0 for proper sorting
            scores = self.evaluate(self.model.tokenizer, self.textcat, texts, cats, thr=i/N)
            tpr.append(scores["textcat_r"])
            fpr.append(1-scores["textcat_s"])

        # Integrate area under ROC curve using trapezoidal rule (precision will strongly depend on delta_thr)
        auc = 0
        for i in range(len(fpr) - 1):
            auc += (fpr[i + 1] - fpr[i]) * (tpr[i + 1] + tpr[i]) / 2.0

        if plot_roc:
            plt.figure()
            plt.plot(fpr, tpr, label='AUC = '+str(auc))
            plt.xlabel('False Positive Rate (FPR) [-]')
            plt.ylabel('True Positive Rate (TPR) [-]')
            plt.title("Receiver Operating Characteristic (ROC) curve")
            plt.legend()
            plt.tight_layout(pad=0.5)

        return auc, fpr, tpr


    def get_auc_Nsq(self, texts, cats, s_frac=1.0):

        """
        Computes the receiver operating characteristic (ROC) area under curve (AUC) of the model using Algorithm 1 of
        reference “Fawcett, Tom. (2004). ROC Graphs: Notes and Practical Considerations for Researchers. Machine
        Learning. 31. 1-38.”, having a computational cost of :math:`O(N^2)` with :math:`N` being the test sample size

        :param texts: texts used for training metrics computation
        :type texts: list(str)
        :param cats: categories corresponding to the input texts used as gold standard to compute training metrics
        :type cats: list(str)
        :param s_frac: fraction of the total input test data used to compute the ROC AUC, defaults to 1.0
        :type s_frac: float, optional

        :return: ROC AUC value
        :rtype: float
        """

        pos = list()
        neg = list()
        s = int(s_frac*len(texts))
        for text, cat in random.sample(list(zip(texts, cats)), s):
            if cat["cats"]["POSITIVE_NUCL_MED"] == 1.0 and cat["cats"]["NEGATIVE_NUCL_MED"] == 0.0:
                pos.append(text)
            elif cat["cats"]["POSITIVE_NUCL_MED"] == 0.0 and cat["cats"]["NEGATIVE_NUCL_MED"] == 1.0:
                neg.append(text)
            else:
                continue

        N = len(pos) * len(neg)
        auc = 0.0
        for p in pos:
            doc_pos = self.model.tokenizer(p)
            doc_pos = self.textcat(doc_pos)
            for n in neg:
                doc_neg = self.model.tokenizer(n)
                doc_neg = self.textcat(doc_neg)
                if doc_pos.cats["POSITIVE_NUCL_MED"] >= doc_neg.cats["POSITIVE_NUCL_MED"]:
                    auc += 1.0
        auc /= N

        return auc


    def get_auc_Nlog2N(self, texts, cats):

        """
        Computes the receiver operating characteristic (ROC) area under curve (AUC) of the model using Algorithm 2 of
        reference “Fawcett, Tom. (2004). ROC Graphs: Notes and Practical Considerations for Researchers. Machine
        Learning. 31. 1-38.”, having a computational cost of :math:`O(N \\log N)` with :math:`N` being the test sample
        size

        :param texts: texts used for training metrics computation
        :type texts: list(str)
        :param cats: categories corresponding to the input texts used as gold standard to compute training metrics
        :type cats: list(str)

        :return: ROC AUC value
        :rtype: float
        """

        scores = [self.textcat(self.model.tokenizer(text)).cats["POSITIVE_NUCL_MED"] for text in texts]
        sort_idx = list(reversed([i[0] for i in sorted(enumerate(scores), key=lambda x: x[1])]))

        n_pos = 0
        n_neg = 0
        n_neg_eq = 0
        n_pos_eq = 0
        n_pos_gr = 0
        auc = 0
        for i, j in enumerate(sort_idx):

            if i != 0 and scores[j] == scores[sort_idx[i-1]]:
                if cats[sort_idx[i-1]]["cats"]["POSITIVE_NUCL_MED"] == 1.0 and cats[sort_idx[i-1]]["cats"]["NEGATIVE_NUCL_MED"] == 0.0:
                    n_pos_eq += 1
                elif cats[sort_idx[i-1]]["cats"]["POSITIVE_NUCL_MED"] == 0.0 and cats[sort_idx[i-1]]["cats"]["NEGATIVE_NUCL_MED"] == 1.0:
                    n_neg_eq += 1
            else:
                n_neg_eq = 0
                n_pos_eq = 0

            if cats[j]["cats"]["POSITIVE_NUCL_MED"] == 1.0 and cats[j]["cats"]["NEGATIVE_NUCL_MED"] == 0.0:
                n_pos_eq += 1
                n_pos += 1
            elif cats[j]["cats"]["POSITIVE_NUCL_MED"] == 0.0 and cats[j]["cats"]["NEGATIVE_NUCL_MED"] == 1.0:
                n_neg_eq += 1
                n_neg += 1

            auc += n_neg_eq*n_pos_gr + (n_pos_eq*n_neg_eq)/2.0

            if cats[j]["cats"]["POSITIVE_NUCL_MED"] == 1.0 and cats[j]["cats"]["NEGATIVE_NUCL_MED"] == 0.0:
                n_pos_gr += 1

        auc /= (n_pos*n_neg)

        return auc

    @timer('Training TC model...\n')
    def train(self, add_pipe=True, n_iter=10):
        """
        Trains spaCy's TextCategorizer model

        :param add_pipe: adds new "textcat" pipe to the loaded spaCy model if `True`, defaults to `True`
        :type add_pipe: bool, optional
        :param n_iter: number of iterations for the TextCategorizer model training, defaults to 10
        :type n_iter: int, optional
        """
        if add_pipe:
            self.add_pipe()

        # Start training
        # Disabling other components
        other_pipes = [pipe for pipe in self.model.pipe_names if pipe != 'textcat']
        with self.model.disable_pipes(*other_pipes):  # only train textcat
            optimizer = self.model.begin_training()

            print('\t{:^5}\t{:^5}\t{:^5}\t{:^5}'.format('LOSS', 'P', 'R', 'F'))

            # Initialise training performance metrics dict
            self.metrics = {'losses': list(),
                            'precision': list(),
                            'recall': list(),
                            'fscore': list(),
                            'specificity': list()}

            # Performing training
            for i in range(n_iter):
                self.losses = {}
                batches = minibatch(self.train_data, size=compounding(4., 32., 1.001))
                for batch in batches:
                    texts, annotations = zip(*batch)
                    self.model.update([preprocess_text_tc(text) for text in texts], annotations,
                                      sgd=optimizer, drop=0.2, losses=self.losses)

                # Calling the self.evaluate() function and printing the scores
                with self.textcat.model.use_params(optimizer.averages):
                    self.scores = self.evaluate(self.model.tokenizer, self.textcat,
                                                [preprocess_text_tc(text) for text in self.dev_texts], self.dev_cats)
                print('\t{0:.3f}\t{1:.3f}\t{2:.3f}\t{3:.3f}'
                      .format(self.losses['textcat'],
                              self.scores['textcat_p'], self.scores['textcat_r'], self.scores['textcat_f']))

                # Store performance metrics for current training iteration
                self.metrics['losses'].append(self.losses['textcat'])
                self.metrics['precision'].append(self.scores['textcat_p'])
                self.metrics['recall'].append(self.scores['textcat_r'])
                self.metrics['fscore'].append(self.scores['textcat_f'])
                self.metrics['specificity'].append(self.scores['textcat_s'])

    @timer('Saving TC model to disk... ')
    def savemodel(self, output_path='texcat_model'):
        """
        Saves the text classifying model

        :param output_path: path to the directory that will contain the text classifying model files, defaults to "textcat_model"
        :type output_path: str, optional
        """
        self.output_path = os.path.abspath(output_path)
        self.model.to_disk(self.output_path)