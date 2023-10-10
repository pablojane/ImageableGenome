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
import mygene
import numpy as np
import pandas as pd


class Translate:
    """
    A class to perform protein to gene translation using as input an Excel file exported from the Imagenome MySQL
    database
    """

    def __init__(self):
        """
        Constructor method
        """
        self.input_excel_path = None
        self.output_excel_path = None
        self.df = None
        self.mg = None
        self.g = None

    def translate(self, input_excel_path=".", output_excel_path="."):
        """
        Performs protein to gene translation using as input an Excel file exported from the Imagenome MySQL database.
        Loads the file as a Pandas dataframe, reads the column "protein_1_abstract", creates three new columns
        ("SIMILAR_PROTEIN", "SIMILAR_GENE_LIST", "SIMILAR_ENSEMBL"), makes a query to the mygene REST API and fills
        these columns with the results. Lastly, it saves the new dataframe to an output Excel file

        :param input_excel_path: path to the Excel file exported from the Imagenome sql database, defaults to "."
        :type input_excel_path: str, optional
        :param output_excel_path: name of the output annotated Excel file, defaults to "."
        :type output_excel_path: str, optional

        """
        self.input_excel_path = os.path.abspath(input_excel_path)
        self.output_excel_path = os.path.abspath(output_excel_path)
        self.df = pd.read_excel(self.input_excel_path)
        self.df["SIMILAR_PROTEIN"] = np.nan
        self.df["SIMILAR_GENE_LIST"] = np.nan
        self.df["SIMILAR_ENSEMBL"] = np.nan
        self.mg = mygene.MyGeneInfo()

        for index, row in self.df.iterrows():
            protein = row["protein_1_abstract"]
            try:
                self.g = self.mg.query(protein, species='human', fields= 'symbol,name,ensembl')
                if self.g["hits"] != []:
                    self.df.loc[index, "SIMILAR_PROTEIN"] = str(self.g["hits"][0]["name"])
                    if "ensembl" in self.g["hits"][0].keys():
                        self.df.loc[index, "SIMILAR_ENSEMBL"] = str(self.g["hits"][0]["ensembl"]["gene"])
                    if "symbol" in self.g["hits"][0].keys():
                        self.df.loc[index, "SIMILAR_GENE_LIST"] = str(self.g["hits"][0]["symbol"])
            except:
                pass