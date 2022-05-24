from abc import ABC
import yaml
import re
import datetime
import torch

import torch_june
from torch_june.utils import read_date
from torch_june.paths import default_config_path


class Policy(torch.nn.Module):
    def __init__(self, start_date, end_date, device):
        super().__init__()
        self.start_date = read_date(start_date)
        self.end_date = read_date(end_date)
        self.device = device

    def apply(self):
        raise NotImplementedError

    def is_active(self, date: datetime.datetime) -> bool:
        """
        Returns true if the policy is active, false otherwise

        Parameters
        ----------
        date:
            date to check
        """
        return self.start_date <= date < self.end_date


class PolicyCollection(torch.nn.Module):
    def __init__(self, policies: Policy):
        """
        A collection of like policies active on the same date
        """
        super().__init__()
        self.policies = torch.nn.ModuleList(policies)

    def __getitem__(self, idx):
        return self.policies[idx]


class Policies(torch.nn.Module):
    def __init__(self, policies=None):
        super().__init__()
        if policies is None:
            policies = torch.nn.ModuleList([])
        self.policies = policies
        from torch_june.policies import (
            InteractionPolicies,
            QuarantinePolicies,
            CloseVenuePolicies,
        )

        self.interaction_policies = InteractionPolicies(
            self._get_policies_by_type(policies, "interaction")
        )
        self.quarantine_policies = QuarantinePolicies(
            self._get_policies_by_type(policies, "quarantine")
        )
        self.close_venue_policies = CloseVenuePolicies(
            self._get_policies_by_type(policies, "close_venue")
        )

    @classmethod
    def from_file(cls, fpath=default_config_path):
        with open(fpath, "r") as f:
            params = yaml.safe_load(f)
        return cls.from_parameters(params)

    @classmethod
    def from_parameters(cls, params):
        policy_params = params["policies"]
        device = params["system"]["device"]
        policies = []
        for policy_collection in policy_params.values():
            for policy_name, policy_config in policy_collection.items():
                policies += cls._parse_policy_config(policy_config, name=policy_name, device=device)
        return cls(policies)

    @staticmethod
    def _parse_policy_config(config, name, device):
        camel_case_key = "".join(x.capitalize() or "_" for x in name.split("_"))
        policies = []
        policy_class = getattr(torch_june.policies, camel_case_key)
        if "start_date" not in config:
            for policy_i, policy_data_i in config.items():
                if (
                    "start_date" not in policy_data_i.keys()
                    or "end_date" not in policy_data_i.keys()
                ):
                    raise ValueError("policy config file not valid.")
                policies.append(policy_class(**policy_data_i, device=device))
        else:
            policies.append(policy_class(**config, device=device))
        return policies

    def _get_policies_by_type(self, policies, type):
        return [policy for policy in policies if policy.spec == type]