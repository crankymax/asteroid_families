"""
Checks the escape analysis puts each asteroid's escapes on that asteroid's family row.

cd test && PYTHONPATH=../src python -m unittest test_escape_analysis
"""
from unittest import TestCase

import numpy as np
import pandas as pd

from escape_analysis import attach_escapes, attach_sma_extremes, escape_years, mean_escape_by_asteroid

ESC_COLS = ['ast_name', 'vectors', 'sim_no', 'particle_number', 'parameter', 'parameter_value',
            'integration_year', 'min_val', 'max_val']


def family():
    # Shaped like luth_fam in the notebook, indexed by ast_name
    return pd.DataFrame({'ast_name': ['2017EV28', '507863', '2017YC16'],
                         'a_P': [2.40, 2.41, 2.42],
                         'e_P': [0.10, 0.11, 0.12],
                         'sineI_P': [0.10, 0.10, 0.10]}).set_index('ast_name')


def escaped():
    # Shaped like orbital_log_scan's escaped_asteroids, which has a plain RangeIndex.
    # 2017EV28 goes inside a_min at 1e8 yr, 507863 goes outside a_max at 3e8 yr,
    # 2017EV28 also has an eccentricity escape, which isn't an SMA escape.
    two_pi = 2 * np.pi
    return pd.DataFrame([
        ['2017EV28', 'XYZVXVYVZ', '00000', 8, 7, 0.40, 0.5e8 * two_pi, 0.10, 0.40],
        ['2017EV28', 'XYZVXVYVZ', '00000', 8, 6, 1.50, 1.0e8 * two_pi, 1.50, 2.40],
        ['507863', 'XYZVXVYVZ', '00000', 9, 6, 4.50, 3.0e8 * two_pi, 2.40, 4.50],
    ], columns=ESC_COLS)


class EscapeAnalysisTest(TestCase):
    def test_escape_year_on_asteroid_row(self):
        mean_escape = mean_escape_by_asteroid(escape_years(escaped()))
        fam = attach_escapes(family(), mean_escape)

        self.assertAlmostEqual(fam.loc['2017EV28', 'integration_year'], 1.0e8)
        self.assertAlmostEqual(fam.loc['507863', 'integration_year'], 3.0e8)
        self.assertEqual(fam.loc['2017YC16', 'integration_year'], 0)
        self.assertEqual(list(fam.graph_symbol), ['o', 'o', '.'])

    def test_one_row_per_asteroid(self):
        mean_escape = mean_escape_by_asteroid(escape_years(escaped()))

        self.assertEqual(sorted(mean_escape.index), ['2017EV28', '507863'])
        self.assertEqual(mean_escape.loc['2017EV28', 'vec_count'], 1)

    def test_sma_extremes_on_asteroid_row(self):
        fam = attach_sma_extremes(family(), escaped())

        self.assertEqual(fam.loc['2017EV28', 'mean_min_val'], 1.50)
        self.assertEqual(fam.loc['507863', 'mean_max_val'], 4.50)
        # inner, outer, stable
        self.assertEqual(list(fam.last_sma), [1, 2, 0])
