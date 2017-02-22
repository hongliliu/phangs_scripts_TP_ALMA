#-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*
# ALMA Total Power Data Reduction Script
# Original calibration script modified by C. Herrera 12/01/2017
# 
# Last modifications 
# Add read_source_coordinates 31/01/2017
# More than 1 line can be defined to be excluded for baseline corrections 01/02/2017
# Handle TOPO ALMA frame vs the given LSRK velocity for extraction of cube and baseline 02/02/2017 
#
# Still need to do
# - Different erros when files are not found, etc.
#
#-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*

# Import libraries
import os              # operating system
import re              # regular expression
import numpy as np     # Support for large, multi-dimensional arrays and matrices
import sys             # System-specific parameters and functions
import scipy.constants # Physical constants

if os.path.isdir("plots/") == False:     os.system('mkdir plots')       # folder containing all plots
if os.path.isdir("obs_lists/") == False: os.system('mkdir obs_lists')   # folder containing all observation lists (i.e., listobs, sdlist)

# Global variables
c_light = scipy.constants.c/1000   # Speed of light in km/s 
pi      = scipy.constants.pi


# Import ALMA Analysis Utils
print "You can download the ALMA Analysis Utils scripts from: ftp://ftp.cv.nrao.edu/pub/casaguides/analysis_scripts.tar"
sys.path.append(path_au+'/analysis_scripts')
import analysisUtils as aU
es = aU.stuffForScienceDataReduction()
print "Specific tasks for ALMA data reduction are loaded"

# Creating CASA tools
def createCasaTool(mytool):
    
    if (type(casac.Quantity) != type):  # casa 4.x
        myt = mytool()
    else:  # casa 3.x
        myt = mytool.create()
    return(myt)

# Retrieve name of the column
def getDataColumnName(inputms):
    
    mytb = createCasaTool(tbtool)
    mytb.open(inputms)
    colnames = mytb.colnames()
    if 'FLOAT_DATA' in colnames:
        data_query= 'FLOAT_DATA'
    else:
        data_query = 'DATA'
    mytb.close()
    return(data_query)

# by ALMA
def scaleAutocorr(vis, scale=1., antenna='', spw='', field='', scan=''):
    
    if os.path.exists(vis) == False:
        print "Could not find MS."
        return
    if os.path.exists(vis+'/table.dat') == False:
        print "No table.dat. This does not appear to be an MS."
        return
    
    mymsmd = createCasaTool(msmdtool)
    mytb = createCasaTool(tbtool)
    
    conditions = ["ANTENNA1==ANTENNA2"]
    
    mymsmd.open(vis)
    
    if antenna != '':
        if not isinstance(antenna, (list, tuple)):
            antenna = [antenna]
        antennaids = []
        for i in antenna:
            if re.match("^[0-9]+$", str(i)): # digits only: antenna ID
                antennaids.append(int(i))
            else: # otherwise: antenna name
                antennaids.append(mymsmd.antennaids(i)[0])
        conditions.append("ANTENNA1 in %s" % str(antennaids))
    if spw != '':
        if not isinstance(spw, (list, tuple)): 
            spw = [spw]
        datadescids = []
        for i in spw:
            datadescids.append(mymsmd.datadescids(spw=int(i))[0])
        conditions.append("DATA_DESC_ID in %s" % str(datadescids))
    if field != '':
        if not isinstance(field, (list, tuple)):
            field = [field]
        fieldids = []
        for i in field:
            if re.match("^[0-9]+$", str(i)): # digits only: field ID
                fieldids.append(int(i))
            else: # otherwise: field name
                fieldids.append(mymsmd.fieldsforname(i)[0])
        conditions.append("FIELD_ID in %s" % str(fieldids))
    if scan != '':
        if not isinstance(scan, (list, tuple)):
            scan = [scan]
        scannumbers = [int(i) for i in scan]
        conditions.append("SCAN_NUMBER in %s" % str(scannumbers))
    
    mymsmd.close()
    
    datacolumn = getDataColumnName(vis)
    
    print "Multiplying %s to the dataset %s column %s." % \
        (str(scale), vis, datacolumn)
    print "The selection criteria are '%s'." % (" && ".join(conditions))
    
    mytb.open(vis, nomodify=False)
    subtb = mytb.query(" && ".join(conditions))
    try:
        data = subtb.getcol(datacolumn)
        print "Dimension of the selected data: %s" % str(data.shape)
        subtb.putcol(datacolumn, data*scale)
    except:
        print "An error occurred upon reading/writing the data."
    finally:
        print "Closing the table."
        mytb.flush()
        subtb.close()
        mytb.close()

