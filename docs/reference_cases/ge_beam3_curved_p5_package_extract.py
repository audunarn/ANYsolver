"""Reproducible, read-only extraction of the internal P5 package candidate.

--emit prints proposed files, never writes them. --check verifies the checked-in
package and source ledger. No mechanics, resource runner or authority execution.
"""

import argparse
import ast
import hashlib
import json
from pathlib import Path
import subprocess


BASE = 'bc4a6dc30a3c2dd1254f4ee6adce4c8ff008ea06'
ROOT = Path(__file__).resolve().parents[2]
TARGET = 'src/anysolver/_ge_beam3_p5'
LEDGER = 'docs/reference_cases/ge_beam3_curved_p5_package_source_map.json'
PREFIX = 'docs/reference_cases/ge_beam3_curved_p5_'

MODULES = {
    'algebra_probe': 'algebra', 'finite_probe': 'arrays', 'section_probe': 'section',
    'nonlinear_mixed_probe': 'mixed', 'compensated_coordinates': 'compensated_coordinates',
    'compensated_mixed': 'compensated', 'native_chart_probe': 'chart',
    'native_material_probe': 'core', 'native_driver_probe': 'element',
    'native_state_codec': 'codec', 'restart_probe': 'typed_schema',
    'factor_probe': 'factors', 'mass_probe': 'mass', 'finite_inertia_probe': 'inertia',
    'native_modal_probe': 'reference_modal', 'native_committed_modal_probe': 'committed_modal',
}
RENAMES = {
    'PrivateP5NativeElement': 'StationaryCore', 'DriverP5Element': 'NativeP5BeamElement',
    'DirectedHardeningSectionProbe': 'DirectedHardeningSection',
    'NonlinearMixedBeamProbe': 'StationaryMixedBeam',
    'CompensatedMixedBeamProbe': 'CompensatedStationaryBeam', 'FiniteInertiaProbe': 'LiftedInertia',
    'CANDIDATE_GE_BEAM3_DC_CURVED_OBJECTIVE_LIFT_NATIVE_DRIVER_V1': 'CANDIDATE_GE_BEAM3_P5_NATIVE_PACKAGE_V1',
    'CANDIDATE_GE_BEAM3_DC_CURVED_OBJECTIVE_LIFT_NATIVE_V1': 'CANDIDATE_GE_BEAM3_P5_PACKAGE_CORE_V1',
    'GE_BEAM3_P5_PRIVATE_DRIVER_STATION_STATE_V1': 'GE_BEAM3_P5_PACKAGE_DRIVER_STATE_V1',
    'GE_BEAM3_P5_PRIVATE_NATIVE_STATION_STATE_V1': 'GE_BEAM3_P5_PACKAGE_STATION_STATE_V1',
    'GE_BEAM3_P5_NATIVE_TYPED_STATE_JSON_V1': 'GE_BEAM3_P5_PACKAGE_TYPED_STATE_JSON_V1',
}
NP = 'import numpy as np\n'
SPECS = {
    'algebra': ('algebra_probe', ['HALVES','skew','rotation','log_rotation','validate_section','CellMetrics','metrics'],
                'from dataclasses import dataclass\nfrom typing import Any\n'+NP),
    'arrays': ('finite_probe', ['_readonly','_array','_frames'], NP),
    'section': ('section_probe', ['_array','SectionHistory','_history','SectionResponse','MixedSectionResponse','DirectedHardeningSectionProbe'],
                'from dataclasses import dataclass\n'+NP),
    'mixed': ('nonlinear_mixed_probe', None, None),
    'compensated_coordinates': ('compensated_coordinates', None, None),
    'compensated': ('compensated_mixed', None, None),
    'chart': ('native_chart_probe', ['_axial','exp_chart_terms','pullback'], NP+
              'from anysolver._ge_beam3_mixed_ad import Jet2, so3_exp\nfrom .algebra import skew\nfrom .arrays import _array, _readonly\n'),
    'core': ('native_material_probe', ['SCHEMA','FORMULATION','canonical','sha','seal','NativeMaterialError','PrivateP5NativeElement'],
             'from copy import deepcopy\nfrom dataclasses import asdict, is_dataclass\nimport hashlib\nimport json\n'+NP+
             'from anysolver.elements import Element\nfrom anysolver.ge_beam3_curved_reference import CurvedBeam3ReferenceGeometry\n'
             'from .compensated import CompensatedStationaryBeam\nfrom .arrays import _array, _frames\n'
             'from .mixed import LocalForceAccuracy\nfrom .section import DirectedHardeningSection, SectionHistory, _history\n'),
    'codec': ('native_state_codec', None, None),
    'element': ('native_driver_probe', None, None),
    'factors': ('factor_probe', ['ReferenceFactors','reference_factors'], 'from dataclasses import dataclass\n'+NP+
                'from .algebra import HALVES, metrics, skew, validate_section\n'),
    'mass': ('mass_probe', ['ReferenceKineticFactors','reference_kinetic_factors'], 'from dataclasses import dataclass\n'+NP+
             'from .algebra import HALVES, skew, validate_section\nfrom .factors import reference_factors\nfrom .arrays import _array, _readonly\n'),
    'inertia': ('finite_inertia_probe', None, None),
    'reference_modal': ('native_modal_probe', None, None),
    'committed_modal': ('native_committed_modal_probe', None, None),
}
CORE_EXCLUDED_METHODS = ('compute_nonlinear_response', '_require_live_view')
HEADER = '"""Internal P5 package candidate; unqualified and not publicly registered.\n\nExtracted mechanically from the bound source map. Do not edit copied mechanics\nwithout a reviewed successor mapping and renewed equivalence checks.\n"""\n\n'


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False)+'\n'


