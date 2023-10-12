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
7. Create the required PBS jobs to complete the simulation runs
8. After the simulations have completed, run the simulation analysis on the cluster
9. Download the escaped asteroids data
10. Use the Python Notebooks to analyse the data

# Project Structure
The structure of a project starts at the project directory. In this 
case it's luthera. Under this are the input, results and console directories
```
|luthera_ast
|_console
|_input
|_plots
|_results
```

# Initiating simulation runs

  613  python asteroid_sim/manage_runs.py 0 19044 120 asteroid_sim/

  911  python asteroid_sim/manage_runs.py asteroid_sim/mc_pm6_3/rerun_jobs asteroid_sim/

# Initiating log scan

 qsub chk_mc_pm6_3 

## In Progress
The ba




    