import rebound


def create_rebound_sim(active_list, manual_masses, particle_period):
    """
    Initialises a REBOUND simulation file with values from HORIZONS for the list
    of planets in active_list. The manual masses are assigned if supplied for planets with
    no HORIZONS mass. Values are calculated for 2451544.5 JD. dt is set to 1/30 of the particle_period
    :param active_list: List of planets or bodies
    :param manual_masses: Mass values in KG for
    :param particle_period: The particle to use to set dt
    :return: REBOUND simulation
    """
    sim = rebound.Simulation()
    date = 'JD2451544.5'
    sim.add(active_list, date=date)
    for p_num, mass in manual_masses.items():
        # Set Mass in Solar masses if horizons doesn't have it
        sim.particles[p_num].m = mass
    # 1/30 of the innermost planetary period
    sim.dt = sim.particles[particle_period].P / 30
    sim.N_active = len(active_list)
    sim.testparticle_type = 1
    sim.move_to_com()
    return sim


def create_whfast_sim(active_list, manual_masses=None, particle_period=1):
    """
    Configure whfast as the integrator for the simulation.
    :param active_list: List of planets or bodies
    :param manual_masses: Mass values in KG for
    :param particle_period: The particle to use to set dt
    :return: REBOUND simulation
    """
    wh_sim = create_rebound_sim(active_list, manual_masses, particle_period)
    wh_sim.integrator = "whfast"
    return wh_sim


def create_mercurious_sim(active_list, manual_masses=None, particle_period=1):
    """
    Configure mercurius as the integrator
    :param active_list: List of planets or bodies
    :param manual_masses: Mass values in KG for
    :param particle_period: The particle to use to set dt
    :return: REBOUND simulation
    """
    merc_sim = create_rebound_sim(active_list, manual_masses, particle_period)
    merc_sim.integrator = "mercurius"
    # collision and boundary options
    merc_sim.collision = "direct"
    merc_sim.collision_resolve = "merge"
    merc_sim.collision_resolve_keep_sorted = 1
    merc_sim.boundary = "open"
    boxsize = 200.
    merc_sim.configure_box(boxsize)
    merc_sim.track_energy_offset = 1

    return merc_sim


def copy_sim(sim, sims_required):
    sim_list = []
    for _ in range(sims_required):
        sim_list.append(sim.copy())

    return sim_list