# Create vector with antenna names
def read_ants_names(filename):
    
    mytb = createCasaTool(tbtool)
    mytb.open(filename + '/ANTENNA')
    vec_ants = mytb.getcol('NAME')
    mytb.close()
    
    return vec_ants

# Correct the Tsysmap
def get_tsysmap(tsysmap,spws_scie,spws_tsys,freq_rep_scie,freq_rep_tsys):
    
    for i in range(len(freq_rep_scie)): 
        diff = [abs(freq_rep_tsys[j] - freq_rep_scie[i]) for j in range(len(freq_rep_tsys))]
        ddif = np.array(diff)
        tsysmap[spws_scie[i]]   = spws_tsys[ddif.argmin()]
        tsysmap[spws_scie[i]+1] = spws_tsys[i]
    print "Final map used for the observations: (they should have the same frequency)"
    for i in range(len(spws_scie)): print spws_scie[i],tsysmap[spws_scie[i]]
    return tsysmap

# Read spw information
def read_spw(filename,source):
    
    # Tsys spws (index)
    mytb = createCasaTool(tbtool)
    mytb.open(filename + '/SYSCAL')
    
    spwstsys  = mytb.getcol('SPECTRAL_WINDOW_ID')
    spws_tsys = np.unique(spwstsys).tolist()
    mytb.close()
    
    # Science spws (index)
    mytb.open(filename + '/SOURCE') 
    names  = mytb.getcol('NAME')
    numli  = mytb.getcol('NUM_LINES')
    ss     = np.where((names == source) & (numli ==  1))
    spws_scie      = [int(mytb.getcol('SPECTRAL_WINDOW_ID',startrow=i,nrow=1))    for i in ss[0]]
    rest_freq_scie = [float(mytb.getcol('REST_FREQUENCY',startrow=i,nrow=1)) for i in ss[0]]
    mytb.close()
    mytb.open(filename + '/SPECTRAL_WINDOW')
    names          = mytb.getcol('NAME')
    rest_freq_scie = [rest_freq_scie[i] for i in range(len(spws_scie)) if "FULL_RES" in names[spws_scie[i]]]
    spws_scie      = [spw for spw in spws_scie if "FULL_RES" in names[spw]]
    
    # Read number of channels, frequency at channel zero and compute representative frequency
    freq_zero_scie  = range(len(spws_scie))
    chan_width_scie = range(len(spws_scie))
    num_chan_scie   = range(len(spws_scie))
    freq_rep_scie   = range(len(spws_scie))
    for i in range(len(spws_scie)):
        freq_zero_scie[i]  = float(mytb.getcol('REF_FREQUENCY',startrow=spws_scie[i],nrow=1))
        chan_width_scie[i] = float(mytb.getcol('CHAN_WIDTH',startrow=spws_scie[i],nrow=1)[0])
        num_chan_scie[i]   = float(mytb.getcol('NUM_CHAN',startrow=spws_scie[i],nrow=1))
        freq_rep_scie[i]   = (num_chan_scie[i]/2*chan_width_scie[i]+freq_zero_scie[i])/1e6
    freq_zero_tsys  = range(len(spws_tsys))
    chan_width_tsys = range(len(spws_tsys))
    num_chan_tsys   = range(len(spws_tsys))
    freq_rep_tsys   = range(len(spws_tsys))
    for i in range(len(spws_tsys)):
        freq_zero_tsys[i]  = float(mytb.getcol('REF_FREQUENCY',startrow=spws_tsys[i],nrow=1))
        chan_width_tsys[i] = float(mytb.getcol('CHAN_WIDTH',startrow=spws_tsys[i],nrow=1)[0])
        num_chan_tsys[i]   = float(mytb.getcol('NUM_CHAN',startrow=spws_tsys[i],nrow=1))
        freq_rep_tsys[i]   =  (num_chan_tsys[i]/2*chan_width_tsys[i]+freq_zero_tsys[i])/1e6
    mytb.close()
    
    return spws_scie,spws_tsys,freq_rep_scie,freq_rep_tsys,chan_width_scie,num_chan_scie

