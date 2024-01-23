import torch
from torch_geometric.data import HeteroData

class IsInfectedSampler(torch.nn.Module):
    def forward(self, not_infected_probs):
        """
        Here we need to sample the infection status of each agent and the variant that
        the agent gets in case of infection.
        To do this, we construct a tensor of size [M+1, N], where M is the number of
        variants and N the number of agents. The extra dimension in M will represent
        the agent not getting infected, so that it can be sampled as an outcome using
        the Gumbel-Softmax reparametrization of the categorical distribution.
        """
        logits = torch.vstack((not_infected_probs, 1.0 - not_infected_probs)).log()
        infection = torch.nn.functional.gumbel_softmax(
            logits, dim=0, tau=0.1, hard=True
        )
        return infection[1, :]

def infect_people(data: HeteroData, time: int, new_infected: torch.Tensor):
    """
    Sets the `new_infected` individuals to infected at time `time`.

    **Arguments:**

    - `data`: the graph data
    - `time`: the time step at which the infection happens
    - `new_infected`: a tensor of size [N] where N is the number of agents.
    """
    data["agent"].susceptibility = torch.clamp(
        data["agent"].susceptibility - new_infected, min=0.0
    )
    data["agent"].is_infected = data["agent"].is_infected + new_infected
    data["agent"].infection_time = data["agent"].infection_time + new_infected * (
        time - data["agent"].infection_time
    )