import sys
from pathlib import Path

import h5py as h5
import numpy as np
import pandas as pd

from scipy import stats
import datetime as datetime

import matplotlib as mpl
import matplotlib.pyplot as plt
mpl.use('Agg')

# boundary values
# semi major axis a
a_min = 1.8
a_max = 3.95
# eccentricity e
e_min = 0.0
e_max = 0.34
# inclination i (radians)
i_min = 0.0
i_max = 0.55

# indices in the particles array
SMA = 6
ECC = 7
INC = 8

ind_limits = {SMA: (a_min, a_max), ECC: (e_min, e_max), INC: (i_min, i_max)}


def scan_logs(particle_assignments_file: Path, results_dir: Path, project_dir: Path) -> tuple:
    integration_time = None
    time_taken = []
    escaped_asteroid_data = list()
    particles_simulated = 0

    inner_solar = 0
    outer_solar = 0
    escaped_asteroids = set()
    particles_assigned = pd.read_hdf(particle_assignments_file.resolve())

    for pv_file in results_dir.glob('*.h5'):
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
                        ast_name, vec_list, particle_number = \
                            sim_particles.iloc[[sim_particle]][['ast_name',
                                                                'particle_types',
                                                                'particle_number']].values[0]
                    except IndexError:
                        print(f"We got an unallocated particle we'll skip file:{pv_file} particle:{sim_particle} "
                              f"parameter:{param_index}")
                        continue
                    escaped_asteroids.add(f"{ast_name}{''.join(vec_list)}")
                    # we need the first item index for this sim_particle
                    escape_index = (np.where(outside[1] == sim_particle))[0][0]
                    min_val_arg = np.argmin(part_values[:, sim_particle, param_index])
                    min_val = part_values[min_val_arg, sim_particle, param_index]
                    if param_index == SMA and min_val < a_min:
                        inner_solar += 1
                    max_val_arg = np.argmax(part_values[:, sim_particle, param_index])
                    max_val = part_values[max_val_arg, sim_particle, param_index]
                    if param_index == SMA and max_val > a_max:
                        outer_solar += 1
                    escaped_asteroid_data.append([ast_name, ''.join(vec_list),
                                                  simulation_log.attrs['simulation'],
                                                  particle_number, param_index,
                                                  part_values[outside[0][escape_index], outside[1][escape_index],
                                                  param_index],
                                                  int_values[outside[0][escape_index]],
                                                  min_val,
                                                  max_val])

    escaped_ast_cols = ['ast_name', 'vectors', 'sim_no', 'particle_number', 'parameter', 'parameter_value',
                        'integration_year', 'min_val', 'max_val']
    escaped_ast_df = pd.DataFrame(escaped_asteroid_data, columns=escaped_ast_cols)
    escapees_file = project_dir / "escaped_asteroids.h5"

    with pd.HDFStore(str(escapees_file.resolve())) as hdf_store:
        hdf_store.put('escaped_asteroids', escaped_ast_df)
        hdf_store.get_storer('escaped_asteroids').attrs.metadata = {'integration_time': integration_time,
                                                                    'simulated': particles_simulated,
                                                                    'escaped': len(escaped_asteroids),
                                                                    'outer_solar': outer_solar,
                                                                    'inner_solar': inner_solar,
                                                                    'avg_walltime': np.mean(time_taken),
                                                                    }

    return len(escaped_asteroids), particles_simulated, np.mean(time_taken)


def collect_statistics(part_values):
    all_parts = np.reshape(part_values, [part_values.shape[0] * part_values.shape[1], part_values.shape[2]])
    desc_stats = stats.describe(all_parts, 0)
    deciles = np.percentile(all_parts, [10, 20, 30, 40, 50, 60, 70, 80, 90], 0)
    return desc_stats, deciles


def plot_orbital_escapes(results_dir: Path, project_dir: Path):
    escapees_file = project_dir / "escaped_asteroids.h5"
    xlabel_time = 'Years after start of simulation [$10^9 ~ yr$]'

    # Read the escaped asteroids file
    ea_mmc3 = None
    with pd.HDFStore(str(escapees_file.resolve())) as ea_file:
        ea_mmc3 = ea_file.get('escaped_asteroids')

    # Get a list of all asteroids that have >= 75% of clones go missing
    ea_grouped1 = ea_mmc3[ea_mmc3.parameter == 6][['ast_name', 'vectors']].groupby('ast_name').size()
    asteroid_track_names = ea_grouped1[ea_grouped1 > (65 * 0.75)].index

    escaped_ast_sim = ea_mmc3[ea_mmc3.ast_name.isin(asteroid_track_names)][['ast_name', 'sim_no', 'particle_number']]
    escaped_ast_sim = escaped_ast_sim.drop_duplicates()
    for ast_name in asteroid_track_names:
        ast_array = escaped_ast_sim.loc[escaped_ast_sim.ast_name == ast_name].values
        print(ast_name)
        int_values = None
        plot_vals = np.zeros([10000, len(ast_array), 11])
        xkcd_colors = list(mpl.colors.XKCD_COLORS.keys())

        fig = plt.figure(figsize=(8, 8))
        fig.suptitle(f'Orbital Evolution for clones of asteroid {ast_name} ')
        gs = fig.add_gridspec(3, hspace=0)
        (ax1, ax2, ax3) = gs.subplots(sharex=True)

        for p_no, (_, sim_file, particle_no) in enumerate(ast_array):
            with h5.File(results_dir / f"pvals_{sim_file:0>5}.h5", 'r') as sim_log:
                # Unpack the H5
                # Store the first array of time steps (they're duplicated across H5's)
                if int_values is None:
                    int_values = sim_log['integration_time_values'][()]/(2*np.pi)
                # Copy the values for the particle
                part_values = sim_log['particle_values'][()]
                sma_0 = np.where(part_values[:, particle_no - 8, SMA] == 0.0)[0]
                if len(sma_0) > 0:
                    graph_end = sma_0[0] + 1
                else:
                    graph_end = len(part_values)
                color = xkcd_colors[p_no * 13]
                ax1.scatter(int_values[:graph_end], part_values[:graph_end, particle_no - 8, SMA],
                            s=5, marker='o', c=color)
                ax2.scatter(int_values[:graph_end], part_values[:graph_end, particle_no - 8, ECC],
                            s=5, marker='o', c=color)
                ax3.scatter(int_values[:graph_end], part_values[:graph_end,  particle_no - 8, INC],
                            s=5, marker='o', c=color)
        plt.xlabel(xlabel_time)
        ax1.set_ylabel("Semi-major axis $a$ [AU]")
        ax1.label_outer()
        ax2.set_ylabel("Eccentricity $e$ []")
        ax2.label_outer()
        ax3.set_ylabel("Inclination $i$ [radian]")
        plt.savefig(project_dir / f"plots/orb_evol_{ast_name.replace(' ', '_')}.png", dpi=300)
        plt.close()

    print('Completed')


if __name__ == '__main__':
    print(sys.argv)
    clone_assignments = Path(sys.argv[1])
    cl_results_dir = Path(sys.argv[2])
    cl_project_dir = Path(sys.argv[3])
    escaped_c, simulated_c, avg_runtime = scan_logs(clone_assignments, cl_results_dir, cl_project_dir)
    print(f"Escaped asteroids:{escaped_c} Total simulated {simulated_c} "
          f"\nFraction escaped:{escaped_c/simulated_c}")
    print(f'Average run time {datetime.timedelta(seconds=avg_runtime)}')
    plot_orbital_escapes(cl_results_dir, cl_project_dir)