# Get information of the source velocity
def read_vel_source(filename,source):
    
    mytb  = createCasaTool(tbtool)
    mytb.open(filename + '/SOURCE')
    names = mytb.getcol('NAME')
    numli = mytb.getcol('NUM_LINES')
    ss    = np.where((names == source) & (numli ==  1))[0]
    vel_source = float(mytb.getcol('SYSVEL',startrow=ss[0],nrow=1))/1e3
    vel_frame = mytb.getcolkeywords('SYSVEL')['MEASINFO']['Ref']
    print "Frame of source velocity  is: "+vel_frame
    mytb.close()
    
    return vel_source

# SPW where the requested line is located
def get_spw_line(vel_source,freq_rest,spws_info):
    
    #science spws
    spws_scie,spws_tsys,freq_rep_scie,freq_rep_tsys,chan_width_scie,num_chan_scie  = spws_info
    
    found = False
    for i in range(len(spws_scie)):
        freq_ini = (freq_rep_scie[i]-num_chan_scie[i]/2*chan_width_scie[i]*1e-6)/(1-vel_source/c_light)  # initial frequency in spw -> still to be check since observations are in TOPO
        freq_fin = (freq_rep_scie[i]+num_chan_scie[i]/2*chan_width_scie[i]*1e-6)/(1-vel_source/c_light)  # final frequency in spw -> still to be check since observations are in TOPO
        if freq_rest > min(freq_ini,freq_fin) and freq_rest < max(freq_ini,freq_fin): 
            found = True
            return spws_scie[i]
    if found == False: 
        print "** Requested line with rest frequency "+str(freq_rest/1e3)+" GHz is not on the data **"
        return False

# Extract flagging from original data reduction file
def extract_flagging(filename,pipeline):

    os.system('rm ../script/file_flags.py')
    file_flag = open('../script/file_flags.py', 'w')
 
    if pipeline == True: 
        print "No file with flagging because pipeline data reduction."
    else:  
        file_script = '../script/'+filename+'.scriptForSDCalibration.py'  
        with open(file_script) as f: lines_f = f.readlines()
        with open(file_script) as f:
            for i, line in enumerate(f):
                ll = i
                if "sdflag(infile" in line: 
                    ss = line.index("sdflag(i")
                    while len(lines_f[ll].split()) != 0: 
                        file_flag.write((lines_f[ll])[ss:len(lines_f[ll])]) 
                        ll = ll+1
        print "Flags saved in script/file_flags.py"
    file_flag.close()

# Convert the given velocity to channels (using MS file)
def convert_vel2chan(filename,freq_rest,vel_cube,spw_line,vel_source,spws_info,coords):
    
    spws_scie,freq_rep_scie,chan_width_scie,num_chan_scie = spws_info[0],spws_info[2],spws_info[4],spws_info[5]
    freq_rep_line   = freq_rep_scie[np.where(np.array(spws_scie)    == spw_line)[0]]
    chan_width_line = (chan_width_scie[np.where(np.array(spws_scie) == spw_line)[0]])/1e6
    num_chan_line   = num_chan_scie[np.where(np.array(spws_scie)    == spw_line)[0]]
    
    vel1 = float((vel_cube.split('~'))[0])
    vel2 = float((vel_cube.split('~'))[1])
    freq1 = (1-vel1/c_light)*freq_rest
    freq2 = (1-vel2/c_light)*freq_rest
    
    ra  = coords.split()[1]
    ra  = ra.replace("h",":")
    ra  = ra.replace("m",":")
    dec = coords.split()[2]
    dec = dec.replace("d",":")
    dec = dec.replace("m",":")

    date = aU.getObservationStartDate(filename)
    date = (date.split()[0]).replace('-','/')+'/'+date.split()[1]
    
    freq1_topo = aU.lsrkToTopo(freq1,date,ra,dec)
    freq2_topo = aU.lsrkToTopo(freq2,date,ra,dec)
    
    freq_chan0  = freq_rep_line-(num_chan_line/2-0.5)*chan_width_line
    
    chan1 = int(round((freq1_topo-freq_chan0)/chan_width_line))
    chan2 = int(round((freq2_topo-freq_chan0)/chan_width_line))
    
    return min(chan1,chan2),max(chan1,chan2) 

