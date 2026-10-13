import requests

import numpy as np

from pathlib import Path
import pandas as pd

# Column names used in the ephemeris dataframe
eph_cols_df = ['ast_name', 'X', 'Y', 'Z', 'VX', 'VY', 'VZ', 'sX', 'sY', 'sZ', 'sVX', 'sVY', 'sVZ']


def is_float(element: any) -> bool:
    """
    Check the element can be converted to a float
    :param element: string representing a float value for an orbital parameter
    :return: True if float otherwise False
    """
    try:
        float(element)
        return True
    except (ValueError, TypeError):
        return False


def check_ephem(ast_values):
    """
    Check the list of values to ensure that they all have non-zero not-null values
    :param ast_values:
    :return: True if valid value False otherwise
    """
    if any(ast_values) == 0.0:
        return False
    elif any(ast_values) is None:
        return False

    return True


def retrieve_ephemeris(asteroids):
    """
    Extract the ephemeris values for the asteroids in the dataframe parameter
    :param asteroids: pandas dataframe with ast_name column
    :return: list of asteroid ephemeris
    """
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
    for ast_name in asteroids.ast_name:
        # There is an incompatibility between AFP and Horizons with multi-oppositional
        # asteroids (i.e. horizons wants '2004 YR21'  vs AFP provides '2004YR21'
        if not ast_name.isnumeric():
            # print(f'Mangle this : {" ".join([ast_name[0:4], ast_name[4:]])}')
            horizons_ast_name = " ".join([ast_name[0:4], ast_name[4:]])
        else:
            horizons_ast_name = ast_name

        # Setup the JSON HTTP request
        horizons_params['COMMAND'] = f"'{horizons_ast_name};'"
        r = requests.get('https://ssd.jpl.nasa.gov/api/horizons.api',
                         data=horizons_params)
        # Process the result
        hozres = r.json()['result']
        biz_start = hozres.find('$$SOE')
        biz_end = hozres.find('$$EOE')
        # Check we got the bizness
        if biz_start == -1:

            print(f'Error fetching ephemeris for asteroid |{ast_name}|')
            # No bizness; no worries. Try the next one
            continue

        # Extract the ephemeris text
        horizon_ephem = hozres[biz_start+6: biz_end]
        # Create the new list to store the values
        ephem_values = [ast_name]
        # The request stated we wanted CSV format so parsing is easier
        horizon_values = horizon_ephem.split(',')
        for val in horizon_values[2:14]:
            if val.strip() == 'n.a.':
                ephem_values.append(None)
            elif not is_float(val):
                print(f'asteroid {ast_name} has bad value |{val}|') if (len(val) >= 1) else None
                continue
            else:
                ephem_values.append(float(val))
        # Check parsed values, and append if all good.
        if check_ephem(ephem_values):
            asteroids_ephem.append(ephem_values)
        else:
            print(f'asteroid {ast_name} has parsing errors |{horizon_ephem}|')

    return asteroids_ephem


def convert_dy2yr(eph_df):
    """
    The Horizons data has velocities as AU/dy; but REBOUND defaults to AY/yr. This changes the values
    in the parameter dataframe. However it will also handle dict's
    :param eph_df: The pandas dataframe with Horizons values
    :return:
    """
    dy2yr = 365.25 / (2 * np.pi)

    eph_df['VX'] = eph_df['VX'] * dy2yr
    eph_df['VY'] = eph_df['VY'] * dy2yr
    eph_df['VZ'] = eph_df['VZ'] * dy2yr
    eph_df['sVX'] = eph_df['sVX'] * dy2yr
    eph_df['sVY'] = eph_df['sVY'] * dy2yr
    eph_df['sVZ'] = eph_df['sVZ'] * dy2yr


def get_family_eph(data_dir, target_family):
    """
    A check is made if the data is locally available, if so that is used. Otherwise the target_family
    is retrieved from Horizons.
    :param data_dir: Project directory
    :param target_family: A list of asteroid identifiers.
    :return: ephemeris dataframe.
    """
    family_eph = data_dir / 'ephemerides.h5'

    if not Path(family_eph).exists():
        target_ephemeris = retrieve_ephemeris(target_family)
        trgt_eph_df = pd.DataFrame(target_ephemeris, columns=eph_cols_df)
        convert_dy2yr(trgt_eph_df)

        # Save a copy
        trgt_eph_df.to_hdf(family_eph.resolve(), 'ephemerides', mode='w')
    else:
        trgt_eph_df = pd.read_hdf(family_eph.resolve(), 'ephemerides')

    return trgt_eph_df
