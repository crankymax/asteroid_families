import unittest

import itertools
import datetime

import pandas as pd

from rebound_run_sim import sim_particle_system


class TestSimulation(unittest.TestCase):
    def test_one_shot(self):
        inp_dir = '../../asteroid_data/sim_data/mvc_3/'
        sim_no = 0
        run_length = 1.0e6
        max_walltime = 1
        sim_particle_system(inp_dir, sim_no, run_length, max_walltime)

    def notest_simple(self):
        ft_params = itertools.product([f'./luthera_sims/sim_{sim_no:05}.bin' for sim_no in range(3, 6)],
                                      [1.e6, 2.5e6, 5.e6, 7.5e6, 1.e7])

        params = list()
        for ptup in ft_params:
            ft_list = list(ptup)
            ft_list.append(runtime)
            params.append(ft_list)

        pool = InterruptiblePool(processes=3)
        res = pool.map(run_sim, params)
        results_df = pd.DataFrame.from_dict(res)
        results_df.to_hdf(f"./run_logs/results_{runtime}.h5", 'results', mode='w')


if __name__ == '__main__':
    unittest.main()