# Convert the given velocity to channels (using ASAP file)
def convert_vel2chan_line(filename_in,freq_rest,vel_line,spw_line,coords,date):
   
    vel1 = float((vel_line.split('~'))[0])
    vel2 = float((vel_line.split('~'))[1])
    
    freq1 = (1-vel1/c_light)*freq_rest
    freq2 = (1-vel2/c_light)*freq_rest
    
    ra  = coords.split()[1]
    ra  = ra.replace("h",":")
    ra  = ra.replace("m",":")
    dec = coords.split()[2]
    dec = dec.replace("d",":")
    dec = dec.replace("m",":")
    
    freq1_topo = aU.lsrkToTopo(freq1, date,ra,dec)
    freq2_topo = aU.lsrkToTopo(freq2, date,ra,dec)

    mytb  = createCasaTool(tbtool)
    mytb.open(filename_in)
    nchan = mytb.getkeyword('nChan')
    mytb.close()
    
    mytb.open(filename_in+'/FREQUENCIES')   
    freq_chan0 = mytb.getcol('REFVAL',startrow=spw_line,nrow=1)/1e6
    chan_width = mytb.getcol('INCREMENT',startrow=spw_line,nrow=1)/1e6
    mytb.close()
    
    chan1 = int(round((freq1_topo-freq_chan0)/chan_width))
    chan2 = int(round((freq2_topo-freq_chan0)/chan_width))
    
    return min(chan1,chan2),max(chan1,chan2),nchan

def str_spw4baseline(filename_in,freq_rest,vel_line,spw_line,coords):
    
    filename = re.search('(.+?).ms',filename_in).group(0)
    
    date = aU.getObservationStartDate(filename)
    date = (date.split()[0]).replace('-','/')+'/'+date.split()[1]
    vel_line_s = vel_line.split(':')
    nlines = len(vel_line_s)
    spw_extr = str(spw_line)+":0~"
    for i in range(nlines):
        vel_str = vel_line_s[i]
        chan1_line,chan2_line,nchan_line = convert_vel2chan_line(filename_in,freq_rest,vel_str,spw_line,coords,date)
        
        # String to define spws for baseline correction
        spw_extr = spw_extr+str(chan1_line)+";"+str(chan2_line)+"~"
    spw_extr = spw_extr+str(nchan_line)
    
    return spw_extr

# Extract variable jyperk, used to convert from K to Jy.
def extract_jyperk(filename,pipeline):
    
    os.system('rm ../script/file_jyperk.py')
    file_jyperk = open('../script/file_jyperk.py', 'w')
    
    if pipeline == True: 
        file_script = '../calibration/jyperk.csv'
        ant_arr = []
        spw_arr = []
        val_arr = []
        with open(file_script) as f: 
            for line in f:
                if filename in line:
                    line_arr = line.split(',')
                    ant_arr.append(line_arr[1])
                    spw_arr.append(int(line_arr[2]))
                    val_arr.append(line_arr[4][0:line_arr[4].index('\n')])       
        jyperk = {k: {e:{'mean':{}} for e in np.unique(spw_arr)} for k in np.unique(ant_arr)}
        for i in range(12): jyperk[ant_arr[i]][spw_arr[i]]['mean']= float(val_arr[i])
    else:  
        file_script = '../script/'+filename+'.scriptForSDCalibration.py'   
        with open(file_script) as f: lines_f = f.readlines()
        with open(file_script) as f:
            for i, line in enumerate(f):
                ll = i
                if "jyperk = " in line: 
                    ss = line.index("jyperk")
                    while len(lines_f[ll].split()) != 0: 
                        if ll == i+1: ss2 = lines_f[ll].index("{")
                        if ll == i: 
                            file_jyperk.write((lines_f[ll])[ss:len(lines_f[ll])]) 
                        else:
                            file_jyperk.write((lines_f[ll])[ss2:len(lines_f[ll])])
                            ll = ll+1
            file_jyperk.close()
    
    if os.path.exists('../script/file_jyperk.py'): execfile('../script/file_jyperk.py') #exec open('../script/file_jyperk.py').read()
    return jyperk

def read_source_coordinates(filename,source):
    
    source = get_sourcename(filename)
    mytb   = createCasaTool(tbtool)
    mytb.open(filename + '/FIELD')
    names  = mytb.getcol('NAME')
    dir_RA = (mytb.getcol('REFERENCE_DIR')[0])[0]
    dir_DE = (mytb.getcol('REFERENCE_DIR')[1])[0]
    mytb.close()
    
    ss    = np.where(names == source)
    RA    = (np.degrees(dir_RA[ss])[0]+360)/15
    DEC   = np.degrees(dir_DE[ss])[0]
    RA_h  = int(RA)
    RA_m  = int(60*(RA-RA_h))
    RA_s  = 60*(60*(RA-RA_h)-RA_m)
    DEC_x = int(np.sign(DEC))
    DEC   = abs(DEC)
    DEC_d = int(DEC)*DEC_x
    DEC_m = int(60*(DEC-int(DEC)))
    DEC_s = 60*(60*(DEC-int(DEC))-DEC_m)
    coord = "J2000  "+str(RA_h)+"h"+str(RA_m)+"m"+str(RA_s)+" "+str(DEC_d)+"d"+str(DEC_m)+"m"+str(DEC_s)
    return coord