def _name(node):
    if isinstance(node, (ast.FunctionDef, ast.ClassDef)): return node.name
    if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
        return node.targets[0].id
    return None


def _span(node):
    return min([node.lineno]+[d.lineno for d in getattr(node, 'decorator_list', ())])-1, node.end_lineno


def extract():
    sources = {}
    present = subprocess.run(['git','cat-file','-e',BASE+'^{commit}'],cwd=ROOT,capture_output=True).returncode == 0
    shallow_sources = None
    if not present:
        shallow = subprocess.check_output(['git','rev-parse','--is-shallow-repository'],cwd=ROOT).strip()
        if shallow != b'true':
            raise ValueError('missing source base in ordinary local repository')
        raw_ledger = (ROOT/LEDGER).read_text(encoding='utf-8')
        authority = json.loads(raw_ledger)
        if canonical(authority) != raw_ledger or authority['source_commit'] != BASE:
            raise ValueError('invalid shallow source-map authority')
        shallow_sources = authority['sources']
    def read(suffix):
        path = PREFIX+suffix+'.py'
        if present:
            raw = subprocess.check_output(['git','show',BASE+':'+path], cwd=ROOT)
        else:
            raw = (ROOT/path).read_text(encoding='utf-8').encode('utf-8')
            binding = shallow_sources[path]
            if len(raw) != binding['bytes'] or hashlib.sha256(raw).hexdigest() != binding['sha256']:
                raise ValueError('shallow source hash mismatch: '+path)
        text = raw.decode('utf-8').replace('\r\n','\n')
        if (ROOT/path).read_text(encoding='utf-8') != text:
            raise ValueError('bound research source changed: '+path)
        sources[path] = dict(bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())
        return text

    def selected(suffix, names):
        text = read(suffix); lines = text.splitlines(keepends=True); tree = ast.parse(text)
        if names is None:
            # Replace only the module docstring, preserving the rest of the file.
            return ''.join(lines[tree.body[0].end_lineno:]).lstrip('\n')
        chunks = []
        nodes = {_name(n): n for n in tree.body}
        for name in names:
            node = nodes[name]; start, end = _span(node)
            excluded = set()
            if name == 'PrivateP5NativeElement':
                for child in node.body:
                    if _name(child) in CORE_EXCLUDED_METHODS:
                        first, last = _span(child); excluded.update(range(first, last))
            chunks.append(''.join(line for i, line in enumerate(lines[start:end], start) if i not in excluded).rstrip())
        return '\n\n\n'.join(chunks)+'\n'

    def rewrite(text):
        for suffix, destination in sorted(MODULES.items(), key=lambda pair: -len(pair[0])):
            text = text.replace('docs.reference_cases.ge_beam3_curved_p5_'+suffix,
                                'anysolver._ge_beam3_p5.'+destination)
            text = text.replace('from docs.reference_cases import ge_beam3_curved_p5_'+suffix,
                                'from anysolver._ge_beam3_p5 import '+destination)
        for old, new in RENAMES.items(): text = text.replace(old, new)
        if 'docs.reference_cases' in text: raise ValueError('unmapped research dependency')
        ast.parse(text)
        return text

    files = {}
    for destination, (source, names, imports) in SPECS.items():
        content = rewrite(HEADER+(imports+'\n' if imports else '')+selected(source, names))
        files[TARGET+'/'+destination+'.py'] = content
    typed = ('from dataclasses import dataclass\nimport math\nimport numpy as np\n'
             'from .section import SectionHistory, SectionResponse, _history\n'
             'from .mixed import BeamStationTrial, NonlinearCondensedResponse\n\n')
    typed += selected('history_path_probe', ['NonlinearPathState','NonlinearPathTrial'])+'\n'
    typed += selected('restart_probe', ['RestartError','_keys','_pairs','_constant','_decode','_schemas'])
    files[TARGET+'/typed_schema.py'] = rewrite(HEADER+typed)
    files[TARGET+'/__init__.py'] = HEADER+(
        '# Internal import only. No factory alias, root export, or qualification.\n'
        'from .element import NativeP5BeamElement\n'
        'from .section import DirectedHardeningSection\n\n'
        '__all__ = ["NativeP5BeamElement", "DirectedHardeningSection"]\n')
    ledger = dict(schema='GE_BEAM3_P5_PACKAGE_SOURCE_MAP_V1', source_commit=BASE,
        output_text_normalization='UTF8_LF',
        candidate='CANDIDATE_GE_BEAM3_P5_NATIVE_PACKAGE_V1', production_qualified=False,
        sources=sources, selections=SPECS, module_rewrites=MODULES, symbol_and_identity_rewrites=RENAMES,
        excluded_core_methods=CORE_EXCLUDED_METHODS,
        typed_schema_selections=dict(history_path_probe=['NonlinearPathState','NonlinearPathTrial'],
            restart_probe=['RestartError','_keys','_pairs','_constant','_decode','_schemas']),
        outputs={p:dict(bytes=len(t.encode()), sha256=hashlib.sha256(t.encode()).hexdigest()) for p,t in files.items()})
    files[LEDGER] = canonical(ledger)
    return files


def main():
    parser = argparse.ArgumentParser(); group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--emit', action='store_true'); group.add_argument('--check', action='store_true')
    args = parser.parse_args(); files = extract()
    if args.emit: print(canonical(files), end='')
    else:
        for path, content in files.items():
            if (ROOT/path).read_text(encoding='utf-8') != content:
                raise ValueError('extraction mismatch: '+path)
        actual = {p.relative_to(ROOT).as_posix() for p in (ROOT/TARGET).glob('*.py')}
        expected = {p for p in files if p.startswith(TARGET+'/')}
        if actual != expected: raise ValueError('package extent mismatch')
        print(canonical(dict(status='EXTRACTION_EXACT', package_files=len(expected))), end='')


if __name__ == '__main__': main()
