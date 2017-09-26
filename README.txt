# phangs_scripts_TP_ALMA
Scripts for Total Power (TP) ALMA data reduction and imaging.

###########################################################################

Basics: How does it work?
-------------------------

The ALMA total power reduction executes the follwing steps:
  1: import_and_split_ant - Import data to MS and split by antenna    (adsm   -> asap)
  2: gen_tsys_and_flag    - Generate tsys cables and apply flags      (create .tsys and swpmap)
  3: counts2kelvin        - Calibration of Tsys and convert data to K (asap   -> asap.2)
  4: extract_cube         - Extract cube with line                    (asap.2 -> asap.3)
  5: baseline             - Baseline correction                       (asap.3 -> asap.4)
  6: concat_ants          - Concatenate all antennas                  (asap.4 -> ms.5 -> cal.jy)
  7: imaging              - Imaging and fix the header                (cal.jy -> image)
  8: export_fits          - Export image and weight to a fits file    (image  -> fits)


To do this, the sources are spread in three files:

  - analysis_scripts
    ALMA provided folder that contains useful tools to be used during the
    TP ALMA data reduction. You should not modify any of the scripts in
    this folder.

  - ALMA-TP-tools.py
    Script which contains the generic procedures for total power data
    reduction and imaging. You should not modify this script.

  - ALMA-TP-pipeline-GalaxyName.py
    Galaxy specific scripts that encode our own data reduction. This script
    uses the two previous code source.

###########################################################################

Additional information about the TP calibration process
-------------------------------------------------------

1. For some observations (galaxies: NGC 1087, NGC 1385, NGC 1300, NGC 1433,
   NGC 1566) there was an atmospheric line in the bandpass that could not
   be automatically reduced in CASA. In these cases, only a zero order
   baseline was subtracted. After executing all steps from 1 to 8, we went
   to GILDAS\CLASS to make a 2nd round of baseline subtraction
   piecewise. If required, the GILDAS\CLASS scripts can be shared.

2. The ALMA TP data can originally be reduced by JAO or any of the ARC
   nodes using scripts or by an automatized pipeline. Depending on who does
   the data reduction, our scripts should have slightly different behaviors
   to apply the flagging and to convert from Kelvin to Jansky per beam.

   FLAGGING: 

   - For all data, an apriori flagging is applied during step 1
     (import_and_split_ant, see above). This includes flags such as: mount
     off source, calibration device is not in correct position, power
     levels are not optimized, WCA not loaded.

   - In addition,o ther flags can be applied during step 2
     (gen_tsys_and_flag, see above) :

       + For data previously reduced with scripts, the ALMA data reducer
	 may have added additional flags that are stored in the
	 scriptForSDCalibration.py script in the "script" folder. You can
	 add additional flags here. They will be read by the
	 ALMA-TP-tools.py script.

       + For pipeline reduced data, no flag will be applied. If you whish
	 to add additional flags, you need to create a file describing the
	 flags to be done using the "sdflag" task under the name
	 "script/fileflag.py". For intance:
	     sdflag(infile = 'uid___A002_X9998b8_X5d5.ms.PM04.asap', 
		          mode = 'manual', 
		          spw = '19:0~119;3960~4079,21:0~500;3960~4079', 
		          overwrite = True)

   - Note: We'll work out a way so that once the data flagging is done at one
     place, it can automatically be forwarded to the three other places.

   JYPERK: 

   - For script reduced data, the information about the conversion from Kelvin
     to Jansky is stored in the scriptForSDCalibration.py scripts in the
     "script" folder.

   - For the pipeline reduced data, the same information is stored in a file
     called jyperk.csv in the calibration folder.

   - The ALMA-TP-tool.py script will check if the data was reduced by the 
     pipeline or not and will look for this information accordingly.

###########################################################################

What you have to do for galaxy NGC_1672
----------------------------------------

1. Getting scripts:

   - Download the zip file from the Github https://github.com/cnherrera/phangs_scripts_TP_ALMA/
     by clicking the Green bouton "Clone or download".
  

2. Getting the data

     - Donwload from the ALMA Science Archive Query (http://almascience.nrao.edu./aq/) the files under the 
       Member OUS of the TP observations for a given ALMA project (i.e  the product and the raw files). 
       Do NOT download the "semipass" files. 

     - Untar the "product" file (uid..._001_of_001.tar) and the uid....asdm.sdm files. They will be automatically 
       well placed in the standard ALMA directory tree:
  
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
			       ├── script        
			       ├── README        
              
      We will work on the calibration folder, which you can remove once the
      data reduction is finished.

      If you wish, you can read the ALMA README file for comments from the
      ALMA data reducer and for further description of the folders.

3. Running the scripts

     - Place the zip file you downloaded from the github in the script
       folder (see above) and unzip it.
     
     - Untar the analysis_script.tar file included in the zipped folder.
     
     - Modify the "ALMA-TP-pipeline-NGC_1672.py" if you wish to modify the parameters 
       used in the data reduction or imaging. State the step of the data reduction you 
       want to perform. 

     - In the "calibration" folder:
       CASA> execfile('../script/ALMA-TP-pipeline-NGC_1672.py')

       Note: We'll work to ensure that we can use the scripts without
       having to move them first.

     - Two additional folders will be created in the calibration folder: "plots" and "obs_lists"

       PLOTS folder: This folder contains all plots created by the data reduction scripts. For instance, 
       the Tsys and the baseline correction plots. Using such plots, you can judge the quality of the data.
       OBS_LISTS folder: This folder contains the observation lists of the data.

###########################################################################