def get_sourcename(filename):
    
    mytb   = createCasaTool(msmdtool)
    mytb.open(filename)
    source = mytb.fieldnames()[mytb.fieldsforintent('OBSERVE_TARGET#ON_SOURCE')[0]]
    mytb.close()
    
    return source

def str_spw_apply_tsys(spws_info):
    #science spws
    spws_scie,spws_tsys,freq_rep_scie,freq_rep_tsys = spws_info[0:4]
    
    spws_all = spws_tsys+spws_scie
    spws_all.sort()
    spws_tsys_str = (str(spws_tsys))[1:len(str(spws_tsys))-1]
    spws_scie_str = (str(spws_scie))[1:len(str(spws_scie))-1]
    spws_all_str  = (str(spws_all))[1:len(str(spws_all))-1]
    
    return spws_scie_str,spws_tsys_str,spws_all_str

#-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*
# Data reduction steps
#-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*
#
# Step 0
#*-*-*-*-*-*
def check_exists(filename):
    print "Checking that the original ALMA data exists"
    filename_asdm = filename[0:filename.find('.ms')]+'.asdm.sdm'
    
    if os.path.exists(filename_asdm) == True:
        print "** Original ALMA data exists. **"
        return True
    else:
        print "** Original ALMA data does not exist. **"
        return False

#*-*-*-*-*-*_*-*-*-*-*-*
# Step 1  Import data 
#*-*-*-*-*-*-*-*-*-*-*
def import_and_split_ant(filename,doplots=False):
    
    print "=================================================="
    print "= Step 1 - Import ASDM data and split by antenna ="
    print "=================================================="
    
    filename0 = filename[0:filename.find('.ms')]
    os.system('cp -r '+filename0+'.asdm.sdm '+filename0)
    
    # 1.1 Import of the ASDM
    print "1.1 Importing from ASDM to MS"
    if os.path.exists(filename) == False:
        importasdm(filename0, 
            asis='Antenna Station Receiver Source CalAtmosphere CalWVR CorrelatorMode SBSummary', 
            bdfflags=False, 
            process_caldevice=False, 
            with_pointing_correction=True)
    
    # Transfer specific flags (BDF flags) from the ADSM to the MS file
    os.system(os.environ['CASAPATH'].split()[0]+'/bin/bdflags2MS -f "COR DELA INT MIS SIG SYN TFB WVR ZER" '+filename0+' '+filename)
    
    # Check for known issue, CSV-2555: Inconsistency in FIELD_ID, SOURCE_ID and Spw_ID in single dish data
    es.fixForCSV2555(filename)   
    
    # 1.2 Listobs
    print "1.2 Creating listobs for MS file"
    outname = filename+'.listobs'
    os.system('rm -rf obs_lists/'+outname)
    listobs(vis = filename,
        listfile = 'obs_lists/'+outname)
    
    if doplots == True: 
        aU.getTPSampling(vis = filename, 
        showplot = True, 
        plotfile = 'plots/'+filename+'.sampling.png')
    
    # 1.3 A priori flagging: e.g., mount is off source, calibration device is not in correct position, power levels are not optimized, WCA not loaded...
    print "1.3 Applying a priori flagging, check "+filename+".flagcmd.png plot to see these flags."
    flagcmd(vis = filename,
        inpmode = 'table',
        useapplied = True,
        action = 'plot',
        plotfile = 'plots/'+filename+'.flagcmd.png')
    
    flagcmd(vis = filename,
        inpmode = 'table',
        useapplied = True,
        action = 'apply')
    
    # 1.4 Split by antenna 
    fin = '.asap'

    vec_ants   = read_ants_names(filename)
    for ant in vec_ants :
        os.system('rm -Rf '+filename+'.'+ant+fin)
    
    sdsave(infile = filename, 
        splitant = True, 
        outfile = filename+fin, 
        overwrite = True)
    
    #1.5 sdlist
    for ant in vec_ants:
        os.system('rm -Rf obs_lists/'+filename+'.'+ant+'.asap.sdlist')
        sdlist(infile = filename+'.'+ant+'.asap',
            outfile = 'obs_lists/'+filename+'.'+ant+'.asap.sdlist')

