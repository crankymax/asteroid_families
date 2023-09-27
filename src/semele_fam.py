import pandas as pd

from horizons_api import get_family_eph, convert_dy2yr
from parse_afp_family import afp_family_members, afp_proper_elements, mmr_atlas
from sim_creation import create_mercurious_sim
from prepare_clones import create_clones
from pathlib import Path


def simulation_project(base_dir, family_name, family_id):
    """
    Project definition that initiates a simulation project.

    This is a template for asteroid family simulations. It allows the definition of
    a family name and identifier. The function then creates the dataframes that contain the
    data that are used to create the simulations. In this case we define the luthera family
    of 1303
    :return:
    """

    project_dir = Path(f'{base_dir}') / f'{family_name}_ast/'
    project_dir.mkdir(parents=True, exist_ok=True)

    # Extract the family from AFP data
    afp_families = afp_family_members(project_dir)
    family_afp = afp_families[afp_families.family_id == family_id]

    # Extract the 2 body mmr atlas
    mmr_atlas(project_dir)

    # Join the family members and the proper_elements
    proper_elements = project_dir / f'{family_name}_proper.h5'
    if not proper_elements.exists():
        # Get the proper elements
        afp_proper = afp_proper_elements(project_dir)

        family_elements = pd.merge(family_afp[['ast_name']], afp_proper, how='inner', on='ast_name')
        family_elements.to_hdf(proper_elements.resolve(), 'family_proper_elements', mode='w')
    else:
        family_elements = pd.read_hdf(proper_elements.resolve(), 'family_proper_elements', mode='r')

    # Retrieve the ephemeris
    ephemeris_df = get_family_eph(project_dir, family_elements)

    # create the sim files
    # These parameters can be altered to suit the simulation resources available
    # Number of test-particles to be inserted into each simulation file
    part_per_sim = 6
    # The list of planets (active bodies) to be sourced from Horizons
    active_list = ['Sun', 'Venus', 'Earth', 'Mars', 'Ceres', 'Jupiter', 'Saturn', 'Uranus', 'Neptune']
    # This dict provides the mass of Ceres which is unavailable from Horizons
    actives_mass = {4: 5.21e-10}
    input_dir = project_dir / 'inputs'
    input_dir.mkdir(parents=True, exist_ok=True)

    # Creation of the base simulation file with a Mercurius integrator. An alternative is the WHFast integrator.
    base_sim = create_mercurious_sim(active_list, actives_mass)

    # Create the required simulation files in the input directory.
    create_clones(ephemeris_df, input_dir, base_sim, part_per_sim)

    print(f"Completed creating:{active_list}")


if __name__ == '__main__':
    simulation_project('../../', 'semele', '86')
