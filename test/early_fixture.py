"""
Synthetic early escapees project for testing the path from early_escapees.create_sim_files,
through the rebound_run_sim log layout, to orbital_log_scan and the escape analysis.

Nothing here needs network access or real simulation data. The planets are built from fixed
orbital elements instead of Horizons, and the run logs are written by hand in the same layout
as rebound_run_sim so each test knows exactly which asteroid should escape and when.
"""
import shutil
import tempfile
from pathlib import Path

import h5py as h5
import numpy as np
import pandas as pd
import rebound

import early_escapees
from early_escapees import NEPTUNE_SMA_AU, create_sim_files
from horizons_api import eph_cols_df

# Planets after the Sun, in the order build_base_sim adds them: (name, mass M_sol, a AU)
PLANETS = [('Venus', 2.447e-6, 0.723), ('Earth', 3.003e-6, 1.000), ('Mars', 3.227e-7, 1.524),
           ('Jupiter', 9.543e-4, 5.203), ('Saturn', 2.857e-4, 9.537), ('Uranus', 4.365e-5, 19.19),
           ('Neptune', 5.150e-5, 30.07)]

# Five asteroids in the main belt, sim_count=2 splits them 3/2 over sim_00000 and sim_00001
ASTEROIDS = ['2017EV28', '507863', '2017YC16', '533569', '2010GP5']
AST_A = 2.4
AST_E = 0.1
AST_INC = 0.1
PLANET_E = 0.01
PLANET_INC = 0.01

N_STEPS = 10
INT_LENGTH = 1000.0
# Same layout as rebound_run_sim.initialise_config for short runs
TIMES = np.linspace(1, INT_LENGTH * 2 * np.pi, N_STEPS)
# particle_values columns
SMA = 6
ECC = 7
INC = 8


def offline_base_sim():
    """
    build_base_sim without the Horizons call. Same bodies, names and settings.
    """
    sim = rebound.Simulation()
    sim.add(m=1.0, name='Sun')
    for theta, (name, mass, a) in enumerate(PLANETS):
        sim.add(m=mass, a=a, e=PLANET_E, inc=PLANET_INC, theta=theta, name=name)
    sim.dt = sim.particles[1].P / 30
    sim.integrator = "mercurius"
    sim.collision = "direct"
    sim.collision_resolve = "merge"
    sim.boundary = "open"
    sim.root_size = NEPTUNE_SMA_AU*4
    sim.track_energy_offset = 1
    return sim


def fake_ephemeris():
    """
    Ephemeris DataFrame in the shape simulation_project passes to create_sim_files,
    asteroids on circular orbits at AST_A, in yr/2pi velocity units.
    """
    rows = []
    v = np.sqrt(1 / AST_A)
    for k, ast_name in enumerate(ASTEROIDS):
        theta = 2 * np.pi * k / len(ASTEROIDS)
        rows.append([ast_name, AST_A * np.cos(theta), AST_A * np.sin(theta), 0.0,
                     -v * np.sin(theta), v * np.cos(theta), 0.0] + [0.0] * 6)
    eph_df = pd.DataFrame(rows, columns=eph_cols_df)
    eph_df['mass'] = 1.0e-15
    eph_df['diam'] = 2000.0
    return eph_df


class EarlyProject:
    """
    A temporary early escapees project: inputs from create_sim_files and hand written run logs.
    """
    def __init__(self):
        self.dir = Path(tempfile.mkdtemp(prefix='early_ee_'))
        original = early_escapees.build_base_sim
        early_escapees.build_base_sim = offline_base_sim
        try:
            self.assignments = create_sim_files(fake_ephemeris(), self.dir, sim_count=2)
        finally:
            early_escapees.build_base_sim = original
        self.assignment_file = self.dir / 'inputs' / 'early_assignments.h5'
        self.results_dir = self.dir / 'results'

    def cleanup(self):
        shutil.rmtree(self.dir, ignore_errors=True)

    def sim_asteroids(self, sim_no):
        return self.assignments[self.assignments.sim_no == sim_no].sort_values('particle_number')

    def row(self, ast_name):
        """
        Log row of an asteroid before any removal. N_active == N, so run_sim logs from index 1.
        """
        asg = self.assignments.set_index('ast_name')
        return int(asg.loc[ast_name, 'particle_number']) - 1

    def baseline_log(self, sim_no):
        """
        Names and values for a run where nothing escapes. Planets at their real a (Venus and
        Jupiter onwards are outside the scan bounds), asteroids inside the bounds.
        :return: (particle_names[time, row], particle_values[time, row, 11])
        """
        sim_asts = self.sim_asteroids(sim_no)
        n_rows = len(PLANETS) + len(sim_asts)
        names = [name for name, _, _ in PLANETS] + [None] * len(sim_asts)
        values = np.zeros((N_STEPS, n_rows, 11))
        for row, (_, _, a) in enumerate(PLANETS):
            values[:, row, SMA] = a
            values[:, row, ECC] = PLANET_E
            values[:, row, INC] = PLANET_INC
        for ast in sim_asts.itertuples():
            row = ast.particle_number - 1
            names[row] = ast.ast_name
            values[:, row, SMA] = AST_A
            values[:, row, ECC] = AST_E
            values[:, row, INC] = AST_INC
        name_len = max(len(n) for n in names)
        name_log = np.array([[n.encode('utf-8') for n in names]] * N_STEPS, dtype=f'S{name_len}')
        return name_log, values

    def write_log(self, sim_no, names, values):
        """
        Write a completed run log in the rebound_run_sim.store_config layout
        """
        with h5.File(self.results_dir / f'pvals_{sim_no:05}.h5', 'w') as run_log:
            run_log.attrs['simulation'] = f'{sim_no:05}'
            run_log.attrs['int_length'] = INT_LENGTH
            run_log.attrs['start_index'] = 0
            run_log.attrs['clock_time'] = 1.0
            run_log.create_dataset('integration_time_values', data=TIMES)
            run_log.create_dataset('sim_energy_values', data=np.zeros(N_STEPS))
            run_log.create_dataset('particle_values', data=values)
            run_log.create_dataset('particle_names', data=names)

    def write_baseline_logs(self):
        for sim_no in self.assignments.sim_no.unique():
            self.write_log(int(sim_no), *self.baseline_log(int(sim_no)))

    def escaped(self):
        return pd.read_hdf(self.dir / 'escaped_asteroids.h5', key='escaped_asteroids')
