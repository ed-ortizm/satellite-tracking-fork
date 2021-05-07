# lets say 20 output for satellite:
# just to see like one line randomly
###########################################
# Observations are starting friday 7/5/2021
###########################################
# add a data structure so for each observatory you have a config of alt lat,
# lon of the sat according to a given observatory and time
###########################################
import os
import sys
import time
from datetime import datetime, timezone

import ephem
import matplotlib.pyplot as plt
import numpy as np
import pyorbital
from pyorbital.orbital import Orbital
import urllib
################################################################################
def time_stamp():

    date = datetime.now(tz=timezone.utc)
    year = date.year
    month = date.month
    day = date.day
    hour = date.hour
    minute = date.minute
    second = date.second

    stamp = (f'{year}_{month:02}_{day:02}_'
        f'{hour:02}h_{minute:02}m_{second:02}s')

    return stamp
################################################################################
def download_tle(satellite_brand:'str', tle_dir:'str'):

    sat_tle_url = (f'https://celestrak.com/NORAD/elements/supplemental/'
        f'{satellite_brand}.txt')

    tle_file = f'tle_{satellite_brand}_{time_stamp()}.txt'

    if not os.path.exists(tle_dir):
        os.makedirs(tle_dir)

    urllib.request.urlretrieve(sat_tle_url, f'{tle_dir}/{tle_file}')

    return tle_file
################################################################################
def observatory_pro(observatories:'dict'):
    # converts to format used by otarola

# ;       .observatory - abbreviated observatory name
# ;       .name - full observatory name
# ;       .longitude - observatory longitude in degrees *west*
# ;       .latitude - observatory latitude in degrees
# ;       .altitude - observatory altitude in meters above sea level
# ;       .tz - time zone, number of hours *west* of Greenwich

    satellite_track = {}
    for observatory, data in observatories.items():
        otarola_format = {}
        for key, val in data.items():
            if type(val)==type([]):
                signo = 1
                otarola_format[key]=0
                for idx, f in enumerate(val):
                    if f<0:
                        signo = -1
                        f = abs(f)
                    otarola_format[key] += f/60**idx
                otarola_format[key] = signo*otarola_format[key]
            else:
                otarola_format[key]=val

            if key=='longitude':
                if otarola_format[key] > 180.:
                    otarola_format[key] = 360 - otarola_format[key]
                else:
                    otarola_format[key] = -otarola_format[key]

        satellite_track[observatory] = otarola_format
    return satellite_track
################################################################################
example_script_input = f'IAC80 "STARLINK-1436 (VISORSAT)" 2020 8 31'
observatories= {
    'KPEAK':['K.P. Observatory', +31.9599, -111.5997, 2.067],
    'CTIO':['CTIO', -30.1690, -70.8063, 2.2],
    'CKOIRAMA':['Ckoirama Observatory', -24.08913333, -69.93058889, 0.966],
    'HOME':['Home', +32.2671111, -110.8507778, .753],
    'VLT':['VLT', -24.6275, -70.4044, 2.650],
    'VISTA':['VISTA', -24.6157000, -70.3976000, 2.635],
    'CHILESCOPE':['CHILESCOPE', -30.4708333333333, -70.7647222222222, 1.580],
    'IAC80':['IAC80', +28.29966667, -16.51102778, 2.38125],
    'CA':['CA', 37.22364444, -2.54621667, 2.168]
    }
# Store orbital computations in file
#print the columns header of sat data to be displayed
# Note the angular speed of the satellite is in the AZ,EL (or AZ,ALT) frame
## Convert using str.join and a function like list_to_str
ut_time = 'UT Date, UT time'
lla_sat = 'Sat(lon) [deg], Sat(lat) [deg], Sat(alt) [km]'
angular_sat = 'Sat(Azimuth) [deg], Sat(Elevation), [deg] SatRA[hr], SatDEC[deg]'
angular_sun = 'SunRA[hr], SunDEC[deg], SunZenithAngle[deg]'
speed_sat = 'SatAngularSpeed [arcsecs/sec]'

colum_headers = f'{ut_time}, {lla_sat}, {angular_sat}, {angular_sun}, {speed_sat}'

################################################################################
# str manipulation

