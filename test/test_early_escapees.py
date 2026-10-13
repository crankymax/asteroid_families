import math
from unittest import TestCase

import numpy as np
import pandas as pd

from early_escapees import M_sol, calculate_diameter, sol_mass_from_vol_dens


def sphere_volume(radius):
    return (4 / 3) * math.pi * radius ** 3


class SolMassFromVolDensTest(TestCase):
    def test_unit_mass(self):
        # One solar mass worth of material should give 1.0
        self.assertAlmostEqual(sol_mass_from_vol_dens(M_sol, 1.0), 1.0)
        self.assertAlmostEqual(sol_mass_from_vol_dens(1.0, M_sol), 1.0)

    def test_ceres(self):
        # (1) Ceres (Dawn): mean radius 469.7 km, bulk density 2162 kg/m3, mass 9.3839e20 kg
        volume = sphere_volume(469.7e3)
        mass = sol_mass_from_vol_dens(volume, 2162)
        expected = 9.3839e20 / M_sol
        self.assertAlmostEqual(mass, expected, delta=expected * 0.01)
        self.assertAlmostEqual(mass, 4.718e-10, delta=0.01e-10)

    def test_vesta(self):
        # (4) Vesta (Dawn): mean radius 262.7 km, bulk density 3456 kg/m3, mass 2.59076e20 kg
        volume = sphere_volume(262.7e3)
        mass = sol_mass_from_vol_dens(volume, 3456)
        expected = 2.59076e20 / M_sol
        # Vesta isn't spherical, so allow a slightly looser match
        self.assertAlmostEqual(mass, expected, delta=expected * 0.02)

    def test_series(self):
        # load_family passes pandas columns through
        volumes = pd.Series([sphere_volume(469.7e3), sphere_volume(262.7e3)])
        masses = sol_mass_from_vol_dens(volumes, 2162)
        self.assertEqual(len(masses), 2)
        self.assertAlmostEqual(masses[0], sol_mass_from_vol_dens(volumes[0], 2162))


class CalculateDiameterTest(TestCase):
    def test_ceres(self):
        # (1) Ceres: H = 3.34, p_v = 0.090, Dawn mean diameter 939.4 km
        diameter = calculate_diameter(3.34, 0.090)
        self.assertAlmostEqual(diameter, 951.489e3, delta=1)
        self.assertAlmostEqual(diameter, 939.4e3, delta=939.4e3 * 0.02)

    def test_pallas(self):
        # (2) Pallas: H = 4.12, p_v = 0.155, mean diameter 512 km
        diameter = calculate_diameter(4.12, 0.155)
        self.assertAlmostEqual(diameter, 506.243e3, delta=1)
        self.assertAlmostEqual(diameter, 512e3, delta=512e3 * 0.02)

    def test_default_albedo(self):
        self.assertEqual(calculate_diameter(15.0), calculate_diameter(15.0, 0.0387))

    def test_scaling(self):
        # +5 magnitudes is 1/10 the diameter, 4x the albedo is 1/2 the diameter
        self.assertAlmostEqual(calculate_diameter(8.34, 0.090), calculate_diameter(3.34, 0.090) / 10)
        self.assertAlmostEqual(calculate_diameter(3.34, 0.36), calculate_diameter(3.34, 0.090) / 2)

    def test_array(self):
        diameters = calculate_diameter(np.array([3.34, 4.12]), np.array([0.090, 0.155]))
        np.testing.assert_allclose(diameters, [951.489e3, 506.243e3], rtol=1e-5)
