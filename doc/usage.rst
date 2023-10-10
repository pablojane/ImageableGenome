Usage
=====

There are two test scripts available in the *test/* directory illustrating all the steps in the process:

- main_models.py: downloading, parsing and saving the NLM MEDLINE/Pubmed baseline dataset and running the pre-trained TC.
- main_annotate.py: saving the results obtained from the text classification step to an SQL table and running the pre-trained NER model to annotate it. This script requires the main_models.py script to have previously run successfully, as well as the previous setup of a mysql database with the following default values,

  - name: imagenome_db
  - host: localhost
  - user: root
  - password: password

These tests can be easily modified to process the entire dataset and to use different mysql database connection parameters, as well as to perform model training/testing using custom datasets. To run them, simply open a terminal on the repository root directory and execute the commands

::

   cd test/
   python3 main_models.py
   python3 main_annotate.py

