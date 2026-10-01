import pandas as pd
import numpy as np

import rebound

from horizons_api import convert_dy2yr, retrieve_ephemeris, eph_cols_df
from pathlib import Path

M_sol: float = 1.989e30


def sol_mass_from_vol_dens(volume, density):
    return (volume*density) / M_sol


def calculate_diameter(abs_mag, p_v=0.0387):
    # Calculate diameter in meters
    return ((1329 * 10 ** (-abs_mag / 5)) * (p_v ** (-0.5))) * 1e3


def load_family(project_dir):
    # We need the rest of the asteroid data to calculate the mass

    fam_proper_h5 = project_dir / 'luther_proper.h5'
    fam_params = pd.read_hdf(fam_proper_h5)
    assert isinstance(fam_params, pd.DataFrame)

    fam_params['irad'] = np.arcsin(fam_params['sineI_P'])
    fam_params['ideg'] = np.degrees(fam_params['irad'])

    p_v = 0.0387
    x_dens_gcm3 = 5.5
    # Calculate diameter (km?)
    fam_params['diam'] = calculate_diameter(fam_params['abs_mag'], p_v)
    # Calculate volume in m3
    fam_params['vol'] = ((4/3) * np.pi * (fam_params['diam']/2) ** 3)

    # Calculate mass in M_sol
    fam_params['mass'] = sol_mass_from_vol_dens(fam_params['vol'], x_dens_gcm3*1e3)

    fam_params = fam_params.set_index('ast_name')
    return fam_params


def simulation_project():
    family_name = 'luthera'
    family_id = '1303'

    project_dir = Path(f'../../{family_name}_prod/')

    # read the family parameters from HDF
    fam_params = load_family(project_dir)

    # read the early escapees from the file
    early_asts = []
    with open(project_dir / 'early_asts.csv', 'r') as ast_file:
        for ast in ast_file:
            early_asts.append(ast.strip())

    early_asts_df = pd.DataFrame(early_asts, columns=['ast_name'])
    print(early_asts_df)
    early_eph = retrieve_ephemeris(early_asts_df)
    print(early_eph)
    early_eph_df = pd.DataFrame(early_eph, columns=eph_cols_df)
    convert_dy2yr(early_eph_df)

    # Construct a base sim
    active_list = ['Sun', 'Venus', 'Earth', 'Mars', 'Jupiter', 'Saturn', 'Uranus', 'Neptune']
    particle_period = 1

    merc_sim = rebound.Simulation()
    y2k_date = 'JD2451544.5'
    merc_sim.add(active_list, date=y2k_date)
    # 1/30 of the innermost planetary period
    merc_sim.dt = merc_sim.particles[particle_period].P / 30
    merc_sim.N_active = len(active_list)
    merc_sim.testparticle_type = 0
    merc_sim.move_to_com()

    merc_sim.integrator = "mercurius"
    # collision and boundary options
    merc_sim.collision = "direct"
    merc_sim.collision_resolve = "merge"
    merc_sim.collision_resolve_keep_sorted = 1
    merc_sim.boundary = "open"
    boxsize = 50.0
    merc_sim.configure_box(boxsize)
    merc_sim.track_energy_offset = 1


if __name__ == '__main__':
    simulation_project()
