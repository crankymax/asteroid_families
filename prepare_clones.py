import math
import itertools
import os

import pandas as pd
from horizons_api import get_family_eph
from parse_afp_family import get_family_df
from sim_creation import create_whfast_sim, create_mercurious_sim, copy_sim


def add_level(inputs, levels):
    next_level = []
    for lvl in levels:
        for inp in inputs:
            ic = inp.copy()
            ic.append(lvl)
            next_level.append(ic)
    return next_level


def create_clones(asteroid_ephem, output_dir, sim_file, clones_per_sim=5):
    # produce a new column for each of the clones as values +- sigma
    asteroid_ephem['Xcp'] = asteroid_ephem['X'] * (1 + asteroid_ephem['sX'])
    asteroid_ephem['Ycp'] = asteroid_ephem['Y'] * (1 + asteroid_ephem['sY'])
    asteroid_ephem['Zcp'] = asteroid_ephem['Z'] * (1 + asteroid_ephem['sZ'])
    asteroid_ephem['Xcm'] = asteroid_ephem['X'] * (1 - asteroid_ephem['sX'])
    asteroid_ephem['Ycm'] = asteroid_ephem['Y'] * (1 - asteroid_ephem['sY'])
    asteroid_ephem['Zcm'] = asteroid_ephem['Z'] * (1 - asteroid_ephem['sZ'])
    asteroid_ephem['VXcp'] = asteroid_ephem['VX'] * (1 + asteroid_ephem['sVX'])
    asteroid_ephem['VYcp'] = asteroid_ephem['VY'] * (1 + asteroid_ephem['sVY'])
    asteroid_ephem['VZcp'] = asteroid_ephem['VZ'] * (1 + asteroid_ephem['sVZ'])
    asteroid_ephem['VXcm'] = asteroid_ephem['VX'] * (1 - asteroid_ephem['sVX'])
    asteroid_ephem['VYcm'] = asteroid_ephem['VY'] * (1 - asteroid_ephem['sVY'])
    asteroid_ephem['VZcm'] = asteroid_ephem['VZ'] * (1 - asteroid_ephem['sVZ'])

    # create the clones array
    ephem_types = [['Xcp', 'Xcm'], ['Ycp', 'Ycm'], ['Zcp', 'Zcm'],
                   ['VXcp', 'VXcm'], ['VYcp', 'VYcm'], ['VZcp', 'VZcm']]
    # Combine the clones into a list
    particles = [list(parts) for parts in itertools.product(*ephem_types)]
    # Now add the original asteroid to the list
    particles.append(['X', 'Y', 'Z', 'VX', 'VY', 'VZ'])

    # Set the index to the asteroid name
    lth_eph_df = asteroid_ephem.set_index('ast_name')
    # keep track of which clone is assigned to what simulation
    clone_assignments = list()

    # Determine the number of sims
    sim_numbers = math.ceil((len(asteroid_ephem) * len(particles)) / clones_per_sim)
    # generate the sims
    sim_list = copy_sim(sim_file, sim_numbers)

    # assign particles to simulation
    for a_n, asteroid in enumerate(lth_eph_df.index):
        for p_n, particle_cols in enumerate(particles):
            particle_vals = lth_eph_df.loc[asteroid][particle_cols]
            assigned_sim_no = ((p_n + (a_n*len(particles))) % sim_numbers)
            sim = sim_list[assigned_sim_no]
            sim.add(m=0.0, x=particle_vals.iloc[0], y=particle_vals.iloc[1], z=particle_vals.iloc[2],
                    vx=particle_vals.iloc[3], vy=particle_vals.iloc[4], vz=particle_vals.iloc[5])
            clone_assignments.append([assigned_sim_no, len(sim.particles), asteroid, particle_cols])

    cln_asg_cols = ['sim_no', 'particle_number', 'ast_name', 'particle_types']
    cln_asg_df = pd.DataFrame(clone_assignments, columns=cln_asg_cols)
    cln_asg_df.to_hdf(f'{output_dir}/clone_assignments.h5', 'clone_assignments', mode='w')

    # Write out the simulations
    for sim_no, sim in enumerate(sim_list):
        file_name = f'{output_dir}/sim_{sim_no:05}.bin'
        sim.save(file_name)


if __name__ == '__main__':
    # Do we want to add active asteroid  426/P ???
    # COMMAND = 'DES=1003609;NOFRAG;'
    """$$SOE
    2451544.500000000, A.D. 2000-Jan-01 00:00:00.0000,  2.334269053942694E+00, -1.808322981199081E+00,  6.292178749934185E-01,  4.428832441905231E-03,  8.923607089146576E-03,  1.921127626386464E-03,  1.48642185E-05,  2.32441520E-05,  6.25526758E-06,  7.55661843E-08,  4.71045977E-08,  2.07506493E-08,
    $$EOE
    """

    # Extract the family
    luthera_family = get_family_df("1303")
    # Retrieve the ephemeris
    lth_eph_df = get_family_eph(luthera_family)
    # create the sim files
    active_list_v = ['Sun', 'Venus', 'Earth', 'Mars', 'Jupiter', 'Saturn', 'Uranus', 'Neptune']
    active_list_vc = ['Sun', 'Venus', 'Earth', 'Mars', 'Ceres', 'Jupiter', 'Saturn', 'Uranus', 'Neptune']

    ceres = False
    whfast = False
    part_per_sim = 3

    if not ceres:
        active_list = active_list_v
        mass_particles = {}
        out_dir = "../asteroid_data/sim_data/mv_3/inputs"
    else:
        active_list = active_list_vc
        mass_particles = {4: 5.21e-10}
        out_dir = "../asteroid_data/sim_data/mvc_5/inputs"

    if whfast:
        base_sim = create_whfast_sim(active_list, mass_particles)
    else:
        base_sim = create_mercurious_sim(active_list, mass_particles)

    create_clones(lth_eph_df, out_dir, base_sim, part_per_sim)

    print(f"Completed creating:{active_list}")
