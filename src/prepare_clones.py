import math
import itertools

import pandas as pd
from sim_creation import copy_sim


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
    lth_eph_ext_df = asteroid_ephem.set_index('ast_name')
    # keep track of which clone is assigned to what simulation
    clone_assignments = list()

    # Determine the number of sims
    sim_numbers = math.ceil((len(asteroid_ephem) * len(particles)) / clones_per_sim)
    # generate the sims
    sim_list = copy_sim(sim_file, sim_numbers)
    # Create a copy of the sim_file to capture the family asteroids for analysis
    family_sim = sim_file.copy()
    family_assignments = list()

    # assign particles to simulation
    for a_n, asteroid in enumerate(lth_eph_ext_df.index):
        particle_vals = lth_eph_ext_df.loc[asteroid][['X', 'Y', 'Z', 'VX', 'VY', 'VZ']]
        family_sim.add(m=0.0, x=particle_vals.iloc[0], y=particle_vals.iloc[1], z=particle_vals.iloc[2],
                       vx=particle_vals.iloc[3], vy=particle_vals.iloc[4], vz=particle_vals.iloc[5])
        family_assignments.append([asteroid, len(family_sim.particles)])
        for p_n, particle_cols in enumerate(particles):
            particle_vals = lth_eph_ext_df.loc[asteroid][particle_cols]
            assigned_sim_no = ((p_n + (a_n * len(particles))) % sim_numbers)
            sim = sim_list[assigned_sim_no]
            sim.add(m=0.0, x=particle_vals.iloc[0], y=particle_vals.iloc[1], z=particle_vals.iloc[2],
                    vx=particle_vals.iloc[3], vy=particle_vals.iloc[4], vz=particle_vals.iloc[5])
            clone_assignments.append([asteroid, particle_cols, assigned_sim_no, len(sim.particles)])

    cln_asg_cols = ['ast_name', 'particle_types', 'sim_no', 'particle_number']
    cln_asg_df = pd.DataFrame(clone_assignments, columns=cln_asg_cols)
    cln_asg_df.to_hdf(f'{output_dir}/clone_assignments.h5', 'clone_assignments', mode='w')

    # Write out the simulations
    for sim_no, sim in enumerate(sim_list):
        file_name = f'{output_dir}/sim_{sim_no:05}.bin'
        sim.save(file_name)

    # Save the family sim
    family_sim.save(f'{output_dir}/family_sim.bin')
    # Save family asteroid particle assignments
    fam_asg_cols = ['ast_name', 'particle_number']
    fam_asg_df = pd.DataFrame(family_assignments, columns=fam_asg_cols)
    fam_asg_df.to_hdf(f'{output_dir}/family_assignments.h5', 'family_assignments', mode='w')

    # Save the actives only sim. This is the simulation file without the test particles.
    sim_file.save(f'{output_dir}/sim_actives.bin')

