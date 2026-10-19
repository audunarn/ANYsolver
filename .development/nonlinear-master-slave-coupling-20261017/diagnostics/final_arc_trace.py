"""Observe remaining registered arc cases without changing inputs or oracle."""
from __future__ import annotations

import json
import arc_reference


def main():
    original = arc_reference.solve_static_nonlinear

    def observed(*args, **kwargs):
        if 'status_callback' in kwargs or 'progress_callback' in kwargs:
            raise RuntimeError('Refuse to replace an existing observer')
        kwargs['status_callback'] = lambda message: print(message, flush=True)
        kwargs['progress_callback'] = lambda event: print(
            json.dumps({'kind': 'accepted_progress', 'event': str(event)}), flush=True)
        return original(*args, **kwargs)

    arc_reference.solve_static_nonlinear = observed
    arc_reference.main()


if __name__ == '__main__':
    main()
