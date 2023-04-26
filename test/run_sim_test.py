import itertools
import datetime

import pandas as pd
from rebound.interruptible_pool import InterruptiblePool

from rebound_run_sim import run_sim

# TODO: Implement the tests!!

multi_test = False
if multi_test:
    runtime = datetime.today().strftime('%Y%m%d_%H%M')
    ft_params = itertools.product([f'./luthera_sims/luther_sim_{sim_no:05}.bin' for sim_no in range(3, 6)],
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

else:
    # simple test
    print('done!')