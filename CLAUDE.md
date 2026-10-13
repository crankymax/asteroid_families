# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

Simulates asteroid families from the Asteroid Families Portal (AFP) with REBOUND on the UniSQ HPC cluster (Fawkes, PBS scheduler), then finds clones that escape the family's orbital region. Built as an MSC6001 dissertation project. There is no packaging, build step, or linter config; modules in `src/` import each other by bare name (e.g. `from sim_creation import ...`), so `src/` must be on the path / the working directory.

Local Python env: conda env `rebnd2` (`~/miniforge3/envs/rebnd2`, referenced in `pyrefly.toml` and `.vscode/settings.json`). On the cluster, jobs use `module load python/3.9.13-gcc...`, so keep code Python 3.9 compatible. Key deps: `rebound`, `h5py`, `pandas` (with PyTables for HDF), `numpy`, `matplotlib`, `requests`.

## Pipeline (end to end)

1. **Project creation (local)** — a per-family script (`euterpe_fam.py`, `semele_fam.py`, `luthera_ast.py`) is copied from a template and edited (base dir, family name/ID, active bodies, particles per sim). Its `simulation_project()`:
   - creates `<family>_ast/{inputs,results,console,plots}`
   - downloads AFP members/proper elements and the Gallardo 2-body MMR atlas (`parse_afp_family.py`)
   - fetches ephemerides from JPL Horizons (`horizons_api.py`), cached as HDF in the project dir
   - builds a base Mercurius sim from Horizons at JD2451544.5 (`sim_creation.py`; Ceres mass set manually, `N_active` = number of actives, `testparticle_type = 1`)
   - `prepare_clones.create_clones()` spreads each asteroid's clone particles round-robin across N copies of the base sim and writes `inputs/sim_NNNNN.bin`, `inputs/sim_actives.bin`, a family sim, and `inputs/clone_assignments.h5` (maps `ast_name` → `sim_no`, `particle_number`).
2. **Run on cluster** — `manage_runs.py` builds PBS job scripts as strings and pipes them to `qsub`. Each job runs `rebound_run_sim.py <sim_no|actives> <int_length_years> <project_dir> <max_walltime_hours>`.
3. **Status / reruns** — `determine_status.py <project_dir> [report]` checks inputs/results for missing, truncated (<1 KB) or short-integrated sims. It deletes bad outputs so they restart, unless `report` is passed. The resulting list of sim numbers goes to `manage_runs.py <rerun_file> <project_dir>`.
4. **Scan** — `orbital_log_scan.py <clone_assignments.h5> <results_dir> <project_dir>` (run through `bash/orbital_log_scan` via qsub) flags particles leaving the a/e/i bounds hard-coded at the top of the file and writes `escaped_asteroids.h5` into the project dir.
5. **Analysis** — copy `escaped_asteroids.h5` locally into the top project dir and use the notebooks in `jupyter_notebooks/` (copied into the project's `notebooks/`).

## Simulation run/restart semantics (`rebound_run_sim.py`)

- Sim numbers get zero-padded to 5 digits (`sim_00042.bin`); `actives` is the special planets-only sim (it logs every particle from index 1 instead of from `N_active`).
- Output per sim: `results/pvals_NNNNN.h5` (datasets `integration_time_values`, `sim_energy_values`, `particle_values[time, particle, 11]` = x,y,z,vx,vy,vz,a,e,inc,omega,Omega; attrs `simulation`, `int_length`, `start_index`, `clock_time`) and `results/sim_NNNNN_fin.bin`.
- Walltime-aware: integration stops early with a safety margin (30 min, or 5% for short walltimes) and saves; if a `pvals` file exists, rerunning the same command resumes from `start_index`. `start_index == 0` in a saved log means "completed", and that is the only state where rerunning with a larger `int_length` extends the time array. Extending an unfinished run raises.
- Time units: years × 2π (REBOUND G=1 units). The number of log points comes from the magnitude of `int_length`.
- `store_config` builds paths as `f'{base_dir}results/'`, so `project_dir` arguments need a trailing slash.

## Tests

Tests in `test/` are unittest/pytest integration tests. They point at real simulation data through relative paths like `../../asteroid_data/...` or `/Volumes/fua/...` and will fail without that data. Run them from `test/` with `src` on the path:

```
cd test && PYTHONPATH=../src python -m pytest test_run_sim.py::TestSimulation::test_one_shot
```

`test/qsub` is a stub (`cat -`) passed as `cmd='./qsub'` so `manage_runs` job submission prints the generated PBS script instead of submitting it.

## Cluster specifics

PBS project code, job names, email, queue and the `module load` line are hard-coded in `bash/*` and in the job templates in `manage_runs.py`. Update them for each family/run. Job scripts `cd asteroid_sim/` and expect the `src/` modules and project dirs to sit together there on the cluster.
