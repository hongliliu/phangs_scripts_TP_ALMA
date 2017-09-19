#
# Parameters for individual sources for data reduction and imaging.
#-------------------------------------------------------------------

# Path for Analysis Utils
# You can download the ALMA Analysis Utils scripts from: ftp://ftp.cv.nrao.edu/pub/casaguides/analysis_scripts.tar
path_au    = "/users/softs/alma/jao-mirror/AIV/science"

#------------------------------
# Parameters for data reduction:
#------------------------------

# Pipeline reduced data (True or False)
pipeline   = True

# Additional plots, non-interactive (plots will be saved in "plots" folder)
doplots    = True   

#Number of EB files to be used (Thought to test fast some  
doEBs      = 0   # 0 to use all EBs

# Source name (as it is written in the data)
source     = 'NGC_4321'

# Order for the baseline fitting
bl_order   = 1

# Rest frequency of requested line in MHz (ex: "freq_rest  = 230538" for CO(2-1))
freq_rest  = 230538.  

# Range in velocity in km/s to extract the total line cube
vel_cube   = '1320~1830'

# Range in velocity in km/s to exclude the line emission from the baseline fit. You can add more than 1 line
# in the following format: 
# '-100~-50;20~30', where line emission is found between -100 and -50 km/s, and between 20 and 30 km/s. 
vel_line   = '1430~1730' 

#-----------------------------
# Parameters for imaging:
#-----------------------------

# Provide coordinate of phase center, otherwise set to "False" and coordinates will be read from the data
phase_center   = 'J2000 12h22m54.8s +15d49m19s'  # False

# Provide velocity of the source, otherwise set to "False" and coordinates will be read from the data
source_vel_kms = 1571 # False

# width in velocity and velocity resolution in km/s for final image
vwidth_kms     = 500
chan_dv_kms    = 2.5

# rest frequency in GHz
restfreq_ghz   = freq_rest/1e3

# Name of the line, to be used for naming the files
name_line  = 'CO21.v0p2'

# Factor to estimate the ALMA theoretical beam 
fwhmfactor = 1.13  

# Diameter of ALMA antennas in meters
diameter   = 12    


