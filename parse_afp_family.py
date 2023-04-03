import pandas as pd


def parse_tro_families():
    ast_cols = [(0, 9), (12, 16), (21, 24), (26, 38), (40, 45), (46, 55), (57, 60), (71, 75), (77, 86),
                (88, 93)]

    asteroids: list[list] = []
    luthera_family: list[list] = []

    ast_input = open('../asteroid_data/all_tro.members.txt')

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


def parse_fam_families(target_family='1303'):
    ast_cols = [(0, 11), (14, 20), (23, 34), (37, 48), (51, 62), (64, 72)]

    asteroids: list[list] = []
    luthera_family: list[list] = []

    ast_input = open('../asteroid_data/afp.fam.members.txt')

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






