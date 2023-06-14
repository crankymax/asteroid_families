from pathlib import Path
import itertools
from rebound.interruptible_pool import InterruptiblePool
import unittest

from rebound_run_sim import run_sim, prun_sim


class TestSimulation(unittest.TestCase):
    inp_dir = '../../asteroid_data/sim_data/mvc_3/'

    def setUp(self):
        # Setup the test directory
        # Remove any files in the results directory
        results_dir = Path(self.inp_dir).joinpath('results')
        for path in results_dir.glob("*"):
            if path.is_file():
                path.unlink()

    def tearDown(self):
        results_dir = Path(self.inp_dir).joinpath('results')
        for path in results_dir.glob("*"):
            if path.is_file():
                path.unlink()

    def test_one_shot(self):
        sim_no = '0'
        run_length = 1.0e6
        max_walltime = 1.0
        stop_index = run_sim(self.inp_dir, sim_no, run_length, max_walltime)
        assert stop_index

    def test_two_shots(self):
        sim_no = '0'
        run_length = 1.0e6
        max_walltime = 100 * (1/3600)
        stop_index = run_sim(self.inp_dir, sim_no, run_length, max_walltime)
        assert not stop_index
        stop_index = run_sim(self.inp_dir, sim_no, run_length, max_walltime)
        assert stop_index

    def test_one_shot_actives(self):
        run_length = 1.0e6
        max_walltime = 1.0
        stop_index = run_sim(self.inp_dir, 'actives', run_length, max_walltime)
        assert stop_index

    def test_two_shots_actives(self):
        run_length = 1.0e6
        max_walltime = 100 * (1/3600)
        stop_index = run_sim(self.inp_dir, 'actives', run_length, max_walltime)
        assert not stop_index
        stop_index = run_sim(self.inp_dir, 'actives', run_length, max_walltime)
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


if __name__ == '__main__':
    unittest.main()
