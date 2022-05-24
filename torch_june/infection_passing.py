import torch
import yaml
import numpy as np
from torch_geometric.nn.conv import MessagePassing
from torch.nn.functional import gumbel_softmax
from pyro.distributions import RelaxedBernoulliStraightThrough
from torch.utils.checkpoint import checkpoint

from torch_june.paths import default_config_path


import pickle




class IsInfectedSampler(torch.nn.Module):
    def forward(self, not_infected_probs):
        infected_probs = 1.0 - not_infected_probs
        dist = RelaxedBernoulliStraightThrough(temperature=0.1, probs=infected_probs)
        return dist.rsample()