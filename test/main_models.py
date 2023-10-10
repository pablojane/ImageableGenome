import os
import imagenome as ig

# README:
##################################################################################################################
# This script uses Text Classifier (TC) and Named Entity Recognition (NER) models which have been pre-trained    #
# by the Imageable Genome team and are included in the models/ folder of the ImageableGenome repository.         #
# However, the training processes for both models are illustrated in the commented code snippets of lines 26-35  #
# and 42-51. These snippets refer to hypothetical training and testing datasets. Format examples of such files   #
# are included in the data/examples/ directory of the repository solely for users' information, not for its use. #
##################################################################################################################

# Change working directory
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Instantiate Parser object
parser = ig.Parser()

# Download bibliographic raw text files from PUBMED ftp server
parser.download(ftp_list=['ftp://ftp.ncbi.nlm.nih.gov/pubmed/baseline/pubmed23n0001.xml.gz',
                          'ftp://ftp.ncbi.nlm.nih.gov/pubmed/baseline/pubmed23n0002.xml.gz'])

# Parse all the downloaded raw text files and store the result as *.parquet files
parser.parse('./ftp.ncbi.nlm.nih.gov/pubmed/baseline', 'parquet', max_workers=2)

# # Instantiate TextClassification object
# tc = ig.TextClassification()
#
# # Load train and test data for text classifier
# tc.load_train_data('../data/train_tc_data.json')
# tc.load_test_data('../data/test_tc_data.json')
#
# # Train text classifying model and save it to disk
# tc.train()
# tc.savemodel('../models/tc_custom')

# Instantiate filter using the stored text classifier and filter the parsed text *.parquet files (limited to 100
# positive entries per output *.json). For full filtering, leave max_lines as default
filter = ig.Filter('../models/tc')
filter.filter('parquet', output_path='filtered', max_workers=2, max_lines=100)

# # Instantiate Name Entity Recognition model (NER)
# ner = ig.Ner()
#
# # Load train and test data for NER
# ner.load_train_data('../data/train_ner_data.json')
# ner.load_test_data('../data/test_ner_data.json')
#
# # Train NER model and save it to disk
# ner.train()
# ner.savemodel('../models/ner_custom')
