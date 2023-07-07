
from horizons_api import get_family_eph, convert_dy2yr
from parse_afp_family import get_family_df
from sim_creation import create_whfast_sim, create_mercurious_sim
from prepare_clones import create_clones
from orbital_log_scan import scan_logs


def simulation_project():
    family_name = 'luthera'
    family_id = 1303

    project_dir = '../../asteroid_data/'
    sim_dir = project_dir+family_name
    # Add active asteroid  426/P ???
    # COMMAND = 'DES=1003609;NOFRAG;'
    """$$SOE
    2451544.500000000, A.D. 2000-Jan-01 00:00:00.0000,  2.334269053942694E+00, -1.808322981199081E+00,  
    6.292178749934185E-01,  4.428832441905231E-03,  8.923607089146576E-03,  1.921127626386464E-03, 
    1.48642185E-05,  2.32441520E-05,  6.25526758E-06,  7.55661843E-08,  4.71045977E-08,  2.07506493E-08,
    $$EOE
    """
    P_426 = {'ast_name': 'P_426', 'X': 2.334269053942694E+00, 'Y': -1.808322981199081E+00, 'Z': 6.292178749934185E-01,
             'VX': 4.428832441905231E-03, 'VY': 8.923607089146576E-03, 'VZ': 1.921127626386464E-03,
             'sX': 1.48642185E-05, 'sY': 2.32441520E-05, 'sZ': 6.25526758E-06,
             'sVX': 7.55661843E-08, 'sVY': 4.71045977E-08, 'sVZ': 2.07506493E-08}

    convert_dy2yr(P_426)

    # Check on AFP data and download if required

    # Extract the family
    luthera_family = get_family_df('../../asteroid_data/afp.fam.members.txt', "1303")
    # Retrieve the ephemeris
    lth_eph_df = get_family_eph('../../asteroid_data/', luthera_family)
    # Add the P/426 active asteroid ephemeris to the family
    lth_eph_df.loc[len(lth_eph_df)] = [P_426[x] for x in ['ast_name', 'X', 'Y', 'Z', 'VX', 'VY', 'VZ',
                                                          'sX', 'sY', 'sZ', 'sVX', 'sVY', 'sVZ']]

    # create the sim files
    part_per_sim = 3

    active_list = ['Sun', 'Mars', 'Ceres', 'Jupiter', 'Saturn', 'Uranus', 'Neptune']
    mass_particles = {2: 5.21e-10}
    out_dir = f"../../asteroid_data/sim_data/mc_pm6_{part_per_sim}/inputs"

    base_sim = create_mercurious_sim(active_list, mass_particles)

    particle_assignments = create_clones(lth_eph_df, out_dir, base_sim, part_per_sim)

    print(f"Completed creating:{active_list}")

    # Zip or tar the inputs
    # upload the sim files

    # kick off the jobs??

    # Determine escaped asteroids
    escaped_asteroids = scan_logs(particle_assignments, results_files, summary_files)
    # Plot

    # scan the pval files to track the escaped asteroids

