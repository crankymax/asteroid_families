from unittest import TestCase
from orbital_log_scan import plot_orbital_escapes, scan_logs

from pathlib import Path

class Test(TestCase):
    asteroid_assignments = "../../asteroid_data/mc_pm6_3/inputs/clone_assignments.h5"
    project_dir = '../../asteroid_data/mc_pm6_3/'
    results_dir = '../../asteroid_data/mc_pm6_3/fawkes_pvals/'

    def test_plot_scan_logs(self):
        scan_logs(self.asteroid_assignments, self.results_dir, self.project_dir)

    def test_plot_orbital_escapes(self):
        plot_orbital_escapes(Path(self.results_dir), Path(self.project_dir))


