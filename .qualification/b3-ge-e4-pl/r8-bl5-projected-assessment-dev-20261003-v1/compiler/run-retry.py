from pathlib import Path
import importlib.util, json, sys
ROOT = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('source_runner', ROOT/'run.py')
text = (ROOT/'run.py').read_text()
text = text.replace("command = [sys.executable, '-u', str(ROOT/'child.py')]", "command = [sys.executable, '-u', str(ROOT/'child-retry.py')]")
text = text.replace("ROOT/'command.json'", "ROOT/'command-retry.json'")
text = text.replace("'focused-run'", "'restart-retry-run'")
exec(compile(text, str(ROOT/'run.py'), 'exec'))
