# *imagenome* - The Imageable Genome

The *imagenome* package contains all the necessary tools to reproduce the data pipeline of the Imageable Genome project. 

Here are the main steps in the Imageable Genome pipeline:

- Training a text classifier (TC) to detect abstracts concerning research on radiopharmaceuticals. 
- Training a Named Entity Recognition (NER) model to detect radiopharmaceuticals, genes, and proteins. 
- Downloading, parsing and saving the entire NLM MEDLINE/Pubmed baseline dataset to a series of parquet files. (about 40GB)
- Running the text classifier on the 20,000,000 abstracts within the NLM/ Medline dataset in order to detect all abstracts concerning research on radiopharmaceuticals.
- Creating an SQL table with the results of the text classification step. 
- Annotating all the abstracts and titles in the SQL table with the NER model and saving it to a new SQL table. 
- Filtering all the entries in the annotated SQL table according to a series of rules (mainly the fact that they mention a protein or gene and a radiopharmaceutical)

## Before starting

This package was developed for Python 3.8 and Ubuntu20.04(x86_64). The use of different Python versions and/or other Linux distributions/versions might lead to unexpected issues and the instructions specified in this file may not apply. This also applies to versions of the required external software packages.

In order to avoid package dependency issues, we strongly recommend to set up a specific Python virtual environment to install and run *imagenome* (see [venv](https://docs.python.org/3.8/library/venv.html)). 

Some pre-requisites:

* [pip](https://pypi.org/project/pip/) needs to be pre-installed (v20.0.2). You can do so using the terminal commands
```
sudo apt update
sudo apt install python3-pip
```


* [Wheel](https://pypi.org/project/wheel/) needs to be pre-installed (v.0.37.1). You can do so, once pip has been successfully installed, using the terminal command
```
pip install wheel==0.37.1
```

* The final database is stored to a SQL database and requires mysql (v8.0.29) to be installed in your machine. You can use this [tutorial](https://www.digitalocean.com/community/tutorials/how-to-install-mysql-on-ubuntu-20-04) 
to install mysql and set up the database. After doing so, some additional mysql-related tools have to be installed using the terminal commands
```
sudo apt update
sudo apt install libmysqlclient-dev
```

* A database, user and password must be set up to run the imagenome.SqlDb and imagenome.Annotate classes. 


To install the *imagenome* package using pip, download/clone the repository, open a terminal on its root directory and execute the command

```
pip install .
```

Some of the dependencies will be installed by default in your ~/.local/bin directory. If the path to this directory is not included in your PATH environment variable, a warning message will be shown in your terminal during installation. If this is the case, once the installation of *imagenome* and its dependencies is complete, add this directory to your PATH using the terminal command
```
PATH=$PATH:~/.local/bin
```
You can make these changes permanent by adding the line above at the end of your ~/.bashrc file. The changes will be made effective once you open a new terminal.

## Getting started

There are two test scripts available in the *test/* directory illustrating all the steps in the process:
- main_models.py: downloading, parsing and saving the NLM MEDLINE/Pubmed baseline dataset and running the pre-trained TC. 
- main_annotate.py: saving the results obtained from the text classification step to an SQL table and running the pre-trained NER model to annotate it. This script requires the main_models.py script to have previously run successfully, as well as the previous setup of a mysql database with the following default values,
  - name: imagenome_db
  - host: localhost
  - user: root
  - password: password

These tests can be easily modified to process the entire dataset and to use different mysql database connection parameters, as well as to perform model training/testing using custom datasets. To run them, simply open a terminal on the repository root directory and execute the commands
```
cd test/
python3 main_models.py
python3 main_annotate.py
```

## Reference installation and test run times

The typical installation time of the *imagenome* package (following the instructions specified in this file) is ~10 minutes, where ~8 minutes correspond to the installation/setup of the specified pre-requisites (pip, mysql, ...) and ~2 minutes correspond to the installation of the package itself (and its dependencies).

Typical run times for the test scripts, obtained using an Intel(R) Core(TM) i9-10900 CPU @ 2.80GHz, are

- main_models.py: ~3 minutes
- main_annotate.py: ~10 seconds

Keep in mind that in these tests, only a small fraction of the NLM MEDLINE/Pubmed baseline dataset is downloaded, classified and annotated by the pipeline. The processing of the entire dataset might take up to days and ideally requires more computational resources than the ones provided by the average personal computer.

## Documentation
After having successfully installed the package and its dependencies (making sure that the PATH environment variable has been properly updated to include the necessary directories) its API documentation can be built in html format in the *doc/* directory by opening a terminal in the repository root directory and executing the commands

```
cd doc/
make html
```


## Data Use & License
All data used in this pipeline are obtained from the
NLM MEDLINE/Pubmed baseline dataset ("Courtesy of the U.S. National Library of Medicine",
https://www.nlm.nih.gov/databases/download/pubmed_medline.html) and were only used  for meta-analysis / systematic review purposes.

The training and testing datasets curated by the Imageable Genome team and used to generate the pre-trained TC and NER models included in the *imagenome* package are not publicly available at the moment due to copyright issues that need to be resolved. 

*imagenome* is copyright (C) 2023 of Pablo Jané and is distributed under the terms of the [Affero GNU General Public License (GPL) version 3](./LICENSE) or later.