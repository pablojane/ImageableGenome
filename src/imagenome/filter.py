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
import spacy
import os.path
import pandas as pd
from glob import glob
from bounded_pool_executor import BoundedProcessPoolExecutor

from .utils import preprocess_text_tc, timer


# Build function for workers
def process(filename, model, save_path, max_lines=-1):
    """
    This function is called by the different workers launched in parallel in :func:`~filter.Filter.filter`. It processes
    each individual Pubmed .parquet file, running the classifier on each abstract string and then storing the whole row
    to a dictionary with the PMID value as key, when the "POSITIVE_NUCL_MED" category > 0.5.
    The dictionary is finally saved to a .json file.

    :param filename: path to the source .parquet file
    :type filename: str
    :param model: text categorizer model
    :type model: spaCy TextCategorizer object
    :param save_path: path to the output .json file
    :type save_path: str
    :param max_lines: max number of positive entries stored to a .json file, defaults to -1
    :type max_lines:  int, optional
    """
    number = os.path.splitext(os.path.basename(filename))[0]
    table = pd.read_parquet(str(filename), engine='pyarrow')
    d = table.to_dict("index")
    found_loop = {}
    count = 0
    for elem in d.values():
        if elem["abstract"] != None:
            if len(elem["abstract"]) > 10:
                doc = model(preprocess_text_tc(elem["abstract"]))
                if doc.cats["POSITIVE_NUCL_MED"] > 0.50:
                    elem["class_value"] = doc.cats["POSITIVE_NUCL_MED"]
                    found_loop[elem["pmid"]] = elem
                    count = count + 1
                    if count > max_lines > 0:
                         break
    path = os.path.join(save_path, str(number) + ".json")
    with open(path, 'w', encoding="utf8") as n:
        json.dump(found_loop.copy(), n)


class Filter:
    """
    A class to classify and keep the PubMed entries labeled as Nuclear Medicine Positive.

    :param model_path: path to the directory containing the text categorizer model
    :type model_path: str
    """

    def __init__(self, model_path):
        """
        Constructor method
        """

        self.input_path = None
        self.parquet_files = None
        self.output_path = None
        self.max_workers = None

        self.input_model_path = os.path.abspath(model_path)
        self.model = spacy.load(self.input_model_path)

    @timer('Filtering parsed *.parquet data using TC model... ')
    def filter(self, input_path='.', output_path='.', max_workers=1, max_lines=-1, verbose=False):
        """
        Runs the text categorizer on the PubMed parquet files and stores the results. Iterates over the PubMed
        parquet files' rows and runs the classifier on each abstract string. Stores the whole row to a dictionary
        with the PMID value as key, when the "POSITIVE_NUCL_MED" category > 0.5. The dictionary is finally saved to a
        .json file

        :param input_path: path to the PubMed .parquet files directory, defaults to '.'
        :type input_path: str, optional
        :param output_path: path to .json files output directory, defaults to '.'
        :type output_path: str, optional
        :param max_workers: maximum size of the pool of workers for parallel processing, defaults to 1
        :type max_workers: int, optional
        :param max_lines: max number of positive entries stored to .json file, defaults to -1 (which makes the function
                          process the entire file)
        :type max_lines:  int, optional
        :param verbose: activates verbose mode if `True`, defaults to `False`
        :type verbose: bool, optional
        """

        # Build the necessary directories
        self.input_path = os.path.abspath(input_path)
        self.parquet_files_total = glob(self.input_path + '/*')
        self.output_path = os.path.abspath(output_path)
        os.makedirs(self.output_path, exist_ok=True)
        self.max_workers = max_workers
        self.json_files_total = glob(self.output_path + '/*')
        self.already_filtered = []
        for elem in self.json_files_total:
            json_number = os.path.splitext(os.path.basename(elem))[0]
            self.already_filtered.append(os.path.join(str(self.input_path), str(json_number) + ".parquet"))
        self.parquet_files_update = set(self.parquet_files_total) - set(self.already_filtered)
        self.output_path = os.path.abspath(output_path)
        os.makedirs(self.output_path, exist_ok=True)
        self.max_workers = max_workers

        with BoundedProcessPoolExecutor(max_workers=self.max_workers) as worker:
            for filename in self.parquet_files_update:
                if verbose:
                    print(f'Worker initialization: {filename}')
                worker.submit(process, filename, self.model, self.output_path, max_lines=max_lines)