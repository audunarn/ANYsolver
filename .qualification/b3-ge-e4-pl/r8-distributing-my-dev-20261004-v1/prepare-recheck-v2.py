from pathlib import Path
ROOT=Path(__file__).resolve().parent
text=(ROOT/'recheck.py').read_text(encoding='utf-8').replace('import pytest','import numpy as np,pytest').replace('recheck-runtime.json','recheck-runtime-v2.json').replace('pytest-recheck','pytest-recheck-v2')
(ROOT/'recheck-v2.py').open('x',encoding='utf-8',newline='').write(text)
text=(ROOT/'run-recheck.py').read_text(encoding='utf-8').replace("'recheck.py'","'recheck-v2.py'").replace("'recheck',2*","'recheck-v2',2*")
(ROOT/'run-recheck-v2.py').open('x',encoding='utf-8',newline='').write(text)
