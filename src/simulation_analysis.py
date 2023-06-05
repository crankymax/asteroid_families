import sys
import glob

import h5py as h5
import numpy as np
import pandas as pd

from scipy import stats
import datetime as datetime

# boundary values
# semi major axis a
a_min = 1.8
a_max = 3.95
# eccentricity e
e_min = 0.0
e_max = 0.34
# inclination i
i_min = 0.0
i_max = 0.55

# indices in the particles array
A = 6
E = 7
I = 8

ind_limits = {A: (a_min, a_max), E: (e_min, e_max), I: (i_min, i_max)}


def simulation_analysis(particle_assignments: str, results_files: str, summary_files: str) -> tuple:
    integration_time = None
    time_taken = []
    escaped_asteroid_data = list()
    particles_simulated = 0
    escaped_asteroids = set()
    particles_assigned = pd.read_hdf(particle_assignments)

    for pv_file in glob.glob(results_files):
        with h5.File(pv_file, 'r') as simulation_log:
            if simulation_log.attrs['simulation'] == 'actives':
                continue
            sim_particles = particles_assigned[particles_assigned['sim_no'] == int(simulation_log.attrs['simulation'])]
            if integration_time and integration_time != simulation_log.attrs['int_length']:
                print(f"Overall integration_time:{integration_time}, "
                      f"this {pv_file}:{simulation_log.attrs['int_length']}")
            else:
                integration_time = simulation_log.attrs['int_length']

            time_taken.append(simulation_log.attrs['clock_time'])

            # Load the arrays
            int_values = simulation_log['integration_time_values'][()]
            part_values = simulation_log['particle_values'][()]
            particles_simulated += part_values.shape[1]

            # Check for particles that are under or over limits
            for param_index, limits in ind_limits.items():
                outside = np.where(((part_values[:, :, param_index] < limits[0]) |
                                    (part_values[:, :, param_index] > limits[1])))
                # Get the particles that have exceeded the limits
                for sim_particle in np.unique(outside[1]):
                    # TODO: Check to see if this is a null particle in the array
                    try:
                        ast_name, vec_list, particle_number = sim_particles.iloc[[sim_particle]][['ast_name',
                                                                        'particle_types', 'particle_number']].values[0]
                    except IndexError:
                        print(f"We got an unallocated particle we'll skip file:{pv_file} particle:{sim_particle} "
                              f"parameter:{param_index}")
                        continue
                    escaped_asteroids.add(f"{ast_name}{''.join(vec_list)}")
                    # we need the first item index for this sim_particle
                    escape_index = (np.where(outside[1] == sim_particle))[0][0]
                    escaped_asteroid_data.append([ast_name, ''.join(vec_list),
                                                  simulation_log.attrs['simulation'],
                                                  particle_number, param_index,
                                                  part_values[outside[0][escape_index], outside[1][escape_index],
                                                  param_index],
                                                  int_values[outside[0][escape_index]]])

    escaped_ast_cols = ['ast_name', 'vectors', 'sim_no', 'particle_number', 'parameter', 'parameter_value',
                        'integration_year']
    escaped_ast_df = pd.DataFrame(escaped_asteroid_data, columns=escaped_ast_cols)
    escaped_ast_df.to_hdf(f"{summary_files}escaped_asteroids.h5", 'escaped_asteroids', mode='w')

    return len(escaped_asteroids), particles_simulated, np.mean(time_taken)


def collect_statistics(part_values):
    all_parts = np.reshape(part_values, [part_values.shape[0] * part_values.shape[1], part_values.shape[2]])
    desc_stats = stats.describe(all_parts, 0)
    deciles = np.percentile(all_parts, [10, 20, 30, 40, 50, 60, 70, 80, 90], 0)
    return desc_stats, deciles


if __name__ == '__main__':
    print(sys.argv)
    clone_assignments = sys.argv[1]
    results_dir = sys.argv[2]
    summary_dir = sys.argv[3]
    escaped_c, simulated_c, avg_runtime = simulation_analysis(clone_assignments, results_dir, summary_dir)
    print(f"Escaped asteroids:{escaped_c} Total simulated {simulated_c} "
          f"\nFraction escaped:{escaped_c/simulated_c}")
    print(f'Average run time {datetime.timedelta(seconds=avg_runtime)}')
