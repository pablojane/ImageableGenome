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
import os.path
import pandas as pd
from glob import glob
import mysql.connector

from .utils import timer


class SqlDb:
    """
    A class to create an MySQL table and fill it with the data from a set of source .parquet files using the filtering
    specifications defined in the corresponding set of .json files

    :param password: password for the MySQL user
    :type password: str
    :param parquet_path: path to parquet source file(s) directory, defaults to "parquet"
    :type parquet_path: str, optional
    :param json_path: path to .json filtering file(s) directory, defaults to "filtered"
    :type json_path: str, optional
    :param host: IP address to the working MySQL server, defaults to "localhost"
    :type host: str, optional
    :param user: MySQL user name, defaults to "root"
    :type user: str, optional
    :param database: name of the working MySQL database, defaults to "imagenome_db"
    :type database: str, optional

    """

    def __init__(self, password, parquet_path='parquet', json_path='filtered', host='localhost', user='root',
                 database='imagenome_db'):
        """
        Constructor method
        """
        self.host = host
        self.user = user
        self.database = database
        self.mydb = mysql.connector.connect(host=self.host, user=self.user, password=password, database=self.database)
        self.mycursor = self.mydb.cursor()
        self.parquet_path = os.path.abspath(parquet_path)
        self.parquet = glob(self.parquet_path + '/*')
        self.json_path = os.path.abspath(json_path)
        self.json = glob(self.json_path + '/*')
        self.table = pd.read_parquet(self.parquet[0], engine='pyarrow')
        self.table["class_value"] = 0
        self.table["clean_abstract"] = 0
        self.table["clean_title"] = 0
        self.mytables = []

        # Get currently existing tables and store them in list
        self.mycursor.execute("Show tables;")
        myresult = self.mycursor.fetchall()

        if len(myresult) > 0:
            for table in myresult:
                self.mytables.append(table[0])

    def create_table(self, name="imagenome"):
        """
        Creates MySQL table.

        :param name: name to your created table, defaults to "imagenome"
        :type name: str, optional
        """
        if name in self.mytables:
            print("WARNING! The specified table already exists and will not be created")
            return

        cols = self.table.columns
        ddl = ""
        for col in cols:
            ddl += "`{}` longtext,".format(col)

        ddl = "`TAB_ID` INT NOT NULL AUTO_INCREMENT," + ddl

        sql_create = "CREATE TABLE IF NOT EXISTS `{}` ({} , PRIMARY KEY(`TAB_ID`)) ENGINE=InnoDB " \
                 "DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci  PARTITION BY KEY(`TAB_ID`) " \
                 "PARTITIONS 220;".format(name, ddl[:-1])
        self.mycursor.execute(sql_create)
        self.mytables.append(name)

    @timer('Filling database table with TC-filtered files... ')
    def fill_table(self, name="imagenome"):
        """
        Fills a MySQL table with the data from the filtered .parquet file(s).

        :param name: name of the table to be filled, defaults to "imagenome"
        :type name: str, optional
        """
        if name not in self.mytables:
            print("WARNING! The specified table name cannot be found in the database and will not be filled. Try "
                  "using 'SqlDb.create_table()'")
            return

        for filename in self.json:
            with open(filename) as n:
                self.data = json.load(n)

            cols = "`,`".join([str(i) for i in self.table.columns.tolist()])
            self.sql = "INSERT INTO `{}` (`".format(name) + str(cols) + "`) VALUES (" + \
                       "%s,"*(len(self.table.columns.tolist())-1) + "%s)"

            #Store all the values in a dictionary
            for key, value in self.data.items():
                row = value
                row["clean_abstract"] = ""
                row["clean_title"] = ""

                self.row = tuple(row.values())
                self.mycursor.execute(self.sql, tuple(self.row))
                self.mydb.commit()

    def close(self):
        """
        Closes the open database connection and cursors initialised by default when instantiating the object
        """
        self.mycursor.close()
        self.mydb.close()