import itertools
from pathlib import Path

from multiprocessing import Pool
from sys import argv

import pandas as pd
import numpy as np

import rebound

from horizons_api import convert_dy2yr, retrieve_ephemeris, eph_cols_df
from rebound_run_sim import prun_sim

M_sol: float = 1.989e30
NEPTUNE_SMA_AU: float = 30.0
AU_M: float = 1.495978707e11
p_v = 0.0387
x_dens_gcm3 = 3.2

family_name = 'luthera_ee'


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

    # Calculate diameter (km?)
    fam_params['diam'] = calculate_diameter(fam_params['abs_mag'], p_v)
    # Calculate volume in m3
    fam_params['vol'] = ((4/3) * np.pi * (fam_params['diam']/2) ** 3)

    # Calculate mass in M_sol
    fam_params['mass'] = sol_mass_from_vol_dens(fam_params['vol'], x_dens_gcm3*1e3)

    fam_params = fam_params.set_index('ast_name')
    return fam_params


def build_base_sim():
    # Construct a base sim
    active_list = ['Sun', 'Venus', 'Earth', 'Mars', 'Jupiter', 'Saturn', 'Uranus', 'Neptune']
    particle_period = 1

    merc_sim = rebound.Simulation()
    y2k_date = 'JD2451544.5'
    merc_sim.add(active_list, date=y2k_date)
    # Name the bodies so they can be found in the run logs (Horizons names Jupiter 'Jupiter Barycenter' etc.)
    for name, particle in zip(active_list, merc_sim.particles):
        particle.name = name
    # 1/30 of the innermost planetary period
    merc_sim.dt = merc_sim.particles[particle_period].P / 30

    merc_sim.integrator = "mercurius"
    # collision and boundary options
    merc_sim.collision = "direct"
    merc_sim.collision_resolve = "merge"
    merc_sim.boundary = "open"
    # root_size is the full width, so this removes particles beyond 2x Neptune's distance
    merc_sim.root_size = NEPTUNE_SMA_AU*4
    merc_sim.track_energy_offset = 1

    return merc_sim


def build_sim_file(base_sim: rebound.Simulation, asteroids_df: pd.DataFrame):
    """
    Copy the base sim and add the asteroids as active (massive) particles
    :param base_sim: planets only REBOUND simulation
    :param asteroids_df: ephemeris with mass (M_sol) and diam (m) columns
    :return: REBOUND simulation and the particle number of each asteroid.
             Each asteroid is named by ast_name, i.e. sim.particles[ast_name]
    """
    sim = base_sim.copy()
    particle_numbers = []
    for ast in asteroids_df.itertuples():
        sim.add(m=ast.mass, r=(ast.diam / 2) / AU_M,
                x=ast.X, y=ast.Y, z=ast.Z, vx=ast.VX, vy=ast.VY, vz=ast.VZ, name=str(ast.ast_name))
        particle_numbers.append(len(sim.particles) - 1)

    # Everything is active, so the asteroids perturb the planets and each other
    sim.N_active = len(sim.particles)
    sim.move_to_com()
    return sim, particle_numbers


def create_sim_files(asteroids_df: pd.DataFrame, project_dir: Path, sim_count=9):
    """
    Spread the asteroids over sim_count simulation files in project_dir/inputs and
    record the assignments in inputs/early_assignments.h5
    """
    input_dir = project_dir / 'inputs'
    input_dir.mkdir(exist_ok=True)
    (project_dir / 'results').mkdir(exist_ok=True)

    base_sim = build_base_sim()
    base_sim.save_to_file(str(input_dir / 'sim_actives.bin'))

    assignments = []
    for sim_no, rows in enumerate(np.array_split(np.arange(len(asteroids_df)), sim_count)):
        sim_asts = asteroids_df.iloc[rows]
        sim, particle_numbers = build_sim_file(base_sim, sim_asts)
        sim.save_to_file(str(input_dir / f'sim_{sim_no:05}.bin'))
        for ast_name, particle_number in zip(sim_asts['ast_name'], particle_numbers):
            assignments.append([ast_name, ['X', 'Y', 'Z', 'VX', 'VY', 'VZ'], sim_no, particle_number])

    asg_df = pd.DataFrame(assignments, columns=['ast_name', 'particle_types', 'sim_no', 'particle_number'])
    asg_df.to_hdf((input_dir / 'early_assignments.h5').resolve(), key='early_assignments', mode='w')
    return asg_df


def simulation_project():
    family_name = 'luthera_ee'

    project_dir = Path(f'../../{family_name}/')

    # read the family parameters from HDF
    fam_params = load_family(project_dir)

    # read the early escapees from the file
    with open(project_dir / 'early_asts.csv', 'r') as ast_file:
        # Read each escapee
        early_asts = [x.strip() for x in ast_file.readlines()]
        early_fam_df = fam_params.loc[early_asts]

    early_asts_df = pd.DataFrame(early_asts, columns=['ast_name'])
    print(early_asts_df)
    early_eph = retrieve_ephemeris(early_asts_df)
    early_eph_df = pd.DataFrame(early_eph, columns=eph_cols_df)
    print(early_eph_df)
    convert_dy2yr(early_eph_df)

    # Attach the mass and diameter to the ephemeris
    early_eph_df = early_eph_df.join(early_fam_df[['mass', 'diam']], on='ast_name')
    missing = set(early_asts) - set(early_eph_df['ast_name'])
    if missing:
        print(f'No ephemeris for {sorted(missing)}')

    asg_df = create_sim_files(early_eph_df, project_dir)
    print(asg_df.groupby('sim_no').size())


def run_early_asts():
    project_dir = Path(f'../../{family_name}/')

    params = list(itertools.product([str(project_dir)],
                                    [str(sim_no) for sim_no in range(9)],
                                    [5.0e8],
                                    [168]))

    # One sim per process, REBOUND 5 can corrupt particle names when a process loads several
    with Pool(processes=9, maxtasksperchild=1) as pool:
        res = pool.map(prun_sim, params)
    print(res)


if __name__ == '__main__':
    if len(argv) > 1 and argv[1] == 'run':
        run_early_asts()
    else:
        simulation_project()
