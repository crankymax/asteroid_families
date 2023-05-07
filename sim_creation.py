import rebound


def create_rebound_sim(active_list, manual_masses, particle_period):
    sim = rebound.Simulation()
    date = 'JD2451544.5'
    sim.add(active_list, date=date)
    # TODO: Create a parameter that allows masses to be passed in
    for p_num, mass in manual_masses.items():
        sim.particles[p_num].m = mass  # Ceres Mass in Solar masses
    sim.dt = sim.particles[particle_period].P / 30  # 1/30 of a planetary period
    sim.N_active = len(active_list)
    sim.testparticle_type = 1
    sim.move_to_com()
    return sim


def create_whfast_sim(active_list, manual_masses=None, particle_period=1):
    wh_sim = create_rebound_sim(active_list, manual_masses, particle_period)
    wh_sim.integrator = "whfast"
    return wh_sim


def create_mercurious_sim(active_list, manual_masses=None, particle_period=1):
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
