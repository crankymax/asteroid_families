# Asteroid Family Simulation Management

## Introduction
The goal of this project is to use REBOUND to simulate an asteroid family on the UniSQ HPC facility, Fawkes.

The developed software was generalised so that any family identified in the Asteroid Families Portal (AFP) could be 
simulated in a similar way.

The steps are:
1. Create a project directory
2. Download the current AFP files
3. Parse the AFP data and extract the asteroid family data
4. Retrieve the ephemeris data from Horizons
5. Create the REBOUND simulation files for the clones
6. Export the simulation files to the cluster environment
7. Create the required PBS jobs to complete the simulation runs
8. After the simulations have completed, run the simulation analysis on the cluster
9. Download the escaped asteroids data
10. Use the Python Notebooks to analyse the data

# Project Structure
The structure of a project starts at the project directory. In this 
case it's luthera. Under this are the input, results and console directories

\-luthera

\--console

\--input

\--results


## In Progress
1. Create project template script
2. Wire in the calls to manage the simulation
3. Don't spend too much time



