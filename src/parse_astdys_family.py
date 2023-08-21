import pandas as pd
from urllib import request
from pathlib import Path


ast_family_rec = 'all_tro.famrec.txt'
all_synths = 'all.syn.txt'

def download_astdys_data(project_dir):
    # TODO Work in progress
    # link to family summary data
    family_summary_URL = 'https://newton.spacedys.com/~astdys2/propsynth/all_tro.famrec'
    local_family = Path(project_dir) / ast_family_rec
    request.urlretrieve(family_summary_URL, local_family.resolve())

    syn_pe_URL = 'https://newton.spacedys.com/~astdys2/propsynth/all.syn'
    all_syn = Path(project_dir) / all_synths
    request.urlretrieve(syn_pe_URL, all_syn)


def ast_family_members(data_dir):
    family_hdf = Path(data_dir) / 'AstDyS_families.h5'

    if not family_hdf.exists():
        fam_rec_input = Path(data_dir) / ast_family_rec
        col_defs = [(0, 9), (10, 16), (17, 22), (26, 38), (39, 45), (46, 55), (57, 66), (68, 75), (77, 86),
                    (87, 95)]
        col_names = ['ast_name', 'abs_mag', 'status', 'family1', 'dv_fam1', 'near1', 'family2', 'dv_fam2',
                     'near2', 'rescod']
        family_members = pd.read_fwf(fam_rec_input.resolve(), skiprows=1, names=col_names, colspecs=col_defs,
                                     dtype={'ast_name': str, 'abs_mag': float, 'status': int, 'family1': str,
                                            'dv_fam1': str, 'near1': str, 'family2':str, 'dv_fam2': str,
                                            'near2': str, 'rescod': str})
        family_members.to_hdf(family_hdf.resolve(), 'family_records', mode='w')
    else:
        family_members = pd.read_hdf(family_hdf.resolve(), 'family_records', mode='r')
    return family_members


def ast_proper_elements(data_dir):
    proper_elements_hdf = Path(data_dir) / 'AstDyS_proper_elements.h5'
    if not proper_elements_hdf.exists():

        element_cols = [(0, 9), (10, 15), (16, 26), (27, 38), (39, 48), (49, 60), (61, 73), (74, 86),
                        (87, 94), (95, 98)]
        element_names = ['ast_name', 'abs_mag', 'a_P', 'e_P', 'sineI_P', 'n', 'g', 's', 'LCE', 'My_ast']

        ast_input = Path(data_dir) / all_synths
        proper_elements = pd.read_fwf(ast_input.resolve(), skiprows=2, names=element_names, colspecs=element_cols,
                                      dtype={'ast_name': str, 'abs_mag': float, 'a_P': float, 'e_P': float,
                                      'sineI_P': float, 'n': float, 'g': float, 's': float, 'LCE': float,
                                             'My_ast': int})

        proper_elements.to_hdf(proper_elements_hdf.resolve(), 'proper_elements', mode='w')
    else:
        proper_elements = pd.read_hdf(proper_elements_hdf.resolve(), 'proper_elements', mode='r')

    return proper_elements