def data_formating(date_obj, darksat_latlon, sat_az, sat_alt,
    raSAT_h, raSAT_m, raSAT_s, decSAT_d, decSAT_m, decSAT_s,
    sunRA, sunDEC, sun_zenith_angle, ang_motion):

    year = date_obj.year
    month = date_obj.month
    day = date_obj.day
    hour = date_obj.hour
    minute = date_obj.minute
    second = date_obj.second - 5

    date = f'{year}-{month:02}-{day:02}'
    time = f'{hour:02}:{minute:02}:{second:02}s'

    # print(date_obj)
    # date_obj.second -= 5
    # print(date_obj)
    computed_data_str = [
        f'{date_obj}\t', f'{darksat_latlon[0]:9.6f}\t',
        f'{darksat_latlon[1]:9.6f}\t', f'{darksat_latlon[2]:5.2f}\t',
        f'{sat_az:06.3f}\t',
        f'{sat_alt:06.3f} ',
        f'{raSAT_h:02d}h{raSAT_m:02d}m{raSAT_s:05.3f}s ',
        f'{decSAT_d:03d}:{decSAT_m:02d}:{decSAT_s:05.3f} ',
        f'{sunRA:09.7f} ', f'{sunDEC:09.7f} ',
        f'{sun_zenith_angle:07.3f} ', f'{ang_motion:08.3f}'
        ]

    computed_data_str_simple = [
        f'{date}\t',
        f'{time}\t',
        f'{raSAT_h:02d}h{raSAT_m:02d}m{raSAT_s:05.3f}s\t',
        f'{decSAT_d:03d}:{decSAT_m:02d}:{decSAT_s:05.3f}'
        ]
    data_str = ''.join(computed_data_str)
    data_str_simple = ''.join(computed_data_str_simple)

    return data_str, data_str_simple

################################################################################
def ra_to_hours(ra):
    ra = ra*180./np.pi

    if ra < 0 :
        ra += 360

    ra = ra*(24./360.)

    return ra
################################################################################
def radians_to_deg(radians):

    deg = radians*180./np.pi

    return deg
################################################################################
def ra_to_hh_mm_ss(ra):
    # converts the RA to hh:mm:ss.sss

    hrs = ra_to_hours(ra)

    hh = int(hrs)

    mins = (hrs-hh)*60.
    mm = int(mins)

    ss = (mins-mm)*60

    return hh, mm, ss
################################################################################
def dec_to_dd_mm_ss(dec):
    # converts the DEC to dd:mm:ss
    dec = radians_to_deg(dec)

    if dec < 0:
       dec_sign = -1
       dec = abs(dec)
    else:
        dec_sign = 1

    dd = int(dec)

    mins = (dec-dd)*60.
    mm = int(mins)

    ss = (mins-mm)*60

    return dd*dec_sign, mm, ss
################################################################################
import math
import os
import sys
import time
import urllib

from datetime import datetime, timezone
import ephem
import numpy as np
import pyorbital
from pyorbital.orbital import Orbital
################################################################################
tle_dir = f'/home/edgar/Documents/satellite-tracking/tle_dir'
def compute_visible(satellite:'str', window:'str', observatory_data:'dict',
    output_fname:'str', output_fname_simple:'str', tle_file:'str',
    year, month, day,
    output_dir:'str'):

    observer = ephem.Observer()
    observer.epoch = '2000'
    observer.pressure= 1010
    observer.temp = 15
    ########################################################################
    obs_lat = observatory_data['latitude']
    obs_lon = observatory_data['longitude']
    obs_altitude = observatory_data['altitude']/1000. # in km
    ################################################################################
    observer.lon = np.radians(obs_lon)
    observer.lat = np.radians(obs_lat)
    observer.elevation = observatory_data['altitude']# in meters
    ############################################################################
    flag = 0
    darksat = Orbital(satellite, tle_file=f'{tle_dir}/{tle_file}')
    ############################################################################
    sat_az0 =0
    sat_alt0 =0
    hr0 = 0
    ############################################################################
    if window=='evening':
        hours = [18, 19, 20, 21, 22, 23, 0, 1, 2]
    elif window=='morning':
        hours = [6, 7, 8, 9, 10, 11, 12]
    else:
        print(f'window keyword must be of either "morning" or "evening"')
        sys.exit()
    ############################################################################
    for hr in hours:

        if hr == 0 and window =='evening':
            day += 1

        for mn in range(0, 60):

            for secs in range(30, 31):

                date_obj = datetime(year, month, day, hr, mn, secs)

                # computes the current latitude, longitude of the satellite's
                #footprint and its current orbital altitude
                darksat_latlon = darksat.get_lonlatalt(date_obj)

                # uses the observer coordinates to compute the satellite azimuth
                # and elevation, negative elevation implies satellite is under
                # the horizon
                sat_az, sat_alt = darksat.get_observer_look(date_obj,
                    obs_lon, obs_lat, obs_altitude)

                # gets the Sun's RA and DEC at the time of observation
                sun_ra, sun_dec = pyorbital.astronomy.sun_ra_dec(date_obj)

                sun_zenith_angle = pyorbital.astronomy.sun_zenith_angle(
                    date_obj, obs_lon, obs_lat)

                sunRA = ra_to_hours(ra=sun_ra)
                sunDEC = radians_to_deg(radians=sun_dec)

                observer.date = ephem.date(date_obj)
                ra, dec = observer.radec_of(np.radians(sat_az), np.radians(sat_alt))
                ####################################################################
                # converts the RA to hh:mm:ss.sss
                raSAT_h, raSAT_m, raSAT_s = ra_to_hh_mm_ss(ra)
                ####################################################################
                # converts the DEC to dd:mm:ss
                # print(dec)
                decSAT_d, decSAT_m, decSAT_s = dec_to_dd_mm_ss(dec=dec)
                ####################################################################
                #us
                if sat_alt > 35 and sun_zenith_angle > 95 and sun_zenith_angle < 125:
                # # Angel
                # if sat_alt > 0 and sun_zenith_angle > 95 and sun_zenith_angle < 115:

                    ################################################################
                    flag += 1

                    if flag == 1:

                        with open(f'{output_dir}/{output_fname}.txt', 'a') as file:
                            file.write(f'{satellite}\n')

                        with open(f'{output_dir}/{output_fname_simple}.txt',
                            'a') as file_simple:

                            file_simple.write(f'{satellite}\n')
                    ################################################################
                    # compute the change in AZ and ALT of the satellite position
                    # between this and previous observation
                    ################################################################
                    # difference in azimuth between current and previous postions in
                    # arcsecs
                    daz  = (sat_az - sat_az0)*3600

                    # difference in altitude between current and previous postions
                    # in arcsecs
                    dalt = (sat_alt - sat_alt0)*3600

                    # difference in time stamps between current and previous
                    # observation in seconds of time
                    dt = ((hr + mn/60. + secs/3600.) - hr0)*3600.

                    # sets the current sat position and time, as the "previous" for
                    # next observation
                    sat_az0 = sat_az
                    sat_alt0 = sat_alt
                    hr0 = hr + mn/60. + secs/3600.

                    ang_motion = math.sqrt(math.pow(daz,2) + math.pow(dalt,2))/dt
                    # prints out the UT time, and satellite footprint position as well as
                    # satellite azimuth and elevation at the observer location

                    data_str, data_str_simple = data_formating(
                        date_obj,
                        darksat_latlon,
                        sat_az, sat_alt,
                        raSAT_h, raSAT_m, raSAT_s,
                        decSAT_d, decSAT_m, decSAT_s,
                        sunRA, sunDEC, sun_zenith_angle,
                        ang_motion)
                    ################################################################
                    with open(f'{output_dir}/{output_fname}.txt', 'a') as file:
                        file.write(f'{data_str}\n')

                    with open(f'{output_dir}/{output_fname_simple}.txt',
                        'a') as file_simple:
                        file_simple.write(f'{data_str_simple}\n')
                    ################################################################
                else:
                    # keeps copy of the current AZ, ALT and time information
                    # to derive angular speed of the satellite in the AZ,EL frame
                    sat_az0 = sat_az
                    sat_alt0 = sat_alt
                    hr0 = hr + mn/60. + secs/3600.
