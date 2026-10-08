"""Public connected native TransientConfig workflow; source UNVERIFIED."""
import argparse
from hashlib import sha256
import json
import numpy as np
from anysolver.dynamics import TransientConfig
from anysolver.ge_beam3_native_connected_dynamics import solve_transient
from examples.native_connected_dynamic_dev import build,velocity


def run(steps=4,dt=.00025, *, checkpoint=None):
    owner=build();config=TransientConfig(dt=dt,t_end=steps*dt,
        initial_velocity=velocity(owner),save_every=1)
    result=solve_transient(owner,config,checkpoint=checkpoint,
        expected_sha256=sha256(checkpoint).hexdigest() if checkpoint is not None else None)
    return owner,result


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--steps',type=int,default=4)
    args=parser.parse_args();owner,result=run(args.steps)
    print(json.dumps(dict(status=result.to_dict()['status'],accepted_steps=result.to_dict()['accepted_steps'],
        profile=result.to_dict()['profile'],checkpoint_bytes=len(result.checkpoint),engineering_accepted=False)))


if __name__=='__main__':main()
