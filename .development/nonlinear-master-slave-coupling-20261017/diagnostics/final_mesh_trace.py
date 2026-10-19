"""One observed mesh retry: unchanged physical model, controls and oracle."""
from __future__ import annotations

import argparse
import json

import mesh_study


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('case', choices=('M4', 'P4'))
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    original = mesh_study.solve_static_nonlinear

    def observed(*positional, **keywords):
        if 'status_callback' in keywords or 'progress_callback' in keywords:
            raise RuntimeError('Refuse to replace an existing observer')
        keywords['status_callback'] = lambda message: print(message, flush=True)
        keywords['progress_callback'] = lambda event: print(
            json.dumps({'kind': 'accepted_progress', 'event': str(event)}), flush=True)
        return original(*positional, **keywords)

    mesh_study.solve_static_nonlinear = observed
    mesh_study.write_result(mesh_study.run_case(args.case), args.output)


if __name__ == '__main__':
    main()
