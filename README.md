# Asteroid Family Simulation Management

## Introduction
The goal of this project is to use REBOUND to simulate an asteroid family on the UniSQ HPC facility, Fawkes.

The developed software was generalised so that any family identified in the Asteroid Families Portal (AFP) could be 
simulated in a similar way.

To create the simulation files:
1. Copy the project euterpe_fam.py python module into the /src directory with a new name (e.g. semele_fam.py)
2. Configure the project directory (e.g. ~/asteroid_sim/)
3. Nominate the family and its identifier to study (e.g. Eutrerpe 27) 
4. Edit the list of active bodies
5. Run the python copied python script and it will create the simulations to be run in the cluster. 

The REBOUND simulation files are created in the input directory.  

Running the simulations:
1. Export the simulation files to the cluster environment with the project structure below.
2. Create the required PBS jobs to complete the simulation runs
3. After the simulations have completed, run the simulation analysis on the cluster
4. Download the escaped asteroids data
5. Copy the Python Notebooks from this source folder to the project folders 
6. Execute and edit the notebooks to analyse the data

# Project Structure
The structure of a project starts at the project directory. In this 
case it's luthera. Under this are the input, results and console directories
```
luthera_ast
|__console
|__input
|__notebooks
|__plots
|__results
```

Running the `simulation_project` function will create the directory structure above under a directory named after 
the family. The `console` directory stores the output from PBS, the `input` directory contains the simulation and 
configuration files used to run the simulation, the `notebooks` directory contains the notebooks used to analyse the 
simulation results, `plots` contains output from the orbital log scans and `results` contains the HDF logs from the 
simulations. 

## Initiating simulation runs
Creating a number of PBS array jobs is done by executing the following line: 

    python asteroid_sim/manage_runs.py 0 19044 120 asteroid_sim/

To restart some jobs that failed:

    python asteroid_sim/manage_runs.py asteroid_sim/mc_pm6_3/rerun_jobs asteroid_sim/

Where the rerun_jobs parameter is a file of the simulation identifier numbers that require a rerun

## Initiating log scan
When the PBS jobs have completed the escaped asteroids are detected by running the following command

    qsub orbital_log_scan 

## In Progress
~~~~The ba




    