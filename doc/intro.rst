Introduction
============

The *imagenome* package contains all the necessary tools to reproduce the data pipeline of the Imageable Genome project.

Here are the main steps in the Imageable Genome pipeline:

- Training a text classifier (TC) to detect abstracts concerning research on radiopharmaceuticals.
- Training a Named Entity Recognition (NER) model to detect radiopharmaceuticals, genes, and proteins.
- Downloading, parsing and saving the entire NLM MEDLINE/Pubmed baseline dataset to a series of parquet files. (about 40GB)
- Running the text classifier on the 20,000,000 abstracts within the NLM/ Medline dataset in order to detect all abstracts concerning research on radiopharmaceuticals.
- Creating an SQL table with the results of the text classification step.
- Annotating all the abstracts and titles in the SQL table with the NER model and saving it to a new SQL table.
- Filtering all the entries in the annotated SQL table according to a series of rules (mainly the fact that they mention a protein or gene and a radiopharmaceutical)

Check out the :doc:`Installation <install>` section for instructions to install the software or the :doc:`Usage <usage>` section for information on how to use the library.

Requirements
------------
This package was developed for Python 3.8 and Ubuntu20.04(x86_64). The use of different Python versions and/or other Linux distributions/versions might lead to unexpected issues and the instructions specified here may not apply. This also applies to versions of the required external software packages.

In order to avoid package dependency issues, we strongly recommend to set up a specific Python virtual environment to install and run *imagenome* (see `venv <https://docs.python.org/3.8/library/venv.html>`_).


- `pip <https://pypi.org/project/pip/>`_ needs to be pre-installed (v20.0.2). You can do so using the terminal commands

::

    sudo apt update
    sudo apt install python3-pip

- `Wheel <https://pypi.org/project/wheel/>`_ needs to be pre-installed (v.0.37.1). You can do so, once pip has been successfully installed, using the terminal command

::

    pip install wheel==0.37.1


- The final database is stored to a SQL database and requires mysql (v8.0.29) to be installed in your machine. You can use this `tutorial <https://www.digitalocean.com/community/tutorials/how-to-install-mysql-on-ubuntu-20-04>`_ to install mysql and set up the database. After doing so, some additional mysql-related tools have to be installed using the terminal commands

::

    sudo apt update
    sudo apt install libmysqlclient-dev

- A database, user and password must be set up to run the imagenome.SqlDb and imagenome.Annotate classes.

Data use
--------
All data used in this pipeline are obtained from the
NLM MEDLINE/Pubmed baseline dataset ("Courtesy of the U.S. National Library of Medicine",
https://www.nlm.nih.gov/databases/download/pubmed_medline.html) and were only used  for meta-analysis / systematic review purposes.

The training and testing datasets curated by the Imageable Genome team and used to generate the pre-trained TC and NER models included in the *imagenome* package are not publicly available at the moment due to copyright issues that need to be resolved.

Authors
-------
- Pablo Jané (pablojane@hotmail.es)
- Eduardo Jané (eduardo.jane.soler@gmail.com)

License
-------
*imagenome* is copyright (C) 2023 of Pablo Jané and is distributed under the terms of the Affero GNU General Public License (GPL) version 3 or later.


