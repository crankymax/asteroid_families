import math
from pathlib import Path
import itertools

import pandas as pd
from horizons_api import retrieve_ephemeris, convert_dy2yr
from parse_afp_family import parse_fam_families
from sim_creation import create_rebound_sims
from rebound_run_sim import run_sim
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
afp_fam_df.to_pickle('afp_families.pkl')

lth_fam_df = pd.DataFrame(luthera_family, columns=afp_fam_cols)
lth_fam_df[['abs_mag', 'a_P', 'e_P', 'sineI_P']] = lth_fam_df[['abs_mag', 'a_P', 'e_P', 'sineI_P']].apply(pd.to_numeric)
lth_fam_df.to_pickle('lth_family.pkl')

if not Path('luthera_eph.pkl').exists():
    luther_ephemeris = retrieve_ephemeris(luthera_family)
    cols_df = ['ast_name', 'X', 'Y', 'Z', 'VX', 'VY', 'VZ', 'sX', 'sY', 'sZ', 'sVX', 'sVY', 'sVZ']
    lth_eph_df = pd.DataFrame(luther_ephemeris, columns=cols_df)
    convert_dy2yr(lth_eph_df)
    # Save a copy
    lth_eph_df.to_pickle('luthera_eph.pkl')
else:
    lth_eph_df = pd.read_pickle('luthera_eph.pkl')

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
sim_number = math.ceil((len(lth_eph_df)*len(particles)) / 13.0)
sim_list = create_rebound_sims(sim_number)

# now we need ~4k files with 13 particles in each without overlapping pos values
lth_eph_df = lth_eph_df.set_index('ast_name')
clone_assignments = list()

# assign particles to simulation
for a_n, asteroid in enumerate(lth_eph_df.index):
    for p_n, particle_cols in enumerate(particles):
        particle_vals = lth_eph_df.loc[asteroid][particle_cols]
        assigned_sim_no = ((p_n + (a_n*len(particles))) % sim_number)
        sim = sim_list[assigned_sim_no]
        sim.add(m=0.0, x=particle_vals.iloc[0], y=particle_vals.iloc[1], z=particle_vals[2],
                vx=particle_vals.iloc[3], vy=particle_vals.iloc[4], vz=particle_vals[5])
        clone_assignments.append([assigned_sim_no, len(sim.particles), asteroid, particle_cols])

# Write out the simulations
for sim_no, sim in enumerate(sim_list):
    file_name = f'./luthera_sims/luther_sim_{sim_no:04}.bin'
    sim.save(file_name)

