import math
from pathlib import Path
import itertools

import pandas as pd
from horizons_api import retrieve_ephemeris, convert_dy2yr
from parse_afp_family import parse_fam_families
from sim_creation import create_rebound_sims


def add_level(inputs, levels):
    next_level = []
    for lvl in levels:
        for inp in inputs:
            ic = inp.copy()
            ic.append(lvl)
            next_level.append(ic)
    return next_level


asteroids, luthera_family = parse_fam_families()
afp_fam_cols = ['ast_name', 'abs_mag', 'a_P', 'e_P', 'sineI_P', 'family_id']
afp_fam_df = pd.DataFrame(asteroids, columns=afp_fam_cols)
afp_fam_df[['abs_mag', 'a_P', 'e_P', 'sineI_P']] = afp_fam_df[['abs_mag', 'a_P', 'e_P', 'sineI_P']].apply(pd.to_numeric)
afp_fam_df.to_hdf('afp_families.h5', 'afp_families', mode='w')

lth_fam_df = pd.DataFrame(luthera_family, columns=afp_fam_cols)
lth_fam_df[['abs_mag', 'a_P', 'e_P', 'sineI_P']] = lth_fam_df[['abs_mag', 'a_P', 'e_P', 'sineI_P']].apply(pd.to_numeric)
lth_fam_df.to_hdf('luthera_family.h5', 'luthera_family', mode='w')

if not Path('luthera_eph.h5').exists():
    luther_ephemeris = retrieve_ephemeris(luthera_family)
    cols_df = ['ast_name', 'X', 'Y', 'Z', 'VX', 'VY', 'VZ', 'sX', 'sY', 'sZ', 'sVX', 'sVY', 'sVZ']
    lth_eph_df = pd.DataFrame(luther_ephemeris, columns=cols_df)
    convert_dy2yr(lth_eph_df)
    # Save a copy
    lth_eph_df.to_hdf('luthera_eph.h5', 'luthera_eph', mode='w')
else:
    lth_eph_df = pd.read_hdf('luthera_eph.h5', 'luthera_eph')

# produce a new column for each of the clones as values +- sigma
lth_eph_df['Xcp'] = lth_eph_df['X'] * (1 + lth_eph_df['sX'])
lth_eph_df['Ycp'] = lth_eph_df['Y'] * (1 + lth_eph_df['sY'])
lth_eph_df['Zcp'] = lth_eph_df['Z'] * (1 + lth_eph_df['sZ'])
lth_eph_df['Xcm'] = lth_eph_df['X'] * (1 - lth_eph_df['sX'])
lth_eph_df['Ycm'] = lth_eph_df['Y'] * (1 - lth_eph_df['sY'])
lth_eph_df['Zcm'] = lth_eph_df['Z'] * (1 - lth_eph_df['sZ'])
lth_eph_df['VXcp'] = lth_eph_df['VX'] * (1 + lth_eph_df['sVX'])
lth_eph_df['VYcp'] = lth_eph_df['VY'] * (1 + lth_eph_df['sVY'])
lth_eph_df['VZcp'] = lth_eph_df['VZ'] * (1 + lth_eph_df['sVZ'])
lth_eph_df['VXcm'] = lth_eph_df['VX'] * (1 - lth_eph_df['sVX'])
lth_eph_df['VYcm'] = lth_eph_df['VY'] * (1 - lth_eph_df['sVY'])
lth_eph_df['VZcm'] = lth_eph_df['VZ'] * (1 - lth_eph_df['sVZ'])

# create the particles array
ephem_types = [['Xcp', 'Xcm'], ['Ycp', 'Ycm'], ['Zcp', 'Zcm'],
               ['VXcp', 'VXcm'], ['VYcp', 'VYcm'], ['VZcp', 'VZcm']]
# Combine the clones into a list
particles = [list(parts) for parts in itertools.product(*ephem_types)]
# Now add the original particle to the list
particles.append(['X', 'Y', 'Z', 'VX', 'VY', 'VZ'])

# Determine the number of sims
clones_per_sim = 5
sim_number = math.ceil((len(lth_eph_df)*len(particles)) / clones_per_sim)
sim_list = create_rebound_sims(sim_number)

# Set the index to the asteroid name
lth_eph_df = lth_eph_df.set_index('ast_name')
# keep track of which clone is assigned to what simulation
clone_assignments = list()

# assign particles to simulation
for a_n, asteroid in enumerate(lth_eph_df.index):
    for p_n, particle_cols in enumerate(particles):
        particle_vals = lth_eph_df.loc[asteroid][particle_cols]
        assigned_sim_no = ((p_n + (a_n*len(particles))) % sim_number)
        sim = sim_list[assigned_sim_no]
        sim.add(m=0.0, x=particle_vals.iloc[0], y=particle_vals.iloc[1], z=particle_vals.iloc[2],
                vx=particle_vals.iloc[3], vy=particle_vals.iloc[4], vz=particle_vals.iloc[5])
        clone_assignments.append([assigned_sim_no, len(sim.particles), asteroid, particle_cols])

cln_asg_cols = ['sim_no', 'particle_number', 'ast_name', 'particle_types']
cln_asg_df = pd.DataFrame(clone_assignments, columns=cln_asg_cols)
cln_asg_df.to_hdf('clone_assignments.h5', 'clone_assignments', mode='w')

# Write out the simulations
for sim_no, sim in enumerate(sim_list):
    file_name = f'./luthera_sims/luthera_sim_{sim_no:05}.bin'
    sim.save(file_name)
