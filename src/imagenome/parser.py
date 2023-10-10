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
import pandas as pd
from glob import glob
import pubmed_parser as pp
from bounded_pool_executor import BoundedProcessPoolExecutor

from .utils import timer


def process_file(file, save_path, verbose=False):
    """
    Reads an input PubMed/Medline .xml file, parses it and saves it as a .parquet file

    :param file: input .xml file absolute path
    :type file: str
    :param save_path: output .parquet file directory path
    :type save_path: str
    :param verbose: activates verbose mode if `True`, defaults to `False`
    :type verbose: bool, optional
    """
    if verbose:
        print(f'\nStart processing file {file} ...')

    try:
        pp_list = pp.parse_medline_xml(file)
    except:
        print('\nWARNING! file ' + file + ' is corrupt and could not be loaded. Please, remove the corrupt file and '
              'download it again.')
    else:
        pp_df = pd.DataFrame(pp_list)
        number = file[-11:-7]
        path = os.path.join(save_path, str(number) + ".parquet")
        pp_df.to_parquet(path, engine='pyarrow')

        if verbose:
            print(f'{file} was successfully processed...')


class Parser:
    """
    A class to download, parse and store the PubMed/Medline database
    """

    def __init__(self):
        """
        Constructor method
        """

        # Initialise attributes
        self.data_path = None
        self.output_path = None
        self.max_workers = None
        self.pubmed_files = None

    @timer('Downloading files from ftp server... ')
    def download(self, data_path='.', ftp_list=[]):
        """
        Downloads the PubMed/Medline database from the ftp server to a specified directory path

        :param data_path: path to the directory where the PubMed/Medline database will be downloaded, defaults to "."
        :type data_path: str, optional
        :param ftp_list: list of paths to the PubMed/Medline ftp server directories/files to download, defaults as an
                         empty list
        :type ftp_list: list, optional
        """
        # Store current working direcotry
        cwd = os.getcwd()
        self.data_path = os.path.abspath(data_path)

        # Create specified directory (if not existing) and download files, then return to previous working directory
        os.makedirs(self.data_path, exist_ok=True)
        os.chdir(self.data_path)
        if ftp_list:
            for ftp_path in ftp_list:
                os.system('wget -q --mirror --accept "*.xml.gz" ' + ftp_path)
        else:
            os.system('wget -q --mirror --accept "*.xml.gz" ftp://ftp.ncbi.nlm.nih.gov/pubmed/baseline/')
        os.chdir(cwd)

    @timer('Parsing raw text files and saving the results in *.parquet format... ')
    def parse(self, data_path='.', output_path='.', max_workers=1, verbose=False):
        """
        Loads and parses all the .xml PubMed/Medline files in a specified directory, and then stores them into a given
        output directory as a series of .parquet files using parallel computing

        :param data_path: path to the directory where the target PubMed/Medline database .xml files are stored, defaults
                          to "."
        :type data_path: str, optional
        :param output_path: path to the directory where the parsed .parquet files will be stored, defaults to "."
        :type output_path: str, optional
        :param max_workers: maximum size of the pool of workers for parallel processing, defaults to 1
        :type max_workers: int, optional
        :param verbose: activates verbose mode if `True`, defaults to `False`
        :type verbose: bool, optional
        """
        # Input checks
        if not os.path.isdir(data_path):
            raise IOError(f'The specified path {data_path} holding the files to parse does not exit')

        # Build necessary directories
        self.data_path = os.path.abspath(data_path)
        self.pubmed_files = glob(self.data_path + '/*')
        self.output_path = os.path.abspath(output_path)
        os.makedirs(self.output_path, exist_ok=True)
        self.max_workers = max_workers

        # Launch workers for parallel mapping
        with BoundedProcessPoolExecutor(max_workers=self.max_workers) as worker:
            for filename in self.pubmed_files:
                if verbose:
                    print(f'Worker initialization: {filename}')
                worker.submit(process_file, filename, self.output_path)