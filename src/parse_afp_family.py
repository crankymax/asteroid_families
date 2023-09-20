import pandas as pd
from urllib import request
from pathlib import Path

afp_fam_members = 'afp.fam.members.txt'
afp_prop_elements = 'afp.num.pro.txt'
afp_mprop_elements = 'afp.mult.pro.txt'

mmr_2b_atlas = 'mmr_2b_atlas.html'


def download_afp_data(project_dir):
    # TODO Work in progress
    afp_fam_local = Path(project_dir) / afp_fam_members
    # link to family summary data
    family_members_URL = 'http://asteroids.matf.bg.ac.rs/fam/families/afp.fam.members'
    request.urlretrieve(family_members_URL, afp_fam_local.resolve())
    # Get the proper elements for numbered asteroids
    afp_pe_local = Path(project_dir) / afp_prop_elements
    proper_elements_URL = 'http://asteroids.matf.bg.ac.rs/fam/proper/may2022/afp.num.pro'
    request.urlretrieve(proper_elements_URL, afp_pe_local.resolve())
    # Get the proper elements for the multi-opposition asteroid e.g. '2022 ES123'
    afp_mpe_local = Path(project_dir) / afp_mprop_elements
    mlti_prop_el_URL = 'http://asteroids.matf.bg.ac.rs/fam/proper/may2022/afp.mult.pro'
    request.urlretrieve(mlti_prop_el_URL, afp_mpe_local.resolve())


def download_mmr_data(project_dir):
    mmr_2b_URL = "http://www.fisica.edu.uy/~gallardo/atlas/2020/atlas2020.html"
    mmr_2b_local = Path(project_dir) / mmr_2b_atlas
    request.urlretrieve(mmr_2b_URL, mmr_2b_local.resolve())


def afp_family_members(data_dir):
    fam_hdf = Path(data_dir) / 'afp_families.h5'
    if not fam_hdf.exists():
        ast_cols = [(0, 11), (14, 20), (23, 34), (37, 48), (51, 62), (64, 72)]
        afp_fam_cols = ['ast_name', 'abs_mag', 'a_P', 'e_P', 'sineI_P', 'family_id']

        fam_rec_input = Path(data_dir) / afp_fam_members
        if not fam_rec_input.exists():
            download_afp_data(data_dir)

        afp_fam_df = pd.read_fwf(fam_rec_input.resolve(), skiprows=1, colspecs=ast_cols, names=afp_fam_cols,
                                dtype={'ast_name': str, 'abs_mag': float, 'a_P': float, 'e_P': float,
                                       'sineI_P': float, 'family_id': str})

        afp_fam_df.to_hdf(fam_hdf.resolve(), 'afp_families', mode='w')
    else:
        afp_fam_df = pd.read_hdf(fam_hdf.resolve(), 'afp_families', mode='r')
    return afp_fam_df


def afp_proper_elements(data_dir):
    proper_elements_hdf = Path(data_dir) / 'afp_proper_elements.h5'
    if not proper_elements_hdf.exists():
        element_cols = [(0, 11), (12, 18), (20, 30), (31, 41), (42, 52), (53, 64), (65, 77), (78, 90),
                        (91, 101), (102, 108)]
        element_names = ['ast_name', 'abs_mag', 'a_P', 'e_P', 'sineI_P', 'n', 'g', 's', 'lyap_time', 'My_int_time']

        afp_input = Path(data_dir) / afp_prop_elements
        proper_elements = pd.read_fwf(afp_input.resolve(), names=element_names, colspecs=element_cols,
                                      dtype={'ast_name': str, 'abs_mag': float, 'a_P': float, 'e_P': float,
                                             'sineI_P': float, 'n': float, 'g': float, 's': float,
                                             'lyap_time': float, 'My_int_time': int})

        afp_input = Path(data_dir) / afp_mprop_elements
        multi_proper = pd.read_fwf(afp_input.resolve(), names=element_names, colspecs=element_cols,
                                      dtype={'ast_name': str, 'abs_mag': float, 'a_P': float, 'e_P': float,
                                             'sineI_P': float, 'n': float, 'g': float, 's': float,
                                             'lyap_time': float, 'My_int_time': int})

        all_in_all = pd.concat([proper_elements, multi_proper])
        all_in_all.to_hdf(proper_elements_hdf.resolve(), 'afp_proper_elements', mode='w')
    else:
        all_in_all = pd.read_hdf(proper_elements_hdf.resolve(), 'afp_proper_elements', mode='r')

    return all_in_all


def mmr_atlas(data_dir):
    proper_elements_hdf = Path(data_dir) / 'mmr_atlas.h5'
    if not proper_elements_hdf.exists():
        mmr_cols = [(0, 2), (5, 7), (8, 10), (10, 20), (20, 26), (28, 32), (32, 36), (38, 40),
                    (41, 52), (53, 64), (65, 76), (77, 92), (93, 103)]
        mmr_names = ['planet', 'ratio1', 'ratio2', 'sma', 'ecc', 'inc', 'w', 'ln', 'R', 'strength',
                     'width', 'sigma', 'periods']

        mmr_2b_path = Path(data_dir) / mmr_2b_atlas
        if not mmr_2b_path.exists():
            download_mmr_data(data_dir)

        mmr_atlas_df = pd.read_fwf(mmr_2b_path.resolve(), skiprows=22, skipfooter=5, names=mmr_names, colspecs=mmr_cols,
                                   dtype={'planet': str, 'ratio1': int, 'ratio2': int, 'sma': float, 'ecc': float,
                                   'inc': float, 'w': float, 'ln': float, 'R': float, 'strength': float,
                                   'width': float, 'sigma': str, 'periods': float})
        mmr_atlas_df.to_hdf(proper_elements_hdf.resolve(), 'mmr_atlas', mode='w')
    else:
        mmr_atlas_df = pd.read_hdf(proper_elements_hdf.resolve(), 'mmr_atlas', mode='r')

    return mmr_atlas_df




