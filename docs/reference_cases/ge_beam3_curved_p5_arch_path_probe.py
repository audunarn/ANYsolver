"""Small spatial discrete-arch comparison with a separate symmetric continuum BVP.

No changes to local mechanics or continuation. The full free spatial tangent
is retained; negative modes are reported, not stabilized or deleted. This is
development evidence, not a qualification runner or an exact stability proof.
"""

from dataclasses import dataclass
import time

import numpy as np

from docs.reference_cases.ge_beam3_curved_p5_continuum_probe import parabolic_references
from docs.reference_cases.ge_beam3_curved_p5_section_probe import DirectedHardeningSectionProbe
from docs.reference_cases.ge_beam3_curved_p5_assembly_history_probe import NonlinearAssemblyHistoryProbe
from docs.reference_cases.ge_beam3_curved_p5_continuation_probe import BeamContinuationProbe,spatial_derivative,tangent
from docs.reference_cases.ge_beam3_curved_p5_arch_reference import solve as continuum
from docs.reference_cases.ge_beam3_curved_p5_history_path_probe import digest


@dataclass(frozen=True)
class ArchPathRecord:
    step: int
    load: float
    crown_drop: float
    reference_load: float
    relative_load_error: float
    current_load_slope: float
    predictor_parameter_direction: float
    current_parameter_direction: float
    minimum_free_eigenvalue: float
    equilibrium_error: float
    arc_error: float
    symmetry_error: float
    iterations: int
    mixed_evaluations: int


class ArchPathError(RuntimeError):
    """No completed path; checkpoints are diagnostics only, never partial PASS."""

    def __init__(self,message,records=()):
        super().__init__(message)
        self.records = tuple(records)


@dataclass(frozen=True)
class ArchPathResult:
    elements: int
    records: tuple
    model: object
    orientation: np.ndarray
    production_qualified: bool = False


def specimen(count):
    if type(count) is not int or count not in (2,4,8):
        raise ValueError('registered two/four/eight-element arch required')
    refs = parabolic_references(.1,count)
    elastic = np.diag([1000.,400.,400.,.02,.01,.02])
    sections = [DirectedHardeningSectionProbe(elastic,[1.,0.,0.,0.,0.,0.],1e6,1.) for _ in refs]
    beam = NonlinearAssemblyHistoryProbe(refs,[(2*i,2*i+1,2*i+2) for i in range(count)],
        sections,fixed_nodes=(0,2*count),order=8)
    pattern = np.zeros((2*count+1,3));pattern[count,1] = -1.
    return beam,pattern


def run(count,*,steps=8,max_seconds=60.,progress=None):
    if (type(steps) is not int or not 1<=steps<=12 or
            not isinstance(max_seconds,(int,float)) or isinstance(max_seconds,bool) or
            not np.isfinite(max_seconds) or not 0<=max_seconds<=60):
        raise ValueError('at most twelve bounded development increments required')
    beam,pattern = specimen(count)
    driver = BeamContinuationProbe(beam,pattern)
    started = time.monotonic()
    records,previous = [],None
    try:
        for i in range(steps):
            if time.monotonic()-started>=max_seconds:
                raise ArchPathError('path deadline reached before next increment')
            trial = driver.trial(.01,max_iterations=16,max_mixed_evaluations=256*count)
            driver.commit(trial)
            current = driver.committed_model
            state,response = current.committed,trial.assembly_trial.response
            if digest(current.replay())!=digest(response):
                raise ArchPathError('accepted-origin replay mismatch')
            if any(h.accumulated!=0 for hs in state.histories for h in hs):
                raise ArchPathError('elastic arch acquired plastic history')
            drop = .1-state.positions[count,1]
            remaining = max_seconds-(time.monotonic()-started)
            if remaining<=0:
                raise ArchPathError('path deadline reached before reference comparison')
            previous = continuum(drop,previous=previous,profile='BVP9',max_seconds=remaining)
            if not np.isfinite(previous.load) or previous.load<=0:
                raise ArchPathError('positive finite reference load required on this registered branch')
            free = beam._free
            # Trial.tangent is the OLD-state predictor, not the new-state slope.
            direction = tangent(spatial_derivative(response)[np.ix_(free,free)],
                beam._external(pattern)[free],trial.tangent,driver._metric)
            full = np.zeros(6*beam._nodes);full[free] = direction[:-1]
            crown_direction = -full[6*count+1]
            if abs(crown_direction)<=1e-12:
                raise ArchPathError('crown coordinate cannot parameterize this branch point')
            k = response.tangent[np.ix_(free,free)]
            symmetry = float(np.linalg.norm(k-k.T)/max(1.,np.linalg.norm(k)))
            if symmetry>1e-11:
                raise ArchPathError('free tangent symmetry mismatch')
            record = ArchPathRecord(i+1,driver.parameter,float(drop),previous.load,
                abs(driver.parameter/previous.load-1),float(direction[-1]/crown_direction),
                float(trial.tangent[-1]),float(direction[-1]),float(np.linalg.eigvalsh(k)[0]),
                trial.assembly_trial.residual_norm,trial.arc_residual,symmetry,
                trial.assembly_trial.iterations,trial.assembly_trial.mixed_evaluations)
            if time.monotonic()-started>=max_seconds:
                raise ArchPathError('path deadline reached before publishing checkpoint')
            records.append(record)
            if progress is not None:
                progress(record)
        return ArchPathResult(count,tuple(records),driver.committed_model,driver.orientation)
    except (RuntimeError,ValueError,np.linalg.LinAlgError) as exc:
        raise ArchPathError(f'bounded arch path failed without retry: {type(exc).__name__}: {exc}',records) from exc
