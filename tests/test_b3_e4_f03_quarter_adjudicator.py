"""Bounded independent port integration and crossing preflight for F03."""

import json
from pathlib import Path
from dataclasses import fields
import sys

import numpy as np
import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import _b3_e4_f03_independent_shell as shell
import _b3_e4_f03_independent_line as line
import adjudicate_b3_ge_e4_pl_g0_f03_quarter_refinement_v1 as adjudicator
import _b3_e4_f03_loaded_preflight as loaded


@pytest.mark.parametrize('nm',(16,32,64))
@pytest.mark.parametrize('topology',('Q4','CST-CB'))
def test_first_quarter_physical_port_bands_match_independent_polynomials(nm,topology):
    model=shell.panel(32,64,topology)
    overlay=line.overlay(model,512,nm)
    s=np.arange(nm+1)/nm
    lam=np.column_stack((1e5*(1+s),1e5*(1-2*s),1e4*(s+.5))).ravel()
    bands,quarters=adjudicator._port_bands(lam,nm,overlay)

    def analytic(a,b):
        return [1e5*((b-a)+(b*b-a*a)/2),
                1e5*((b-a)-(b*b-a*a)),
                1e5*((b*b-a*a)/2-2*(b**3-a**3)/3),
                line.YAW_LENGTH*1e4*((b*b-a*a)/2+(b-a)/2)]

    for i,actual in enumerate(bands):
        np.testing.assert_allclose(actual,analytic(i/32,(i+1)/32),
                                   rtol=1e-12,atol=1e-8)
    for i,actual in enumerate(quarters):
        np.testing.assert_allclose(actual,analytic(i/4,(i+1)/4),
                                   rtol=1e-12,atol=1e-8)
    if nm==16:
        assert all(abs(edge*nm-round(edge*nm))==.5
                   for edge in adjudicator.S_EDGES[1::2])


@pytest.mark.parametrize('nm',(16,32,64))
def test_ns32_first_quarter_crossing_sides_are_bounded(nm):
    cb=shell.panel(32,64,'CST-CB')
    q=np.zeros(cb.dof_count)
    crossings=adjudicator._crossings(cb,nm,q,q)
    json.dumps(crossings,allow_nan=False)
    assert crossings
    assert {item['branch'] for item in crossings}=={'rising','falling'}
    assert {item['sample'] for item in crossings}=={0,1,2,3}
    for item in crossings:
        assert 0<item['s']<.25 and 0<item['epsilon']<=1e-6
        assert all(np.isfinite(value)
                   for key in ('pose_left','pose_right','derivative_left',
                               'derivative_right','q4_pose_left','q4_pose_right',
                               'q4_derivative_left','q4_derivative_right')
                   for value in item[key])


def test_piecewise_p1_hat_multiplier_integrates_across_cell_and_band_knots():
    nm=16
    model=shell.panel(32,64,'CST-CB')
    overlay=line.overlay(model,512,nm)
    lam=np.zeros((nm+1,3))
    lam[1]=(350.,-720.,130.)
    lam[2]=(-90.,280.,-45.)
    lam[3]=(510.,-610.,75.)
    actual,_=adjudicator._port_bands(lam.ravel(),nm,overlay)
    roots,weights=np.polynomial.legendre.leggauss(3)
    for band,(a,b) in enumerate(zip(adjudicator.S_EDGES[:-1],
                                     adjudicator.S_EDGES[1:])):
        expected=np.zeros(4)
        for cell in range(nm):
            lo=max(a,cell/nm); hi=min(b,(cell+1)/nm)
            if hi<=lo:
                continue
            for node,weight in zip(roots,weights):
                s=(lo+hi)/2+(hi-lo)*node/2
                xi=nm*s-cell
                density=(1-xi)*lam[cell]+xi*lam[cell+1]
                expected+=(hi-lo)*weight/2*np.array((density[0],density[1],
                                                      s*density[1],
                                                      line.YAW_LENGTH*density[2]))
        np.testing.assert_allclose(actual[band],expected,rtol=1e-12,atol=1e-10)
    assert any(np.linalg.norm(row)>1 for row in actual)


def _independent_cb_pose_slope(model, displacement, s):
    """Hand geometric barycentric gradient, without shell.sample/pose."""
    slopes=[]
    for dx,dy in shell.OFFSETS:
        x=s+dx
        i=min(max(int(np.floor((x+.5)*model.n_s)),0),2*model.n_s-1)
        j=min(max(int(np.floor((dy+.5)*model.n_y)),0),model.n_y-1)
        bl=j*(2*model.n_s+1)+i; br=bl+1
        tl=bl+2*model.n_s+1; tr=tl+1
        candidates=((bl,br,tl),(br,tr,tl)) if (i+j)%2 else (
            (bl,br,tr),(bl,tr,tl))
        for indices in candidates:
            xyz=model.nodes[list(indices)]
            basis=np.column_stack((np.ones(3),xyz))
            weights=np.linalg.solve(basis.T,[1.,x,dy])
            if min(weights)>=-1e-10:
                slopes.append(np.linalg.solve(basis,displacement[2*np.array(indices)+1])[1])
                break
        else:
            raise AssertionError('no independent triangle host')
    offsets=np.asarray(shell.OFFSETS)
    return np.array((0.,np.mean(slopes),
                     line.YAW_LENGTH*(offsets[:,0]@slopes)/shell.YAW_DENOMINATOR))


