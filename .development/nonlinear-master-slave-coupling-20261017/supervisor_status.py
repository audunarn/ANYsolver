"""Compact inspection of worker events and task-owned evidence; no solves."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
log = ROOT / (sys.argv[1] if len(sys.argv) > 1 else 'supervisor_mistral_implementation_escalated.log')
events = []
turns = set()
for line in log.read_text(encoding='utf-8-sig', errors='replace').splitlines():
    try:
        entry = json.loads(line)
    except (ValueError, TypeError):
        continue
    if not isinstance(entry, dict):
        continue
    if entry.get('turnId'):
        turns.add(entry['turnId'])
    state = entry.get('state', {})
    display = state.get('display', {}) if isinstance(state, dict) else {}
    if display.get('message'):
        events.append({'tool': entry.get('title'), 'success': display.get('success'),
                       'message': str(display['message'])[:180]})
print(json.dumps({'observed_turn_ids': len(turns), 'observed_tool_outcomes': len(events),
                  'recent_tools': events[-5:],
                  'checkpoint_exists': (ROOT/'checkpoint.md').exists()}, indent=2))
for pattern in ('*budget*.json', 'evidence/*/receipt.json', 'evidence/*/result.json'):
    paths = list(ROOT.glob(pattern))
    if paths:
        print(pattern, len(paths), [str(p.relative_to(ROOT)) for p in paths[-5:]])
