"""
Data preparation from jupyter_notebooks/Escaped_asteroids_analysis.ipynb, moved here so it
can be tested. The code is as it is in the notebook (cells 6, 12-14 and 27).
"""
import numpy as np
import pandas as pd

# 1 = inner, 2 = outer, 3 = both, 0 = stable
a_min = 1.8
a_max = 3.95


def escape_years(ea_df: pd.DataFrame) -> pd.DataFrame:
    """
    Semi-major axis escapes with the integration time converted to years (cell 6)
    """
    escapee_years = ea_df.loc[ea_df.parameter == 6][['ast_name', 'vectors', 'integration_year']]
    escapee_years['integration_year'] = escapee_years.integration_year/(2*np.pi)
    return escapee_years


def mean_escape_by_asteroid(escapee_years: pd.DataFrame) -> pd.DataFrame:
    """
    Mean escape year and number of escaped clones for each asteroid (cells 12 and 13)
    """
    ey_years = escapee_years.groupby('ast_name')
    mean_escape = ey_years[['integration_year']].mean()
    mean_escape['vec_count'] = ey_years.vectors.count()

    counts, bins = np.histogram(mean_escape.vec_count, 4)
    mean_escape['quartiles'] = np.digitize(mean_escape.vec_count, bins)
    return mean_escape


def attach_escapes(fam_df: pd.DataFrame, mean_escape: pd.DataFrame) -> pd.DataFrame:
    """
    Add the escape year and plot symbol to the family DataFrame, indexed by ast_name (cell 14)
    """
    fam_df['integration_year'] = mean_escape.integration_year
    fam_df['quartiles'] = mean_escape.quartiles

    fam_df = fam_df.fillna(value={'integration_year': 0, 'vec_count': 0})
    fam_df['graph_symbol'] = '.'
    fam_df.loc[fam_df['integration_year'] != 0, ['graph_symbol']] = 'o'
    return fam_df


def inny_outy(esc):
    if esc.mean_min_val < a_min and esc.mean_max_val < a_max:
        return 1
    elif esc.mean_max_val > a_max and esc.mean_min_val > a_min:
        return 2
    elif esc.mean_max_val > a_max and esc.mean_min_val < a_min:
        return 3
    else:
        return 0


def attach_sma_extremes(fam_df: pd.DataFrame, ea_df: pd.DataFrame) -> pd.DataFrame:
    """
    Add the mean min/max semi-major axis and where the asteroid went (cell 27)
    """
    max_min_sma = ea_df.loc[ea_df.parameter == 6][['ast_name', 'min_val', 'max_val']]
    mean_sma = max_min_sma.groupby('ast_name')[['min_val', 'max_val']].mean()

    fam_df['mean_min_val'] = mean_sma.min_val
    fam_df['mean_max_val'] = mean_sma.max_val
    fam_df['last_sma'] = fam_df.apply(inny_outy, axis=1)
    return fam_df
