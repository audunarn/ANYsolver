import sys,json,time,os
from pathlib import Path
sys.path.insert(0,r'C:/Python/Python314/Lib/site-packages')
import openseespy.opensees as ops
before=ops.getNumThreads();returned=ops.setNumThreads(1);after=ops.getNumThreads()
Path(sys.argv[1]).write_text(json.dumps({'pid':os.getpid(),'version':ops.version(),'before':before,'set_return':returned,'after':after,'scope':'import and thread-setting API only; no model, element or analysis'},indent=2))
time.sleep(2)
