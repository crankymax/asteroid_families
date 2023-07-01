import math
from pathlib import Path
import shutil
import itertools
from rebound.interruptible_pool import InterruptiblePool
import unittest

import numpy as np
import h5py as h5
import rebound
from rebound_run_sim import run_sim, prun_sim


class TestSimulation(unittest.TestCase):
    proj_dir = '../../asteroid_data/sim_data/mvc_3/'

    def setUp(self):
        # Set up the test directory
        # Remove any files in the results directory
        results_dir = Path(self.proj_dir).joinpath('results')
        for path in results_dir.glob("*"):
            if path.is_file():
                path.unlink()

    def tearDown(self):
        results_dir = Path(self.proj_dir).joinpath('results')
        for path in results_dir.glob("*"):
            if path.is_file():
                path.unlink()

    def test_one_shot(self):
        sim_no = '0'
        run_length = 1.0e6
        max_walltime = 1.0
        stop_index = run_sim(self.proj_dir, sim_no, run_length, max_walltime)
        assert stop_index

    def test_two_shots(self):
        sim_no = '0'
        run_length = 1.0e6
        max_walltime = 100 * (1/3600)
        stop_index = run_sim(self.proj_dir, sim_no, run_length, max_walltime)
        assert not stop_index
        stop_index = run_sim(self.proj_dir, sim_no, run_length, max_walltime)
        assert stop_index

    def test_one_shot_actives(self):
        run_length = 1.0e6
        max_walltime = 1.0
        stop_index = run_sim(self.proj_dir, 'actives', run_length, max_walltime)
        assert stop_index

    def test_two_shots_actives(self):
        run_length = 1.0e6
        max_walltime = 100 * (1/3600)
        stop_index = run_sim(self.proj_dir, 'actives', run_length, max_walltime)
        assert not stop_index
        stop_index = run_sim(self.proj_dir, 'actives', run_length, max_walltime)
        assert stop_index

    def test_timings(self):
        params = list(itertools.product(['../../asteroid_data/sim_data/m_pm6_3/',
                                         '../../asteroid_data/sim_data/mc_pm6_3/'],
                                        [str(sim_no) for sim_no in range(6)],
                                        [1.e6, 2.5e6, 5.e6, 7.5e6, 1.e7],
                                        [2]))
        pool = InterruptiblePool(processes=3)
        res = pool.map(prun_sim, params)
        print(res)

    def test_restart_2byIntTime(self):
        # Run a simulation for 1.e6 and then run it again to 2.e6
        # We need to compare it with a single 2.e6
        stop_index = run_sim(self.proj_dir, '0', 2.5e5, 1)
        assert stop_index, "Run didn't finish"
        # move the output files to preserve and compare with 2.e5
        # move log file
        results_dir = Path(self.proj_dir).joinpath('results')
        for path in results_dir.glob("*"):
            if path.name == 'pvals_00000.h5':
                pvals_1g = path.rename(path.parent.joinpath(path.stem + '_1g' + path.suffix))
            elif path.name == 'sim_00000_fin.bin':
                sim_fin_1g = path.rename(path.parent.joinpath(path.stem + '_1g' + path.suffix))

        stop_index = run_sim(self.proj_dir, '0', 1.e5, 1)
        assert stop_index, "Run didn't finish"
        # copy the part vals
        for path in results_dir.glob("*"):
            if path.name == 'pvals_00000.h5':
                pvals_2g_a = shutil.copy(path, path.parent.joinpath(path.stem + '_cpy' + path.suffix))
            elif path.name == 'sim_00000_fin.bin':
                sim_fin_2g_a = shutil.copy(path, path.parent.joinpath(path.stem + '_cpy' + path.suffix))

        stop_index = run_sim(self.proj_dir, '0', 2.5e5, 1)
        assert stop_index, "Run didn't finish"
        for path in results_dir.glob("*"):
            if path.name == 'pvals_00000.h5':
               pvals_extend = path
            elif path.name == 'sim_00000_fin.bin':
               sim_fin_extend = path
        # now compare the files :O
        pvals_1g_h5 = h5.File(pvals_1g, 'r')
        pvals_2g_a_h5 = h5.File(pvals_2g_a, 'r')
        pvals_extend_h5 = h5.File(pvals_extend, 'r')
        time_values_1g = pvals_1g_h5['integration_time_values'][()]
        part_values_1g = pvals_1g_h5['particle_values'][()]
        time_values_2g_a = pvals_2g_a_h5['integration_time_values'][()]
        part_values_2g_a = pvals_2g_a_h5['particle_values'][()]
        time_values_2g = pvals_extend_h5['integration_time_values'][()]
        part_values_2g = pvals_extend_h5['particle_values'][()]
        assert (np.var(time_values_2g[1:]-time_values_2g[:-1]) < 0.01), "Too much variance in restarted time steps"
        diff_1_2 = time_values_2g[-1]-time_values_1g[-1]
        assert (abs(diff_1_2) < (np.mean(time_values_2g[1:]-time_values_2g[:-1]))), "Difference between restarted " \
                                                                                    "greater than time step"
        sim_1g = rebound.Simulation(str(sim_fin_1g.resolve()))
        sim_2g = rebound.Simulation(str(sim_fin_extend.resolve()))
        part_1g = sim_1g.particles
        part_2g = sim_2g.particles
        assert math.isclose(part_1g[9].a, part_2g[9].a, rel_tol=1.0e-1), \
             f"Particle 9 has an issue {part_1g[9].a}:{part_2g[9].a}"
        assert math.isclose(part_1g[10].a, part_2g[10].a, rel_tol=1.0e-1), \
            f"Particle 10 has an issue {part_1g[10].a}:{part_2g[10].a}"
        assert math.isclose(part_1g[11].a, part_2g[11].a, rel_tol=1.0e-1), \
            f"Particle 11 has an issue {part_1g[11].a}:{part_2g[11].a}"


if __name__ == '__main__':
    unittest.main()
