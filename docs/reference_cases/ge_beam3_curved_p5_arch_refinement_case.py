"""Numerical part of the separately authorized 16-element arch diagnostic.

Import only after the resource runner's authority/lease checks. No existing
mechanics change. Small counts are exposed solely for disposable correctness
tests; the registered resource case is sixteen elements, eight path steps.
"""

from dataclasses import asdict

import numpy as np
from scipy.interpolate import CubicHermiteSpline

from anysolver.ge_beam3_curved_reference import CurvedBeam3ReferenceGeometry
from docs.reference_cases.ge_beam3_curved_p5_arch_reference import equations,solve as continuum
from docs.reference_cases.ge_beam3_curved_p5_assembly_history_probe import NonlinearAssemblyHistoryProbe
from docs.reference_cases.ge_beam3_curved_p5_continuation_probe import BeamContinuationProbe,spatial_derivative,tangent
from docs.reference_cases.ge_beam3_curved_p5_section_probe import DirectedHardeningSectionProbe
from docs.reference_cases.ge_beam3_curved_p5_history_path_probe import digest


SECTION = np.array([1000.,400.,400.,.02,.01,.02])


def references(count):
    if type(count) is not int or count not in (2,4,8,16):
        raise ValueError('registered arch refinement count required')
    t = np.linspace(-1.,1.,2*count+1)
    nodes = np.column_stack((t,.1*(1-t*t),np.zeros_like(t)))
    frames = []
    for point in t:
        axis = np.array([1.,-.2*point,0.]);axis/=np.linalg.norm(axis)
        second = np.array([0.,0.,1.])
        frames.append(np.column_stack((axis,second,np.cross(axis,second))))
    return tuple(CurvedBeam3ReferenceGeometry(nodes[i:i+3],np.array(frames[i:i+3]))
                 for i in range(0,2*count,2))


def make_beam(count):
    refs = references(count)
    sections = [DirectedHardeningSectionProbe(np.diag(SECTION),[1.,0.,0.,0.,0.,0.],1e6,1.) for _ in refs]
    beam = NonlinearAssemblyHistoryProbe(refs,[(2*i,2*i+1,2*i+2) for i in range(count)],
        sections,fixed_nodes=(0,2*count),order=8,extent='REFINEMENT16' if count==16 else 'SMALL8')
    pattern = np.zeros((2*count+1,3));pattern[count,1] = -1.
    return beam,pattern


def reference_fields(reference,parameters,*,stride=1):
    """Planar physical section components [N,0,-V,0,M,0].

    Reference material axis 2 is global z; axis 3 is minus the planar normal.
    Hermite slopes come from the independent continuum equations, not the
    discrete beam. Comparing strides 1/2 diagnoses interpolation sensitivity.
    """
    if stride not in (1,2):
        raise ValueError('registered reference interpolation stride required')
    t,y = reference.parameter[::stride],reference.fields[:,::stride]
    slopes = equations(t,y,reference.force,reference.height,reference.axial,reference.shear,reference.bending)
    interpolant = CubicHermiteSpline(t,y.T,slopes.T)
    parameters = np.asarray(parameters)
    if not np.isfinite(parameters).all() or np.any(np.abs(parameters)>1):
        raise ValueError('reference station outside arch domain')
    values = interpolant(-np.abs(parameters))
    side = np.where(parameters<=0,1.,-1.)
    theta = side*values[:,2]
    fx,fy = reference.force[0],side*reference.force[1]
    n = fx*np.cos(theta)+fy*np.sin(theta)
    v = -fx*np.sin(theta)+fy*np.cos(theta)
    resultants = np.column_stack((n,np.zeros_like(n),-v,np.zeros_like(n),values[:,3],np.zeros_like(n)))
    return resultants


