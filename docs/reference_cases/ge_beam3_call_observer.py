"""Single-thread, selected-call timing observer; never replaces computation."""
from functools import wraps
from time import perf_counter, process_time


class Observer:
    def __init__(self, wall=perf_counter, cpu=process_time):
        self.wall, self.cpu = wall, cpu
        self.phase = 'initialization'
        self.rows, self.stack = {}, []

    def wrap(self, name, function):
        @wraps(function)
        def measured(*args, **kwargs):
            key = (self.phase, name)
            row = self.rows.setdefault(key, dict(calls=0, failures=0,
                wall_seconds=0., cpu_seconds=0., self_wall_seconds=0., self_cpu_seconds=0.))
            start = self.wall(), self.cpu()
            frame = [0., 0.]
            self.stack.append(frame)
            row['calls'] += 1
            try:
                return function(*args, **kwargs)
            except BaseException:
                row['failures'] += 1
                raise
            finally:
                elapsed = self.wall()-start[0], self.cpu()-start[1]
                if self.stack.pop() is not frame:
                    raise RuntimeError('single-thread observer nesting')
                row['wall_seconds'] += elapsed[0]
                row['cpu_seconds'] += elapsed[1]
                row['self_wall_seconds'] += elapsed[0]-frame[0]
                row['self_cpu_seconds'] += elapsed[1]-frame[1]
                if self.stack:
                    self.stack[-1][0] += elapsed[0]
                    self.stack[-1][1] += elapsed[1]
        return measured

    def summary(self):
        if self.stack:
            raise ValueError('observer still active')
        return [dict(phase=phase, function=name, **values)
            for (phase, name), values in sorted(self.rows.items())]
