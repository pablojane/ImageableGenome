import imagenome as ig

# README:
#################################################################################################################
# This script requires the previous installation of mysql and the deployment of a database named 'imagenome_db' #
# under user 'root' at 'localhost'. Check 'README.md' file for more detailed instructions on how to do this.    #
# This script also requires to have previously run the script 'test/main_models.py' successfully.               #
# Please, set the variable 'password' in this script to match the mysql 'root' user password.                   #
#################################################################################################################

# Script parameters
password = 'password'

# Instantiate database cursor for the deployed mysql database
db = ig.SqlDb(password, parquet_path='parquet', json_path='filtered', host='localhost', user='root',
              database='imagenome_db')

# Create 'imagenome' table in database and fill it with the filtered *.json files generated by the text classifier
db.create_table(name='imagenome')
db.fill_table(name='imagenome')

# Close all database connections
db.close()

# Instantiate database cursor for the deployed mysql database:
ann = ig.Annotate(password, input_model_path='../models/ner', query_table='imagenome')

# Create 'imagenome_ann' table in database and fill it with the annotated entities generated by the ner model.
ann.create_table(output_name='imagenome_ann')
ann.annotate(output_name='imagenome_ann')

# Close all database connections
ann.close()