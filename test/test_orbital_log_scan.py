from unittest import TestCase
from orbital_log_scan import plot_orbital_escapes

class Test(TestCase):
    def test_plot_orbital_escapes(self):
        sim_dir = '../../asteroid_data/mc_pm6_3'
        plot_orbital_escapes(sim_dir)


