import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import datetime

gantt = pd.DataFrame([
    dict(Task="Retrieve Luthera family \nasteroid data", Start=1, Duration=1),
    dict(Task="Write Literature Review", Start=1, Duration=7),
    dict(Task="Generate the orbital data for \neach asteroid from the \nNASA Horizons system",
         Start=3, Duration=2),
    dict(Task="Create test-particle cloud", Start=4, Duration=2),
    dict(Task="Determine REBOUND config", Start=3, Duration=8),
    dict(Task="Create HPC jobs and software \nto log data", Start=6, Duration=3),
    dict(Task="Write Project Proposal", Start=10, Duration=3),
    dict(Task="Create scripts to analyse logs \nand extract summary information", Start=8, Duration=10),
    dict(Task="Create Proposal Presentation", Start=11, Duration=3),
    dict(Task="Analyse the logged data \nto determine any perturbed \nasteroids", Start=15, Duration=15),
    dict(Task="Write dissertation/results", Start=18, Duration=15),
    dict(Task="Create final presentation", Start=28, Duration=4)
    ])

start_date = datetime.datetime.strptime('2023-02-20', "%Y-%m-%d")
week_dates = [datetime.datetime.strftime(start_date+datetime.timedelta(weeks=week), '%m-%d') for week in range(0, 36, 4)]
gantt['start_to_end'] = gantt.Start + gantt.Duration

fig, ax = plt.subplots(1, figsize=(20, 6))
ax.barh(gantt.Task, gantt.Duration, left=gantt.Start)
ax.invert_yaxis()
ax.set_xlabel('2023 Date (Month-Day)')
ax.set_ylabel('Task Name')
ax.set_xticks(range(0, 36, 4), week_dates)
ax.grid(visible=True, axis='both', alpha=0.5)
plt.show()
