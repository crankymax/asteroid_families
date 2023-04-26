import sys
import glob

import h5py as h5
import numpy as np
import pandas as pd

from scipy import stats

# boundary values
# semi major axis a
a_min = 2.0
a_max = 4.0
# eccentricity e
e_min = 0.0
e_max = 0.3
# inclination i
i_min = -0.4
i_max = 0.4

# indices in the particles array
A = 6
E = 7
I = 8

ind_limits = {A: (a_min, a_max), E: (e_min, e_max), I: (i_min, i_max)}


def simulation_analysis(clone_assignments, results_files, active_bodies=8):
    integration_time = None
    time_taken = []
    escaped_asteroids = dict()
    particles_simulated = 0

    particles_assigned = pd.read_hdf(clone_assignments)

    for pv_file in glob.glob(results_files):
        with h5.File(pv_file, 'r') as simulation_log:
            sim_particles = particles_assigned[particles_assigned['sim_no'] == simulation_log.attrs['simulation']]
            if integration_time and integration_time != simulation_log.attrs['int_length']:
                print(
                    f"Overall integration_time:{integration_time}, this {fpv_file}:{simulation_log.attrs['int_length']}")
            else:
                integration_time = simulation_log.attrs['int_length']

            time_taken.append(simulation_log.attrs['clock_time'])

            # Load the arrays
            int_values = simulation_log['integration_time_values'][()]
            part_values = simulation_log['test_particle_values'][()]
            particles_simulated += part_values.shape[1]

            # collect_statistics(part_values)

            # Check for particles that are under or over limits
            for param_index, limits in ind_limits.items():
                outside = np.where(((part_values[:, :, param_index] < limits[0]) |
                                    (part_values[:, :, param_index] > limits[1])))
                # Get the particles that have exceeded the limits
                for sim_particle in np.unique(outside[1]):
                    # TODO: Check to see if this is a null particle in the array
                    try:
                        ast_name, vec_list = sim_particles[sim_particles['particle_number'] ==
                                                           (sim_particle + active_bodies + 1)][['ast_name', 'particle_types']].values[0]
                    except IndexError:
                        print(f"We got an unallocated particle we'll skip file:{pv_file} particle:{sim_particle} "
                              f"parameter:{param_index}")
                        continue

                    part_id = f"{ast_name}_{''.join(vec_list)}"
                    if part_id not in escaped_asteroids:
                        escaped_asteroids[part_id] = list()
                    escaped_asteroids[part_id].append(tuple([param_index]))

    return escaped_asteroids, particles_simulated, np.mean(time_taken)


def collect_statistics(part_values):
    all_parts = np.reshape(part_values, [part_values.shape[0] * part_values.shape[1], part_values.shape[2]])
    desc_stats = stats.describe(all_parts, 0)
    deciles = np.percentile(all_parts, [10, 20, 30, 40, 50, 60, 70, 80, 90], 0)
    return desc_stats, deciles


if __name__ == '__main__':
    print(sys.argv)
    clone_assignments = sys.argv[1]
    results_dir = sys.argv[2]
    escaped_c, simulated_c, avg_runtime = simulation_analysis(clone_assignments,
                                                 results_dir)
    print(f"Escaped asteroids:{len(escaped_c)} Total simulated {simulated_c} "
          f"\nFraction escaped:{len(escaped_c) / simulated_c}")
    print(f'Average run time {avg_runtime}')
