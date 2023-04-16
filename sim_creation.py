import rebound


def create_rebound_sims(number_required=4096):
    sim = rebound.Simulation()
    date = 'JD2451544.5'
    # Abbrev  Venus
    planet_list = ['Sun', 'Earth', 'Mars', 'Ceres', 'Jupiter', 'Saturn', 'Uranus', 'Neptune']
    sim.add(planet_list, date=date)
    sim.integrator = "whfast"
    sim.particles[3].m = 5.21e-10  # Ceres Mass in Solar masses
    sim.dt = sim.particles[1].P / 30  # 1/30 of the innermost planetary period
    sim.N_active = len(planet_list)
    sim.testparticle_type = 1
    sim.move_to_com()

    sim_list = []
    for _ in range(number_required):
        sim_list.append(sim.copy())

    return sim_list