#-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*
# Step 2  Generate Tsys and apply flagging 
#-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*

def gen_tsys_and_flag(filename,spws_info,pipeline,doplots=False):
    
    print "========================================================"
    print " Step 2  Generate Tsys and apply flagging"
    print "========================================================"
    
    # 2.1 Generation of the Tsys cal table
    print " 2.1 Generating Tsys calibration table"
    
    os.system('rm -Rf '+filename+'.tsys')
    gencal(vis = filename, caltable = filename+'.tsys', caltype = 'tsys')
    
    # 2.2 Create png plots of CASA Tsys and bandpass solution
    if doplots == True:
        os.system('rm -Rf plots/'+filename+'.tsys.plots.overlayTime/'+filename+'.tsys')
        plotbandpass(caltable=filename+'.tsys', 
                     overlay='time',
                     xaxis='freq', yaxis='amp', 
                     subplot=22, 
                     buildpdf=False, 
                     interactive=False,
                     showatm=True,
                     pwv='auto',
                     chanrange='92.1875%',
                     showfdm=True,
                     field='', 
                     figfile='plots/'+filename+'.tsys.plots.overlayTime/'+filename+'.tsys')
        
        # Create png plots for Tsys per source with antennas
        es.checkCalTable(filename+'.tsys', msName=filename, interactive=False)
        os.system('mv '+filename+'.tsys.plots  plots/.') 
    
    # 2.3 Do initial flagging 
    print "2.3 Initial flagging, reading flags in file file_flags.py. You can modify this file to add more flags"    
    extract_flagging(filename,pipeline)    # Extract flags from original ALMA calibration script (sdflag entries)
    if os.path.exists('../script/file_flags.py'): execfile('../script/file_flags.py')
    
    
    # 2.4 Create Tsys map 
    print "2.4 Creating Tsysmaps" 
    # Read spws and frquencies for science and tsys
    spws_scie,spws_tsys,freq_rep_scie,freq_rep_tsys = spws_info[0:4]
    
    from recipes.almahelpers import tsysspwmap
    tsysmap = tsysspwmap(vis = filename, tsystable = filename+'.tsys', trim = False)
    
    print "Spectral windows for science are: ",spws_scie,freq_rep_scie
    print "Spectral windows for tsys are   : ",spws_tsys,freq_rep_tsys
    print "Original map between science and tsys spws: (they should have the same frequency)"
    for i in range(len(spws_scie)): print spws_scie[i],tsysmap[spws_scie[i]]
    
    tsysmap = get_tsysmap(tsysmap,spws_scie,spws_tsys,freq_rep_scie,freq_rep_tsys)
    
    spwmap = {}
    for i in spws_scie:
        if not tsysmap[i] in spwmap.keys():
            spwmap[tsysmap[i]] = []
        spwmap[tsysmap[i]].append(i)  
    
    return spwmap

#-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*
# Step 3  From counts to Kelvin
#-*-*-*-*-*-*-*-*-*-*
def counts2kelvin(filename,ant,spwmap,spws_info,doplots=False):
    
    print "=================================="
    print "= Step 3 - From counts to Kelvin ="
    print "=================================="
    
    # Get string with needed spws to apply Tsys
    spws_scie_str,spws_tsys_str,spws_all_str = str_spw_apply_tsys(spws_info)
        
    print "3.1 Converting data into Kelvin Ta* = Tsys * (ON-OFF)/OFF"
    fin    = '.asap'  
    finout = '.asap.2'
    
    filename_in  = filename+'.'+ant+fin
    filename_out = filename+'.'+ant+finout
    
    os.system('rm -Rf '+filename_out)
    sdcal2(infile = filename_in,
            calmode = 'ps,tsys,apply',
            spw = spws_all_str,
            tsysspw = spws_tsys_str,
            spwmap = spwmap,
            outfile = filename_out,
            overwrite = True)
    
    os.system('mv '+filename_out+'  plots/.')
    if doplots == True: es.SDcheckSpectra(filename_out, spwIds=spws_scie_str, interactive=False)
    
    print "3.2 Applying non-linearity correction factor"  
    
    sdscale(infile = filename_out,
            outfile = filename_out,
            factor = 1.25,
            overwrite=True)


