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

import spacy
import mysql.connector

from .utils import timer


class Annotate:
    """
    A class to perform machine annotation on the "imagenome_db" MySQL database, with the help of the NER model

    :param password: MySQL password for "root" user at "localhost"
    :type password: str
    :param input_model_path: path to the directory containing the NER model, defaults to "ner_model"
    :type input_model_path: str, optional
    :param query_table: name of the query or source table used to extract data for annotation, defaults to "imagenome"
    :type query_table: str, optional
    """

    def __init__(self, password, input_model_path="ner_model", query_table="imagenome"):
        """
        Constructor method
        """
        self.output_table = ""
        self.query_table = query_table
        self.model = spacy.load(input_model_path)
        self.mydb = mysql.connector.connect(host="localhost", user="root", password=password, database="imagenome_db")
        self.mycursor = self.mydb.cursor(buffered=True)
        self.mytables = []

        # Get currently existing tables and store them in list
        self.update_table_list()

    def update_table_list(self):
        """
        Updates the list of tables to the ones defined in the MySQL "imagenome_db" database
        """

        self.mytables = []
        self.mycursor.execute("Show tables;")
        myresult = self.mycursor.fetchall()
        if len(myresult) > 0:
            for table in myresult:
                self.mytables.append(table[0])

    def create_table(self, output_name="imagenome_ann"):
        """
        Creates the annotation output table in the MySQL "imagenome_db" database

        :param output_name: name of the annotation output table, defaults to "imagenome_ann"
        :type output_name: str, optional
        """
        self.output_table = output_name
        if self.output_table in self.mytables:
            print("WARNING! The specified table already exists and will not be created")
            return

        self.sql_create = "CREATE TABLE IF NOT EXISTS `{}` ( `TAB_ID` INT NOT NULL AUTO_INCREMENT, " \
                          "`title` longtext, `abstract` longtext," \
                          "`journal` longtext, `pmid` longtext, " \
                          "`radiotracer_1_abstract` longtext, `radiotracer_2_abstract` longtext, " \
                          "`protein_1_abstract` longtext, `DNA_1_abstract` longtext, `cell_line_1_abstract` longtext," \
                          "`radiotracer_1_title` longtext, `radiotracer_2_title` longtext," \
                          "`protein_1_title` longtext, `DNA_1_title` longtext, `cell_line_1_title` longtext,"\
                          " PRIMARY KEY(`TAB_ID`)) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_bin " \
                          " PARTITION BY KEY(`TAB_ID`) PARTITIONS 220;".format(self.output_table)

        self.query = ("SELECT TAB_ID, title, abstract, journal, pmid FROM `{}`".format(self.query_table))

        self.mycursor.execute(self.sql_create)
        self.mycursor.execute(self.query)

        # Update tables list
        self.update_table_list()

    @timer('Performing annotations on the query database table using NER model... ')
    def annotate(self, output_name="imagenome_ann"):
        """
        Performs machine annotation on the abstracts defined in the query or source table of the "imagenome_db"
        MySQL database with the help of the NER model, and inserts them into a new MySQL database that has the following
        columns: "TAB_ID", "title", "abstract", "journal", "pmid", "radiotracer_1_abstract", "radiotracer_2_abstract",
        "protein_1_abstract", "DNA_1_abstract", "cell_line_1_abstract"

        :param output_name: name of the annotation output table, defaults to "imagenome_ann"
        :type output_name: str, optional
        """
        self.output_table = output_name
        if self.output_table not in self.mytables:
            print("WARNING! The specified table name cannot be found in the database and will not be filled. Try "
                  "using 'SqlDb.create_table()'")
            return

        self.query = ("SELECT TAB_ID, title, abstract, journal, pmid FROM `{}`".format(self.query_table))

        self.mycursor.execute(self.query)

        add_paper = "INSERT INTO `{}`  (`TAB_ID`, `title`, `abstract`," \
                    " `journal`, `pmid`, `radiotracer_1_abstract`, `radiotracer_2_abstract`, " \
                    "`protein_1_abstract`, `DNA_1_abstract`, `cell_line_1_abstract`, `radiotracer_1_title`, `radiotracer_2_title`, " \
                    "`protein_1_title`, `DNA_1_title`, `cell_line_1_title`) VALUES (".format(self.output_table)\
                    + "%s," *14 + "%s)"

        mycursor_ann = self.mydb.cursor(buffered=True)
        for (TAB_ID, title, abstract, journal, pmid) in self.mycursor:
            doc = self.model(abstract)
            doc_ents = []
            dict_ = {}
            for ent in doc.ents:
                doc_ents.append(ent.label_)
                dict_[str(ent.label_)] = str(ent.text)
            default_keys = ["RADIOTRACER_S", "RADIOTRACER_L", "PROTEIN", "DNA", "CELL_LINE"]
            null_keys = list(set(default_keys) - set(list(dict_.keys())))

            for keys in null_keys:
                dict_[str(keys)] = None

            doc2 = self.model(title)
            doc_ents2 = []
            dict2_ = {}
            for ent in doc2.ents:
                doc_ents2.append(ent.label_)
                dict2_[str(ent.label_)] = str(ent.text)
            default_keys = ["RADIOTRACER_S", "RADIOTRACER_L", "PROTEIN", "DNA", "CELL_LINE"]
            null_keys2 = list(set(default_keys) - set(list(dict2_.keys())))

            for keys in null_keys2:
                dict2_[str(keys)] = None
            values = (TAB_ID, str(title), str(abstract), str(journal), str(pmid),
                  str(dict_["RADIOTRACER_S"]),
                  str(dict_["RADIOTRACER_L"]), str(dict_["PROTEIN"]),
                    str(dict_["DNA"]), str(dict2_["CELL_LINE"]), str(dict2_["RADIOTRACER_S"]),
                  str(dict2_["RADIOTRACER_L"]), str(dict2_["PROTEIN"]),
                    str(dict2_["DNA"]), str(dict2_["CELL_LINE"]))

            dec_values = []
            for elem in values:
                if elem == 'None':
                    dec_values.append(None)
                else:
                    dec_values.append(elem)
            try:
                mycursor_ann.execute(add_paper, dec_values)
                self.mydb.commit()
            except:
                print("Error transfering entry with PMID: " + str(pmid))
                pass

        # Close cursors and database connection
        mycursor_ann.close()
        self.mycursor.close()
        self.mydb.close()

    def close(self):
        """
        Closes the open database connection and cursors initialised by default when instantiating the object
        """
        self.mycursor.close()
        self.mydb.close()