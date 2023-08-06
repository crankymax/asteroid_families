import pandas as pd
from urllib import request
from pathlib import Path

def download_astdys_data(project_dir):
    # TODO Work in progress
    # link to family summary data
    syn_pe_URL = 'https://newton.spacedys.com/~astdys2/propsynth/all_tro.famrec'
    request.urlretrieve(syn_pe_URL, project_dir + '/afp_fam_members.txt')
    family_summary_URL = 'https://newton.spacedys.com/~astdys2/propsynth/all_tro.famtab'
    request.urlretrieve(family_summary_URL, project_dir + '/afp_fam_summary.txt')
    family_members_URL = 'https://newton.spacedys.com/~astdys2/propsynth/all_tro.members'
    request.urlretrieve(family_members_URL, project_dir + '/afp_fam_summary.txt')


def parse_tro_families():
    ast_cols = [(0, 9), (12, 16), (21, 24), (26, 38), (40, 45), (46, 55), (57, 60), (71, 75), (77, 86),
                (88, 93)]

    asteroids: list[list] = []
    luthera_family: list[list] = []

    ast_input = open('../../asteroid_data/all_tro.members.txt')

    for asteroid in ast_input:
        if asteroid[0] == '%':
            continue
        ast_details = []
        for col in ast_cols:
            ast_details.append(asteroid[col[0]:col[1]].strip())

        asteroids.append(ast_details)
        if ast_details[3] == '1303':
            luthera_family.append(ast_details)

    return asteroids, luthera_family


"""The family membership table and individual family files:   afp.fam.members

Column 1: Asteroid number or designation
Column 2: Absolute magnitude
Column 3: Proper semi-major axis [au]
Column 4: Proper eccentricity
Column 5: Sine of proper inclination
Column 6: Family ID (a number of the lowest numbered family member)
"""


def parse_fam_families(data_dir, target_family):
    ast_cols = [(0, 11), (14, 20), (23, 34), (37, 48), (51, 62), (64, 72)]

    asteroids: list[list] = []
    luthera_family: list[list] = []

    ast_input = open(data_dir)

    for asteroid in ast_input:
        ast_details = []
        for col in ast_cols:
            ast_details.append(asteroid[col[0]:col[1]].strip())
        asteroids.append(ast_details)
        if ast_details[5] == target_family:
            luthera_family.append(ast_details)

    return asteroids, luthera_family


# TODO Parse the summary file
"""
The summary table of asteroid families:   afp.fam.summary

Column 1: Family ID (a number of the lowest numbered family member)
Column 2: Family name (name of the lowest numbered member)
Column 3: Nominal cut-off distance used for the HCM
Column 4: Number of identified members
Column 5: Main belt region (IB = Inner belt; MB = Middle belt; OB = Outer belt)
"""


def get_family_df(data_dir, family_name="1303"):
    asteroids, target_family = parse_fam_families(data_dir, family_name)

    afp_fam_cols = ['ast_name', 'abs_mag', 'a_P', 'e_P', 'sineI_P', 'family_id']
    afp_fam_df = pd.DataFrame(asteroids, columns=afp_fam_cols)
    afp_fam_df[['abs_mag', 'a_P', 'e_P', 'sineI_P']] = afp_fam_df[['abs_mag', 'a_P', 'e_P', 'sineI_P']].apply(
        pd.to_numeric)
    afp_fam_df.to_hdf(f'{data_dir}afp_families.h5', 'afp_families', mode='w')

    lth_fam_df = pd.DataFrame(target_family, columns=afp_fam_cols)
    lth_fam_df[['abs_mag', 'a_P', 'e_P', 'sineI_P']] = lth_fam_df[['abs_mag', 'a_P', 'e_P', 'sineI_P']].apply(
        pd.to_numeric)
    lth_fam_df.to_hdf(f'{data_dir}luthera_family.h5', 'luthera_family', mode='w')

    return target_family


def ast_proper_elements(data_dir):
    element_cols = [(0, 11), (12, 16), (20, 30), (31, 39), (41, 49), (51, 60), (62, 74), (76, 88),
                    (89, 95), (96, 97)]
    element_names = ['ast_name', 'abs_mag', 'a_P', 'e_P', 'sineI_P', 'n', 'g', 's', 'LCE', 'My_ast']
    element_types = ['string', 'float', 'float', 'float', 'float', 'float', 'float', 'float', 'float', 'int']
    asteroids: list[list] = []
    luthera_family: list[list] = []

    ast_input = open(Path(data_dir) / 'all.syn.txt')
    parse_fix_cols(ast_input, element_cols)


def parse_fix_cols(input_text, col_defs):
    parse_results = []
    for line_text in input_text:
        if line_text[0] == '%':
            continue

        line_values = []
        for col in col_defs:
            line_values.append(line_text[col[0]:col[1]].strip())
        parse_results.append(line_values)
    return parse_results


def calculate_diameter(mag_h, p_v=0.0387):
    # D= 1329×10−H/5 ×1/√pv
    # Assuming a common geometric albedo p_v = 0.0387
    # 0.0387 and a diameter of 85.08 kilometers based on an absolute magnitude
    # of 9.5
    return (1329 * 10**(-mag_h/5)) * (p_v ** (-0.5))



