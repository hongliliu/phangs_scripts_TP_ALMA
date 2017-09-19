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
    
2.- Untar the "product" file (uid..._001_of_001.tar) and the uid....asdm.sdm files. They will be automatically well place in the ALMA directory.
    
3.- Download the ALMA Analysis Utils scripts from: ftp://ftp.cv.nrao.edu/pub/casaguides/analysis_scripts.tar and add the path
    in the "path_au" variable in the parameters.py file.
    
4.- Check weather the data was originally reduced by ALMA with scripts or by the pipeline (check the ALMA Readme). Add this information in the "pipeline" variable in the pipeline.py file.

# Directory tree

The directory tree is that of any ALMA project. After untaring your files (see point 2 above), you will have:
201X.1.00XXX.S
└── science_goal.uid___A001_XXX_XXXX
    └── group.uid___A001_XXX_XXXX
        └── member.uid___A001_XXXX_XXX
            ├── calibration
            ├── log
            ├── product
            ├── qa
            ├── raw
            ├── script        :script folder  
            ├── README        :This is the ALMA readme file. Read the comments from ALMA data reducer 



# How to use the scripts  

Place the 3 scripts in the script folder of you ALMA data.

In "calibration" folder:

CASA> execfile('../script/do_data_reduction.py')

# Additional information

The ALMA data can originally be reduced by JAO or any of the ARC nodes using scripts or by an automatized pipeline.
The script makes 2 differences for these 2 kind of observations:

FLAGGING: 

For all data, an apriori flagging is applied during step 1. This includes flags such as: mount off source, calibration device is not in correct position, power levels are not optimized, WCA not loaded. Other flags can be applied during step 2. 

For data previously reduced with scripts, probably the ALMA data reducer added additional flags that are stored in the scriptForSDCalibration.py scripts in the "script" folder (their step 6). You can add additional flags here. They will be read by the script.

For pipeline reduced data, no flag will be applied. If you whish to add additional flags, you need to create a file describing the flags to be done using the "sdflag" task under the name "script/file_flag_pipe.py". For intance:

sdflag(infile = 'uid___A002_X9998b8_X5d5.ms.PM04.asap', mode = 'manual', spw = '19:0~119;3960~4079,21:0~500;3960~4079', overwrite = True)

JYPERK: 

The conversion from Kelvin to Jansky is applied to the data. The conversion factor is given by ALMA in different forms for script and pipeline reduced data. For script reduced data, this information is stored in the scriptForSDCalibration.py scripts in the "script" folder. The pipeline reduced data, it will read a table, jyperk.csv, stored in the calibration folder.



# Still to be done:

- debug when files are not found, etc.

