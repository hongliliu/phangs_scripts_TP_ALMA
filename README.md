# phangs_scripts_TP_ALMA
Scripts for Total Power (TP) ALMA data reduction and imaging.

# Contains:

- ALMA_TP_data_reduction.py:

  Script which contains the procedures for total power data reduction and imaging. Do not modify this script.
  
- parameters.py

  File that contains the individual parameters for each galaxy. Modify here the parameters such as
  coordinates, velocity range, etc.
  
- do_data_reduction.py

  Main script that calls the previous 2 scripts. State here the step of the data reduction that you want to perform.
  
# What do you need?   

To run the script, you need:

1.- Donwload from the ALMA Science Archive Query (http://almascience.nrao.edu./aq/) the files under the Member OUS of the TP observations for a given ALMA project (i.e  the product and the raw files). Do not download the "semipass" files. 
    
2.- Untar the "product" file (uid..._001_of_001.tar) jk
    
3.- Download the ALMA Analysis Utils scripts from: ftp://ftp.cv.nrao.edu/pub/casaguides/analysis_scripts.tar and add the path
    in the "path_au" variable in the parameters.py file.
    
4.- Check weather the data was originally reduced by ALMA with scripts or by the pipeline. Add this information in the
    "pipeline" variable in the pipeline.py file.


# How to use the scripts  

Place the 3 scripts in the script folder of you ALMA data.

In raw folder:

CASA> execfile('../script/do_data_reduction.py')


# Still to be done:

- debug when files are not found, etc.