#-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*
# Step 4  Extract the cube including the line
#-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*
def extract_cube(filename,source,ant,freq_rest,vel_source,spws_info,vel_cube,doplots=False):
    
    print "========================================================="
    print "= Step 4 - Extracting cube including the requested line ="
    print "========================================================="
    
    # Defining extensions
    fin    = '.asap.2'
    finout = '.asap.3'
    
    filename_in  = filename+'.'+ant+fin
    filename_out = filename+'.'+ant+finout
    
    #Plotting the line
    if doplots == True: 
        print "4.1 Plotting each IF for each antenna"
        sdplot(infile=filename+'.'+ant+fin,plottype='spectra', specunit='channel', timeaverage=True,stack='p')
    
    # Get the spw where the requested line is located
    spw_line = get_spw_line(vel_source,freq_rest,spws_info)
    
    print "Velocity of the source: ",vel_source," km/s. The line emission is in the SPW ",spw_line
    
    # Get the string of the channels to be extracted from the original cube
    coords = read_source_coordinates(filename,source)
    chan1_cube,chan2_cube = convert_vel2chan(filename,freq_rest,vel_cube,spw_line,vel_source,spws_info,coords)
    spw_extr = str(spw_line)+":"+str(chan1_cube)+"~"+str(chan2_cube)
    
    print "4.2 Extracting a cube with the line"
    
    os.system('rm -Rf '+filename_out)
    sdsave(infile=filename_in,
           field=source,
           spw=spw_extr,
           outfile=filename_out)
    
    os.system('rm -Rf obs_list/'+filename_out+'.list')
    sdlist(infile=filename_out,
           outfile='obs_list/'+filename_out+'.list') 
    
    if doplots == True: 
        print "4.3 Plotting the line averaged in time"    
        sdplot(infile=filename_out,
               plottype='spectra', 
               specunit='km/s', 
               restfreq=str(freq_rest)+'MHz',
               timeaverage=True, 
               stack='p',
               polaverage=True)


#-*-*-*-*-*-*-*-*-*-*-*-*-*-*
# Step 5 Baseline correction
#-*-*-*-*-*-*-*-*-*-*
def baseline(filename,source,ant,freq_rest,vel_source,spws_info,vel_line,bl_order):
    print "================================"
    print "= Step 5 - Baseline correction ="
    print "================================"
    
    # Definition of extension
    fin    = '.asap.3'
    finout = '.asap.4'
    
    filename_in  = filename+'.'+ant+fin
    filename_out = filename+'.'+ant+finout
    
    # Extract the ID of the spw where the line is
    spw_line = get_spw_line(vel_source,freq_rest,spws_info)
    
    # Convert the velocity range in channels and get spw string for baseline fitting
    coords   = read_source_coordinates(filename,source)
    spw_extr = str_spw4baseline(filename_in,freq_rest,vel_line,spw_line,coords)
    
    # Subtracting the baseline
    os.system('rm -Rf '+filename_out)
    sdbaseline(infile = filename_in,
           spw = spw_extr,
           maskmode = 'list',
           blfunc = 'poly',
           order = bl_order,
           outfile = filename_out,
           overwrite = True)  
    
    if doplots == True:
        # PLotting the result from the baseline correction. Spectra avergarfed in time    
        sdplot(infile=filename_out,
               plottype='spectra', 
               specunit='km/s', 
               restfreq=str(freq_rest)+'MHz', 
               timeaverage=True, 
               stack='p',
               polaverage=True)

    os.system('mv  *blparam.txt  obs_lists/')

#-*-*-*-*-*-*-*-*-*-*-*-*-*-*
# Step 6 Concatenate antennas
#-*-*-*-*-*-*-*-*-*-*
def concat_ants(filename,vec_ants,vel_source,freq_rest,spws_info,pipeline):
    
    print "========================================================"
    print "= Step 6 - Concatenate antennas and K to Jy conversion ="
    print "========================================================"
    
    # Defining extensions
    fin    = '.asap.4'
    finout = '.ms.5'
    
    # Extract the ID of the spw where the line is
    spw_line = get_spw_line(vel_source,freq_rest,spws_info)
    
    # Converting from ASAP to MS
    print "6.1 Converting from ASAP to MS"
    for ant in vec_ants :
        os.system('rm -Rf '+filename+'.'+ant+finout)
        sdsave(infile = filename+'.'+ant+fin,
            outfile = filename+'.'+ant+finout,
            outform='MS2')
    
    # Concatenation
    print "6.2 Concatenating antennas"
    lis_fils = [filename+'.'+vec_ants[i]+finout for i in range(len(vec_ants))]
    os.system('rm -Rf '+filename+'.cal')
    concat(vis = lis_fils,concatvis = filename+'.cal')
    
    # Convert the Science Target Units from Kelvin to Jansky   
    print " 5.3 Convert the Science Target Units from Kelvin to Jansky"
    jyperk = extract_jyperk(filename,pipeline)
    
    os.system('rm -Rf '+filename+'.cal.jy')
    os.system('cp -Rf '+filename+'.cal '+filename+'.cal.jy')
    
    for ant in jyperk.keys():
        scaleAutocorr(vis=filename+'.cal.jy', scale=jyperk[ant][spw_line]['mean'], antenna=ant, spw=spw_line)
    
    # Rename line spw to spw=0
    print "6.3 Renaming spw of line, "+str(spw_line)+" to 0"
    fin = '.cal.jy'
    finout = '.cal.jy.tmp'
    
    split(vis=filename+fin,
         outputvis=filename+finout,
         datacolumn='all')
    
    os.system('rm -Rf '+filename+fin)
    os.system('mv '+filename+finout+' '+filename+fin)