################################################################################

def input_handler(arguments):
    "arguments: list with arguments pass to the script"

    n_args = len(arguments)

    if n_args < 7 or n_args > 7:
        print(f'Use: python satellite_track.py sat_brand obs  Year Month Day window')
        print(f'Ex: python p_satellite_track.py oneweb eso 2021 05 07 morning')
        sys.exit()

    satellite_brand = arguments[1]
    observatory = arguments[2]

    year = int(arguments[3])
    month = int(arguments[4])
    day = int(arguments[5])

    window = arguments[6]
    ############################################################################
    return satellite_brand, observatory, year, month, day, window
# def radians_to_hrs(radians):
#
#     deg = radians_to_deg(radians)
#
#     hrs = deg*24./360
#
#     return hrs
# def input_handler(arguments):
#
#     "arguments: list with arguments pass to the script"
#
#     n_args = len(arguments)
#
#     if n_args < 6:
#         print(f'Use: python satellite_track.py OBSname SATid Year Month Day')
#         print(f'Ex: python satellite_track.py {example_script_input}')
#         sys.exit()
#
#     elif arguments[1] in observatories.keys():
#
#         obs_name = observatories[arguments[1]][0]
#         obs_lat = observatories[arguments[1]][1]
#         obs_lon = observatories[arguments[1]][2]
#         obs_altitude = observatories[arguments[1]][3]
#         satellite_ID = arguments[2]
#         satellite_brand = satellite_ID.split('-')[0].lower()
#         year  = int(arguments[3])
#         month = int(arguments[4])
#         day   = int(arguments[5])
#
#         print(f'Observatory: {obs_name}')
#         print(f'Observatory latitude: {obs_lat}')
#         print(f'Observatory latitude: {obs_lon}')
#         print(f'Observatory latitude: {obs_altitude}')
#         print(f'Satellite ID: {satellite_ID}')
#         print(f'Forecast date: {day}/{month}/{year}\n')
#
#         return (obs_name, obs_lat, obs_lon, obs_altitude, year, month, day,
#             satellite_ID, satellite_brand)
#
#     else:
#
#         print(f'Observatory name = {arguments[1]}  not found...')
#         sys.exit()
###############################################################################
