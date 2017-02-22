# Path for Analysis Utils
# You can download the ALMA Analysis Utils scripts from: ftp://ftp.cv.nrao.edu/pub/casaguides/analysis_scripts.tar
path_au    = "/users/softs/alma/jao-mirror/AIV/science"

# Pipeline reduced data?
pipeline   = False

# Additional plots, non-interactive
doplots    = True   

#Number of EB files to be used. Useful when we want to obtain a first look of the image.
doEBs      = 0   #0 to take all

# Source
source     = 'Source_name'

# Rest frequency of requested line in MHz
freq_rest  = 345795.9899    

# Range in velocity in km/s to extract the line cube
vel_cube   = '-800~800'

# Range in velocity in km/s to exclude the line emission from the baseline fit. You can add more than 1 line
# in the following format: '-100~-50;20~30', where line emission is found between -100 and -50 km/s, and between 20 and 30 km/s. 
vel_line   = '-800~-480:-300~600:760~800'

# Order for the baseline fitting
bl_order   = 1

# Name of the line, to be used for naming the files
name_line  = 'CO32_line'

# Factor to estimate the ALMA theoretical beam 
fwhmfactor = 1.13  

# Diameter of ALMA antennas in meters
diameter   = 12    