#-*-*-*-*-*-*-*-*-*-*-*-*-*-*
# Step 7 - Imaging
#-*-*-*-*-*-*-*-*-*-*
def imaging(source,name_line,diameter,fwhmfactor,doplots=False,doEBs=0):
    
    print "===================="
    print "= Step 7 - Imaging ="
    print "===================="
    
    # Search for files already calibrated
    path = '.'
    Msnames = [f for f in os.listdir(path) if f.endswith('.cal.jy')]
    
    #Check how many EBs you want to use
    if doEBs !=0 : Msnames = Msnames[0:doEBs]

    #Coordinate of phasecenter 
    coord_phase = read_source_coordinates(Msnames[0],source)

    # Definition of parameters for imaging
    xSampling,ySampling,maxsize = aU.getTPSampling(Msnames[0],showplot=False)
    
    msmd.open(Msnames[0])
    freq = msmd.meanfreq(0)
    msmd.close()
    
    theorybeam = fwhmfactor*c_light*1e3/freq/diameter*180/pi*3600
    cell       = theorybeam/9.0
    imsize     = int(round(maxsize/cell)*1.3)   #int(round(maxsize/cell)*2) - smaller image than the one given by ALMA
    
    os.system('rm -Rf ALMA_TP.'+source+'.'+name_line+'.image')
    
    print "Start imaging"
    sdimaging(infiles = Msnames,
        mode = 'channel',
        outframe = 'LSRK',
        gridfunction = 'SF',
        convsupport = 6,
        phasecenter = coord_phase,
        imsize = imsize,
        cell = str(cell)+'arcsec',
        overwrite = True,
        outfile = 'ALMA_TP.'+source+'.'+name_line+'.image')
    
    # Correct the brightness unit in the image header  
    imhead(imagename = 'ALMA_TP.'+source+'.'+name_line+'.image',
        mode = 'put',
        hdkey = 'bunit',
        hdvalue = 'Jy/beam')
    
    # Add Restoring Beam Header Information to the Science Image    
    minor, major, fwhmsfBeam, sfbeam = aU.sfBeam(frequency=freq*1e-9,
        pixelsize=cell,
        convsupport=6,
        img=None, #to use Gaussian theorybeam
        stokes='both',
        xSamplingArcsec=xSampling,
        ySamplingArcsec=ySampling,
        fwhmfactor=fwhmfactor,
        diameter=diameter)
    
    ia.open('ALMA_TP.'+source+'.'+name_line+'.image')
    ia.setrestoringbeam(major = str(sfbeam)+'arcsec', minor = str(sfbeam)+'arcsec', pa = '0deg')
    ia.done()
    
    if doplots == True: viewer('ALMA_TP.'+source+'.'+name_line+'.image')

#-*-*-*-*-*-*-*-*-*-*-*-*-*-*
# Step 8 - Export fits file
#-*-*-*-*-*-*-*-*-*-*
def export_fits(name_line,source):    
    
    # Export to fits file
    os.system('rm -Rf ALMA_TP.'+source+'.'+name_line+'.image.fits')
    os.system('rm -Rf ALMA_TP.'+source+'.'+name_line+'.image.weight.fits')
    exportfits(imagename = 'ALMA_TP.'+source+'.'+name_line+'.image', 
               fitsimage = 'ALMA_TP.'+source+'.'+name_line+'.image.fits')
    exportfits(imagename = 'ALMA_TP.'+source+'.'+name_line+'.image.weight', 
               fitsimage = 'ALMA_TP.'+source+'.'+name_line+'.image.weight.fits')

