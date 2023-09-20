import pandas as pd

from horizons_api import get_family_eph, convert_dy2yr
from parse_afp_family import afp_family_members, afp_proper_elements, mmr_atlas
from sim_creation import create_mercurious_sim
from prepare_clones import create_clones
from pathlib import Path


def simulation_project():
    """
    Project definition that initiates a simulation project.

    This is a template for other asteroid family simulations. It allows the definition of
    a family name and identifier. The function then creates the dataframes that contain the
    data that are used to create the simulations. In this case we define the luthera family
    of 1303
    :return:
    """
    family_name = 'luthera'
    family_id = '1303'

    project_dir = Path(f'../../{family_name}_ast/')

    # Add active asteroid  426/P
    # COMMAND = 'DES=1003609;NOFRAG;'
    """$$SOE
    2451544.500000000, A.D. 2000-Jan-01 00:00:00.0000,  2.334269053942694E+00, -1.808322981199081E+00,  
    6.292178749934185E-01,  4.428832441905231E-03,  8.923607089146576E-03,  1.921127626386464E-03, 
    1.48642185E-05,  2.32441520E-05,  6.25526758E-06,  7.55661843E-08,  4.71045977E-08,  2.07506493E-08,
    $$EOE
    """
    p_426 = {'ast_name': 'P_426', 'X': 2.334269053942694E+00, 'Y': -1.808322981199081E+00, 'Z': 6.292178749934185E-01,
             'VX': 4.428832441905231E-03, 'VY': 8.923607089146576E-03, 'VZ': 1.921127626386464E-03,
             'sX': 1.48642185E-05, 'sY': 2.32441520E-05, 'sZ': 6.25526758E-06,
             'sVX': 7.55661843E-08, 'sVY': 4.71045977E-08, 'sVZ': 2.07506493E-08}

    convert_dy2yr(p_426)

    # Extract the family from AFP data
    afp_families = afp_family_members(project_dir)
    luthera_family_afp = afp_families[afp_families.family_id == family_id]

    # Extract the 2 body mmr atlas
    mmr_atlas(project_dir)

    # Join the family members and the proper_elements
    luthera_prop = project_dir / 'luthera_proper.h5'
    if not luthera_prop.exists():
        # Get the proper elements
        afp_proper = afp_proper_elements(project_dir)

        luthera_elements = pd.merge(luthera_family_afp[['ast_name']], afp_proper, how='inner', on='ast_name')
        luthera_elements.to_hdf(luthera_prop.resolve(), 'family_proper_elements', mode='w')
    else:
        luthera_elements = pd.read_hdf(luthera_prop.resolve(), 'family_proper_elements', mode='r')

    # Retrieve the ephemeris
    lth_eph_df = get_family_eph(project_dir, luthera_elements)
    # Add the P/426 active asteroid ephemeris to the family
    lth_eph_df.loc[len(lth_eph_df)] = [p_426[x] for x in ['ast_name', 'X', 'Y', 'Z', 'VX', 'VY', 'VZ',
                                                          'sX', 'sY', 'sZ', 'sVX', 'sVY', 'sVZ']]

    # create the sim files
    part_per_sim = 3

    active_list = ['Sun', 'Mars', 'Ceres', 'Jupiter', 'Saturn', 'Uranus', 'Neptune']
    actives_mass = {2: 5.21e-10}
    input_dir = project_dir / 'inputs'
    input_dir.mkdir(parents=True, exist_ok=True)

    base_sim = create_mercurious_sim(active_list, actives_mass)

    create_clones(lth_eph_df, input_dir, base_sim, part_per_sim)

    print(f"Completed creating:{active_list}")


if __name__ == '__main__':
    simulation_project()
