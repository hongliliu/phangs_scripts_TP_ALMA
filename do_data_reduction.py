# To be run in RAW folder
# 
#-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-
path_script = '../script/'                                  # Path to the script folder

exec open(path_script+'parameters.py').read()               # Parameters for data reduction
execfile(path_script+'ALMA_TP_data_reduction.py')           # All procedures for data reduction


# Data reduction
do_step = [5,6]
# 1: import_and_split_ant - Import data to MS and split by antenna    (adsm -> asap)
# 2: gen_tsys_and_flag    - Generate tsys cables and apply flags      (create .tsys and swpmap)
# 3: counts2kelvin        - Calibration of Tsys and convert data to K (asap -> asap.2)
# 4: extract_cube         - Extract cube with line                    (asap.2 -> asap.3)
# 5: baseline             - Baseline correction                       (asap.3 -> asap.4)
# 6: concat_ants          - Concatenate all antennas                  (asap.4 -> ms.5 -> cal.jy)
# 7: imaging              - Imaging and fix the header                (cal.jy -> image)
# 8: export_fits          - Export image and weight to a fits file    (image -> fits)

# Defining EB names
EBsnames = [f for f in os.listdir(path_script) if f.endswith('.scriptForSDCalibration.py')]

for h in range(len(EBsnames)):
    
    filename = 'u'+re.search('u(.+?).script', EBsnames[h]).group(1)
    file_exists = check_exists(filename)
    if file_exists == True:
         
        vec_ants   = read_ants_names(filename)                       # Read vector with name of antennas
        vel_source = read_vel_source(filename,source)                # Read source velocity
        spws_info  = read_spw(filename,source)                       # Read information of spws (science and Tsys)
        
        if 1 in do_step: import_and_split_ant(filename,doplots)                      
        if 2 in do_step: spwmap = gen_tsys_and_flag(filename,spws_info,doplots,pipeline) 
        for ant in vec_ants: 
            if 3 in do_step: counts2kelvin(filename,ant,spwmap,spws_info,doplots)
            if 4 in do_step: extract_cube(filename,source,ant,freq_rest,vel_source,spws_info,vel_cube,doplots) 
            if 5 in do_step: baseline(filename,source,ant,freq_rest,vel_source,spws_info,vel_line,bl_order)   
        if 6 in do_step: concat_ants(filename,vec_ants,vel_source,freq_rest,spws_info,pipeline)                         
if 7 in do_step: imaging(source,name_line,diameter,fwhmfactor,doplots,doEBs=4)
if 8 in do_step: export_fits(name_line,source)

#Clean folder
os.system('rm -rf *.tsys')
