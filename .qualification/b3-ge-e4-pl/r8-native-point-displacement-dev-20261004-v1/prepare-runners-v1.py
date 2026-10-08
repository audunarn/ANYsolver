from pathlib import Path
raw=Path(__file__).resolve().parent
previous=raw.parent/'r8-point-zero-reference-dev-20261004-v1'
build=(previous/'build-installed-v2.py').read_text(encoding='utf-8')
build=build.replace('solver-dist-v2','solver-dist-v1').replace('site-v2','site-v1').replace('artifact-v2.json','artifact-v1.json').replace('solver-build-v2.log','solver-build-v1.log').replace('install-v2.log','install-v1.log')
build=build.replace("source_parent='cab437fb'","source_parent='33c01791'").replace('isolated zero-reference development candidate','isolated native point displacement development candidate')
(raw/'build-installed-v1.py').write_text(build,encoding='utf-8')
wrapper=(previous/'run-installed-v1.py').read_text(encoding='utf-8')
wrapper=wrapper.replace("site = root/'site-v2'","site = root/'site-v1'")
(raw/'run-installed-v1.py').write_text(wrapper,encoding='utf-8')
build_wrapper=wrapper.replace("site = root/'site-v1'\n",'').replace("module.ENV['PYTHONPATH'] = os.pathsep.join((str(site),str(root.parents[2])))\n",'')
build_wrapper=build_wrapper.replace("str(root/'probe-installed-v1.py')","str(root/'build-installed-v1.py')").replace("'installed-v1',2*1024**3","'build-v1',2*1024**3")
(raw/'run-build-v1.py').write_text(build_wrapper,encoding='utf-8')
print('Prepared pinned isolated build/installed runners; no numerical job started.')
