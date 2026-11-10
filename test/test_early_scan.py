"""
Checks that the asteroids written by early_escapees.create_sim_files are the asteroids that
orbital_log_scan.scan_logs reports from rebound_run_sim style logs.

cd test && PYTHONPATH=../src python -m unittest test_early_scan
"""
from multiprocessing import Pool
from unittest import TestCase

import numpy as np
import rebound

from orbital_log_scan import scan_logs
from early_fixture import (AST_A, ASTEROIDS, PLANETS, SMA, TIMES, EarlyProject)


def sim_particle_names(sim_file):
    return [p.name for p in rebound.Simulation(str(sim_file)).particles]


class EarlyFixtureTest(TestCase):
    """
    The fixture inputs come from the real create_sim_files, so check they have the layout
    the hand written logs assume.
    """
    @classmethod
    def setUpClass(cls):
        cls.project = EarlyProject()

    @classmethod
    def tearDownClass(cls):
        cls.project.cleanup()

    def test_assignments(self):
        asg = self.project.assignments
        self.assertEqual(sorted(asg.ast_name), sorted(ASTEROIDS))
        self.assertEqual(asg.groupby('sim_no').size().to_dict(), {0: 3, 1: 2})
        for sim_no in (0, 1):
            self.assertEqual(list(self.project.sim_asteroids(sim_no).particle_number),
                             list(range(len(PLANETS) + 1, len(PLANETS) + 1 + (3 - sim_no))))

    def test_sim_files_match_assignments(self):
        sim_files = [self.project.dir / 'inputs' / f'sim_{sim_no:05}.bin' for sim_no in (0, 1)]
        # One sim per process, REBOUND 5 can corrupt particle names when a process loads several
        with Pool(processes=2, maxtasksperchild=1) as pool:
            names = pool.map(sim_particle_names, sim_files)
        for ast in self.project.assignments.itertuples():
            sim_names = names[ast.sim_no]
            self.assertEqual(sim_names[:len(PLANETS) + 1], ['Sun'] + [name for name, _, _ in PLANETS])
            self.assertEqual(sim_names[ast.particle_number], ast.ast_name)


class ScanEarlyLogsTest(TestCase):
    def setUp(self):
        self.project = EarlyProject()
        self.project.write_baseline_logs()

    def tearDown(self):
        self.project.cleanup()

    def scan(self):
        scan_logs(self.project.assignment_file, self.project.results_dir, self.project.dir)
        return self.project.escaped()

    def set_a(self, sim_no, ast_name, a, from_step):
        names, values = self.project.baseline_log(sim_no)
        values[from_step:, self.project.row(ast_name), SMA] = a
        self.project.write_log(sim_no, names, values)

    def test_baseline_nothing_escapes(self):
        # Planets are outside the bounds, the asteroids aren't
        escaped = self.scan()
        self.assertEqual(len(escaped), 0)

    def test_middle_asteroid_escape(self):
        # Only the middle of the three asteroids in sim 0 crosses a_max
        middle = self.project.sim_asteroids(0).iloc[1].ast_name
        self.set_a(0, middle, 4.5, from_step=4)

        escaped = self.scan()

        self.assertEqual(list(escaped.ast_name), [middle])
        esc = escaped.iloc[0]
        self.assertEqual(esc.parameter, SMA)
        self.assertEqual(esc.integration_year, TIMES[4])
        self.assertEqual(esc.parameter_value, 4.5)
        self.assertEqual(esc.min_val, AST_A)
        self.assertEqual(esc.max_val, 4.5)

    def test_last_asteroid_escape_named_correctly(self):
        last = self.project.sim_asteroids(0).iloc[-1].ast_name
        self.set_a(0, last, 4.5, from_step=4)

        escaped = self.scan()

        self.assertEqual(list(escaped.ast_name), [last])
        self.assertEqual(escaped.iloc[0].particle_number,
                         self.project.sim_asteroids(0).iloc[-1].particle_number)

    def test_escape_values_are_the_asteroids(self):
        # The first asteroid drops inside a_min. The reported values must be its own, not a planet's
        first = self.project.sim_asteroids(0).iloc[0].ast_name
        self.set_a(0, first, 1.5, from_step=3)

        escaped = self.scan()

        self.assertEqual(list(escaped.ast_name), [first])
        esc = escaped.iloc[0]
        self.assertEqual(esc.parameter_value, 1.5)
        self.assertEqual(esc.integration_year, TIMES[3])
        self.assertEqual(esc.min_val, 1.5)
        self.assertEqual(esc.max_val, AST_A)
        planet_a = [a for _, _, a in PLANETS]
        self.assertNotIn(esc.min_val, planet_a)
        self.assertNotIn(esc.max_val, planet_a)

    def test_planets_never_reported(self):
        # Every asteroid escapes, the planets are outside the bounds throughout
        for sim_no in (0, 1):
            names, values = self.project.baseline_log(sim_no)
            for ast_name in self.project.sim_asteroids(sim_no).ast_name:
                values[5:, self.project.row(ast_name), SMA] = 4.5
            self.project.write_log(sim_no, names, values)

        escaped = self.scan()

        self.assertEqual(sorted(escaped.ast_name.unique()), sorted(ASTEROIDS))
        self.assertTrue((escaped.particle_number > len(PLANETS)).all())
        np.testing.assert_array_equal(escaped.min_val, AST_A)
        np.testing.assert_array_equal(escaped.max_val, 4.5)

    def test_removed_particle_rows_shift(self):
        # The first asteroid crosses a_max then leaves the sim. The other two move up a row
        # and the last row is empty, which must not be read as an escape.
        sim_asts = self.project.sim_asteroids(0)
        first, second, third = sim_asts.ast_name
        first_row = self.project.row(first)
        removed_step = 6

        names, values = self.project.baseline_log(0)
        values[removed_step - 1, first_row, SMA] = 6.0
        names[removed_step:, first_row:-1] = names[removed_step:, first_row + 1:]
        values[removed_step:, first_row:-1] = values[removed_step:, first_row + 1:]
        names[removed_step:, -1] = b''
        values[removed_step:, -1] = 0.0
        self.project.write_log(0, names, values)

        escaped = self.scan()

        self.assertNotIn(second, set(escaped.ast_name))
        self.assertNotIn(third, set(escaped.ast_name))
        first_esc = escaped[(escaped.ast_name == first) & (escaped.parameter == SMA)]
        self.assertEqual(len(first_esc), 1)
        self.assertEqual(first_esc.iloc[0].integration_year, TIMES[removed_step - 1])
        self.assertEqual(first_esc.iloc[0].max_val, 6.0)
        # The zeros after removal aren't part of the asteroid's orbit
        self.assertEqual(first_esc.iloc[0].min_val, AST_A)

    def test_unfinished_run_not_escaped(self):
        # Steps after the walltime stop are still empty, they aren't removed particles
        names, values = self.project.baseline_log(0)
        names[7:] = b''
        values[7:] = 0.0
        self.project.write_log(0, names, values)

        escaped = self.scan()

        self.assertEqual(len(escaped), 0)

    def test_unnamed_particles_raise(self):
        names, values = self.project.baseline_log(0)
        names[:, len(PLANETS):] = b''
        self.project.write_log(0, names, values)

        with self.assertRaises(ValueError):
            self.scan()