def compare_fields(beam,trial,reference):
    assembly = trial.assembly_trial
    _,weights = np.polynomial.legendre.leggauss(beam._order)
    parameters,measures,actual,strains = [],[],[],[]
    for ref,element in zip(beam._references,assembly.response.elements):
        for station in element.stations:
            xi = station.reference_coordinate
            parameters.append(ref.position(xi)[0])
            measures.append(weights[station.index]*ref.jacobian(xi)/2)
            actual.append(station.response.resultants)
            strains.append(station.response.strain)
    parameters,measures,actual,strains = map(np.asarray,(parameters,measures,actual,strains))
    expected = reference_fields(reference,parameters)
    coarser = reference_fields(reference,parameters,stride=2)
    def squared(a):
        return float(np.sum(measures[:,None]*a*a/SECTION))
    denominator = squared(expected)
    if denominator<=0 or not np.isfinite(denominator):
        raise ValueError('positive finite reference work norm required')
    recovery = np.sqrt(squared(actual-expected)/denominator)
    interpolation = np.sqrt(squared(coarser-expected)/denominator)
    physical_energy = float(.5*np.sum(measures*np.einsum('ij,ij->i',actual,strains)))
    work_error = abs(physical_energy-assembly.response.potential)/max(1.,abs(physical_energy),abs(assembly.response.potential))
    if not np.isfinite(physical_energy) or interpolation>1e-6 or work_error>1e-11:
        raise ValueError('reference interpolation or stationary energy-work closure failed')
    if reference.strain_energy<=0:
        raise ValueError('positive continuum strain energy required')
    r = assembly.response.residual.reshape(beam._nodes,6)
    balance = max(np.linalg.norm(r[:,:3].sum(axis=0)),
                  np.linalg.norm((r[:,3:]+np.cross(assembly.positions,r[:,:3])).sum(axis=0)))
    if balance>1e-11:
        raise ValueError('global resultant/moment balance failed')
    return {'recovery_energy_norm_error':float(recovery),
            'physical_energy_relative_error':abs(physical_energy/reference.strain_energy-1),
            'stationary_work_error':float(work_error),'reference_interpolation_error':float(interpolation),
            'global_balance_error':float(balance),'stations':len(parameters)}, {
            'parameters':parameters,'measures':measures,'reference_resultants':expected,
            'coarser_reference_resultants':coarser,
            'actual_resultants':actual,'actual_strains':strains,'physical_energy':physical_energy}


def records(*,count=16,steps=8,progress,publish_raw):
    if type(steps) is not int or not 1<=steps<=8:
        raise ValueError('at most eight registered refinement increments required')
    beam,pattern = make_beam(count)
    driver = BeamContinuationProbe(beam,pattern)
    previous = None
    result = []
    for i in range(steps):
        progress('STEP_START',i)
        trial = driver.trial(.01,max_iterations=16,max_mixed_evaluations=256*count)
        driver.commit(trial)
        current = driver.committed_model
        state = current.committed
        if digest(current.replay())!=digest(trial.assembly_trial.response):
            raise ValueError('accepted-origin replay mismatch')
        if any(h.accumulated!=0 for hs in state.histories for h in hs):
            raise ValueError('elastic refinement acquired plastic history')
        drop = .1-state.positions[count,1]
        previous = continuum(drop,previous=previous,profile='BVP9')
        comparison,samples = compare_fields(beam,trial,previous)
        response = trial.assembly_trial.response
        direction = tangent(spatial_derivative(response)[np.ix_(beam._free,beam._free)],
            beam._external(pattern)[beam._free],trial.tangent,driver._metric)
        full = np.zeros(6*beam._nodes);full[beam._free] = direction[:-1]
        if abs(full[6*count+1])<=1e-12 or previous.load<=0:
            raise ValueError('finite positive branch comparison required')
        row = {'step':i,'crown_drop':float(drop),'load':trial.parameter,'reference_load':previous.load,
               'relative_load_error':abs(trial.parameter/previous.load-1),
               'current_load_slope':float(direction[-1]/(-full[6*count+1])),
               'minimum_free_eigenvalue':float(np.linalg.eigvalsh(response.tangent[np.ix_(beam._free,beam._free)])[0]),
               'equilibrium_error':trial.assembly_trial.residual_norm,'arc_error':trial.arc_residual,
               'iterations':trial.assembly_trial.iterations,'mixed_evaluations':trial.assembly_trial.mixed_evaluations,
               **comparison}
        raw = {'trial':asdict(trial),'reference':asdict(previous),'samples':samples,'comparison':row}
        row = dict(row,raw=publish_raw(i,raw))
        result.append(row)
        progress('STEP_COMPLETE',i)
    return result