def test_nonaffine_rising_and_falling_crossing_derivatives_are_independent():
    model=shell.panel(32,64,'CST-CB')
    q=np.zeros(model.dof_count)
    x,y=model.nodes.T
    q[1::2]=1e-3*(x*x+.4*x*y*y)
    crossings=adjudicator._crossings(model,16,q,q)
    checked=set()
    for item in crossings:
        if item['branch'] in checked:
            continue
        s=item['s']; eps=item['epsilon']
        for side,station in (('left',s-.75*eps),('right',s+.75*eps)):
            expected=_independent_cb_pose_slope(model,q,station)
            np.testing.assert_allclose(item[f'derivative_{side}'],expected,
                                       rtol=2e-6,atol=2e-9)
        checked.add(item['branch'])
    assert checked=={'rising','falling'}


def test_signed_channel_inventory_and_all_three_adjacent_sweeps():
    channels={}
    for ns,ny,nm,topology in adjudicator.CASES:
        value=float((ns+ny+nm)*(2 if topology=='CST-CB' else 1))
        observed={field.name:value for field in fields(loaded.LoadedObservables)}
        observed.update(phase='loaded_observables',elapsed_seconds=1.,rss_bytes=123)
        entry=dict(observed=observed,edge_bands=[[value]],
                   root_terms={'elastic':[value],'port':[value],
                               'external':[value]},first_eighth_port=[[value]],
                   port_quarters=[[value]],
                   fixed_first_quarter_station_pose=[[value]])
        channels[adjudicator.case_name(ns,ny,nm,topology)]=adjudicator._channels(entry)
    assert len(channels)==14
    assert all('observed.phase' not in row and
               'observed.elapsed_seconds' not in row for row in channels.values())
    sweeps=adjudicator._sweeps(channels)
    assert set(sweeps)=={'transverse','longitudinal','multiplier'}
    field='observed.shell_energy_joule'
    for rows in sweeps.values():
        assert len(rows)==2
        for row in rows:
            change=sum(row['to_mesh'])-sum(row['from_mesh'])
            assert row['q4_change'][field]==change
            assert row['cb_change'][field]==2*change
            assert row['signed_pair_change'][field]==change


def test_historical_parity_vector_has_exact_twenty_three_signed_channels():
    observed=dict(shell_energy_joule=1.,beam_energy_joule=2.,
                  beam_tip_displacement_metre=(3.,4.,5.),
                  shell_station_displacements_metre=((6.,7.,8.),
                                                    (9.,10.,11.),
                                                    (12.,13.,14.)),
                  support_wrenches=((15.,16.,17.),(18.,19.,20.),
                                    (21.,22.,23.)))
    np.testing.assert_array_equal(adjudicator._historical_vector(observed),
                                  np.arange(1,24))


def test_case_receipt_binds_all_six_raw_files(tmp_path):
    case=adjudicator.CASES[0]
    name=adjudicator.case_name(*case)
    registration=tmp_path/'registration.json'
    registration.write_text('{}',encoding='utf-8')
    root=tmp_path/name
    root.mkdir()
    mapping=dict(manifest_sha256='manifest.json',payload_sha256='solved_state.npz',
                 phases_sha256='phases.jsonl',result_sha256='result.json',
                 stderr_sha256='stderr.log',rss_sha256='rss.jsonl')
    check=dict(status='CASE_CHECK_ACCEPTED_DIAGNOSTIC_ONLY',name=name,
               registration_sha256=adjudicator._sha(registration),
               adjudicator_sha256=adjudicator._sha(Path(adjudicator.__file__)))
    for key,filename in mapping.items():
        (root/filename).write_bytes(filename.encode())
        check[key]=adjudicator._sha(root/filename)
    receipt=tmp_path/f'f03-quarter-check-{name}'
    receipt.mkdir()
    (receipt/'case_check.json').write_text(json.dumps(check),encoding='utf-8')
    assert adjudicator._checked_case(registration,tmp_path,case)==check
    for filename in mapping.values():
        original=(root/filename).read_bytes()
        (root/filename).write_bytes(original+b' changed')
        with pytest.raises(AssertionError):
            adjudicator._checked_case(registration,tmp_path,case)
        (root/filename).write_bytes(original)


def test_case_check_rejects_changed_adjudicator_before_reading_case(tmp_path):
    registration=tmp_path/'registration.json'
    registration.write_text(json.dumps(dict(adjudicator_sha256='wrong')),
                            encoding='utf-8')
    with pytest.raises(AssertionError):
        adjudicator.check_case(registration,tmp_path,
                               adjudicator.case_name(*adjudicator.CASES[0]))
