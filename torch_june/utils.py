import numpy as np
import torch
from itertools import chain
from pyro import distributions as dist
import datetime
from typing import Union
from copy import deepcopy


def read_date(date: Union[str, datetime.datetime]) -> datetime.datetime:
    """
    Read date in two possible formats, either string or datetime.date, both
    are translated into datetime.datetime to be used by the simulator

    Parameters
    ----------
    date:
        date to translate into datetime.datetime

    Returns
    -------
        date in datetime format
    """
    if type(date) is str:
        return datetime.datetime.strptime(date, "%Y-%m-%d")
    elif isinstance(date, datetime.date):
        return datetime.datetime.combine(date, datetime.datetime.min.time())
    else:
        raise TypeError("date must be a string or a datetime.date object")


def parse_age_probabilities(age_dict, fill_value=0):
    """
    Parses the age probability dictionaries into an array.
    """
    bins = []
    probabilities = []
    for age_range in age_dict:
        age_range_split = age_range.split("-")
        bins.append(int(age_range_split[0]))
        bins.append(int(age_range_split[1]))
        probabilities.append(age_dict[age_range])
    sorting_idx = np.argsort(bins[::2])
    bins = list(
        chain.from_iterable([bins[2 * idx], bins[2 * idx + 1]] for idx in sorting_idx)
    )
    probabilities = np.array(probabilities)[sorting_idx]
    probabilities_binned = []
    for prob in probabilities:
        probabilities_binned.append(fill_value)
        probabilities_binned.append(prob)
    probabilities_binned.append(fill_value)
    probabilities_per_age = []
    for age in range(100):
        idx = np.searchsorted(bins, age + 1)  # we do +1 to include the lower boundary
        probabilities_per_age.append(probabilities_binned[idx])
    return probabilities_per_age


def parse_distribution(dict, device):
    dd = deepcopy(dict)
    dist_name = dd.pop("dist")
    dist_class = getattr(dist, dist_name)
    input = {
        key: torch.tensor(value, device=device, dtype=torch.float)
        for key, value in dd.items()
    }
    return dist_class(**input)

def fix_seed(seed=None):
    if seed is None:
        seed = np.random.randint(0, 1000)
    print(f"Fixing seed to {seed}")
    torch.manual_seed(seed)
    np.random.seed(seed)
    random.seed(seed)
    torch.cuda.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
