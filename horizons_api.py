import requests
import numpy as np

from pathlib import Path
import pandas as pd

def is_float(element: any) -> bool:
    try:
        float(element)
        return True
    except (ValueError, TypeError):
        return False


def check_ephem(ast_values):
    if any(ast_values) == 0.0:
        return False
    elif any(ast_values) is None:
        return False

    return True


def retrieve_ephemeris(asteroids):
    results = dict()
    missed_ephem = list()
    results['not_found'] = missed_ephem
    horizons_params = {'MAKE_EPHEM': 'YES', 'EPHEM_TYPE': 'VECTORS', 'CENTER': '500@0',
                       'TLIST_TYPE': 'MJD', 'TIME_TYPE': 'UT', 'TLIST': '51544',
                       'VEC_TABLE': '2X', 'REF_SYSTEM': 'ICRF', 'REF_PLANE': 'ECLIPTIC',
                       'VEC_CORR': 'NONE', 'CAL_TYPE': 'M', 'OUT_UNITS': 'AU-D',
                       'VEC_LABELS': 'YES', 'VEC_DELTA_T': 'NO',
                       'CSV_FORMAT': 'YES', 'OBJ_DATA': 'YES', 'FORMAT': 'json'}

    asteroids_ephem = []
    for asteroid in asteroids:
        ast_name = asteroid[0]
        if not ast_name.isnumeric():
            # print(f'Mangle this : {" ".join([ast_name[0:4], ast_name[4:]])}')
            ast_name = " ".join([ast_name[0:4], ast_name[4:]])

        horizons_params['COMMAND'] = f"'{ast_name};'"
        r = requests.get('https://ssd.jpl.nasa.gov/api/horizons.api',
                         data=horizons_params)

        hozres = r.json()['result']
        biz_start = hozres.find('$$SOE')
        biz_end = hozres.find('$$EOE')
        if biz_start == -1:

            print(f'Error fetching ephemeris for asteroid |{ast_name}|')
            continue

        horizon_ephem = hozres[biz_start+6: biz_end]

        ephem_values = [ast_name]

        horizon_values = horizon_ephem.split(',')
        for val in horizon_values[2:14]:
            if val.strip() == 'n.a.':
                ephem_values.append(None)
            elif not is_float(val):
                print(f'asteroid {ast_name} has bad value |{val}|') if (len(val) >= 1) else None
                continue
            else:
                ephem_values.append(float(val))

        if check_ephem(ephem_values):
            asteroids_ephem.append(ephem_values)
        else:
            print(f'asteroid {ast_name} has parsing errors |{horizon_ephem}|')

    return asteroids_ephem


def convert_dy2yr(eph_df):
    dy2yr = 365.25 / (2 * np.pi)

    eph_df['VX'] = eph_df['VX'] * dy2yr
    eph_df['VY'] = eph_df['VY'] * dy2yr
    eph_df['VZ'] = eph_df['VZ'] * dy2yr
    eph_df['sVX'] = eph_df['sVX'] * dy2yr
    eph_df['sVY'] = eph_df['sVY'] * dy2yr
    eph_df['sVZ'] = eph_df['sVZ'] * dy2yr


def get_family_eph(target_family):
    if not Path('luthera_eph.h5').exists():
        target_ephemeris = retrieve_ephemeris(target_family)
        cols_df = ['ast_name', 'X', 'Y', 'Z', 'VX', 'VY', 'VZ', 'sX', 'sY', 'sZ', 'sVX', 'sVY', 'sVZ']
        trgt_eph_df = pd.DataFrame(target_ephemeris, columns=cols_df)
        convert_dy2yr(trgt_eph_df)

        # Save a copy
        trgt_eph_df.to_hdf('luthera_eph.h5', 'luthera_eph', mode='w')
    else:
        trgt_eph_df = pd.read_hdf('luthera_eph.h5', 'luthera_eph')

    return trgt_eph_df
