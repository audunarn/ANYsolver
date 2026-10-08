from pathlib import Path
root = Path(__file__).resolve().parent
repo = root.parents[2]
proof = root/'staged-proof-v1.json'
(root/'staged-proof-before-encoding-fix-v1.json').open('xb').write(proof.read_bytes())
for name in ('goal','plan'):
    path = repo/f'docs/agent_plans/B3_GE_E4_PL_REVISION_8_{name.upper()}.md'
    current = path.read_bytes()
    marker = b'4 October coupled-chart exit:'
    tail = current[current.rindex(marker):]
    original = (root/(name+'-before-final-v1.bin')).read_bytes().replace(b'\r\n',b'\n')
    path.write_bytes(original+b'\n'+tail)
    assert path.read_bytes().startswith(original)
    path.read_bytes().decode('utf-8')
print('Restored original UTF-8 bytes plus ASCII delta; no historical prose changed.')
