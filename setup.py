"""Optional CP311 Windows guard; unsupported hosts retain the Python package."""
import hashlib
import os
from pathlib import Path
import platform
import sys
from setuptools import Extension,setup

extensions=[]
if (sys.platform=='win32' and sys.version_info[:2]==(3,11)
        and platform.machine().upper() in ('AMD64','X86_64')
        and os.environ.get('ANYSOLVER_BUILD_NATIVE_GUARD','1')!='0'):
    source=Path('src/anysolver/_native_guard.cpp')
    digest=hashlib.sha256(source.read_bytes()).hexdigest()
    extensions=[Extension('anysolver._native_guard',[str(source)],language='c++',optional=True,
        define_macros=[('ANYSOLVER_GUARD_SOURCE_SHA','"'+digest+'"')],
        extra_compile_args=['/std:c++17','/O2','/EHsc'])]
setup(ext_modules=extensions)
