from pathlib import Path
ROOT=Path(__file__).resolve().parent;REPO=ROOT.parents[2]
rel='tests/test_r8_e02_distributing_thickness.py';target=ROOT/'checks-v2-bytes'/rel
target.parent.mkdir(parents=True,exist_ok=True);target.open('xb').write((REPO/rel).read_bytes())
source=(ROOT/'probe-v2.py').read_text(encoding='utf-8')
source=source.replace("str(REPO/p) for p in tests", "str(REPO/p)+'::test_saved_legacy_six_decks_metadata_and_parses_are_exact' for p in tests")
source=source.replace('checks-runtime-v2.json','checks-runtime-v3.json').replace('pytest-v2','pytest-v3')
(ROOT/'probe-v3.py').open('x',encoding='utf-8').write(source)
source=(ROOT/'run-checks-v2.py').read_text(encoding='utf-8').replace('probe-v2.py','probe-v3.py').replace("kind+'-v2'","kind+'-v3'")
(ROOT/'run-checks-v3.py').open('x',encoding='utf-8').write(source)
