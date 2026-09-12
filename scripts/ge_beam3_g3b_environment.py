"""Build/verify an isolated G3b dependency capsule; never modify sibling repos."""
import argparse
from hashlib import sha256
import importlib.metadata
import io
import os
from pathlib import Path
import platform
import shutil
import stat
import subprocess
import sys
import time
import zipfile

from ge_beam3_g3b_confirmation_authority import canonical,strict

ROOT=Path(__file__).resolve().parents[1]
SIBLINGS=(
    ("ANYmaterial","anymaterial","d8a233ef4c5e38d25dbba0eb20e6cfa8d44ec5a2"),
    ("ANYfileIO","anyfileio","b48ba51c7b79e6d64b3f99c1fb131b9b602e7e1d"),
    ("ANYgeometry","anygeometry","7edbb8b624d3f7d4548d2ec11b2d00c55f1265d2"),
    ("ANYmesh","anymesher","8c66f5ace788e690b910fd4e2a5463ab65e18fa3"))
DISTRIBUTIONS=("numpy","scipy","numba","llvmlite","pytest","pluggy","iniconfig",
               "packaging","Pygments","colorama","threadpoolctl","PyYAML","charset-normalizer")


def regular(path):
    path=Path(path).absolute()
    for item in (path,*path.parents):
        if item.exists() and item.lstat().st_file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT:
            raise ValueError("reparse input/output path")
    if not path.is_file(): raise ValueError("regular file required: "+str(path))
    return path


def digest(path):
    path=regular(path); h=sha256(); size=0
    with path.open("rb") as stream:
        while block:=stream.read(1024*1024): size+=len(block); h.update(block)
    return dict(bytes=size,sha256=h.hexdigest())


def write(path,data):
    with Path(path).open("xb") as stream:
        stream.write(data); stream.flush(); os.fsync(stream.fileno())


def git_env():
    env={k:v for k,v in os.environ.items() if not k.startswith("GIT_")}
    env.update(GIT_CONFIG_NOSYSTEM="1",GIT_CONFIG_SYSTEM=os.devnull,GIT_CONFIG_GLOBAL=os.devnull,
               GIT_NO_REPLACE_OBJECTS="1",GIT_ATTR_NOSYSTEM="1")
    return env


def git(repo,*args):
    exe=shutil.which("git")
    if not exe: raise ValueError("Git launcher unavailable")
    return subprocess.check_output([exe,"-c","safe.directory="+Path(repo).as_posix(),
        "-c","core.attributesFile="+os.devnull,"-C",str(repo),*args],env=git_env(),timeout=30)


def git_identity():
    launcher=Path(shutil.which("git")).resolve()
    exec_path=Path(git(ROOT,"--exec-path").decode().strip())
    engine=exec_path/"git.exe"
    return dict(launcher=dict(path=str(launcher),**digest(launcher)),
                engine=dict(path=str(engine),**digest(engine)))


def runtime_files():
    base=Path(sys.base_prefix)
    files=set(base.glob("*.dll"))|{Path(sys.executable)}
    for directory in (base/"Lib",base/"DLLs"):
        for parent,dirs,names in os.walk(directory):
            dirs[:]=sorted(d for d in dirs if d not in ("site-packages","__pycache__"))
            for name in names:
                p=Path(parent)/name
                if p.suffix.lower() in (".py",".pyd",".dll",".zip"):
                    files.add(p)
    return {str(p.resolve()):digest(p) for p in sorted(files)}


def scan(directory):
    files={}
    for parent,dirs,names in os.walk(directory):
        dirs.sort()
        for name in sorted(names):
            path=Path(parent)/name
            files[path.relative_to(directory).as_posix()]=digest(path)
    return dict(sorted(files.items()))


def capture(output):
    output=Path(output).absolute()
    if output.exists() or output.is_relative_to(ROOT): raise ValueError("fresh external capsule required")
    deadline=time.monotonic()+600
    def check():
        if time.monotonic()>=deadline: raise TimeoutError("capsule capture deadline")
    output.mkdir(parents=True,exist_ok=False); site=output/"site"; site.mkdir()
    versions={}; sources=[]
    for name in DISTRIBUTIONS:
        check(); dist=importlib.metadata.distribution(name)
        if not dist.files: raise ValueError("installed distribution RECORD required")
        versions[name]=dist.version
        origin=Path(dist.locate_file("")).resolve()
        for entry in dist.files:
            if "__pycache__" in entry.parts or entry.suffix==".pyc": continue
            source=Path(dist.locate_file(entry)).resolve()
            if not source.is_relative_to(origin):
                # Console entry scripts are not part of the import capsule.
                if "Scripts" in source.parts: continue
                raise ValueError("distribution file escapes install root")
            rel=source.relative_to(origin)
            if source.suffix==".pth": raise ValueError("ambient path hook forbidden")
            target=site/rel; target.parent.mkdir(parents=True,exist_ok=True)
            before=digest(source)
            if target.exists():
                if digest(target)!=before: raise ValueError("conflicting distribution files")
            else:
                with source.open("rb") as src,target.open("xb") as dst: shutil.copyfileobj(src,dst)
            if digest(source)!=before or digest(target)!=before: raise ValueError("changed distribution during capture")
        print("CAPSULE installed "+name,flush=True)
    for repo,package,commit in SIBLINGS:
        check(); location=Path("C:/Github")/repo
        archive=git(location,"archive","--format=zip",commit,"src/"+package)
        tree=git(location,"rev-parse",commit+"^{tree}").decode().strip()
        sources.append(dict(repository=repo,commit=commit,tree=tree,package=package,
                            archive_sha256=sha256(archive).hexdigest()))
        with zipfile.ZipFile(io.BytesIO(archive)) as z:
            for info in z.infolist():
                if info.is_dir(): continue
                relative=Path(info.filename)
                if relative.parts[:2]!=("src",package) or ".." in relative.parts:
                    raise ValueError("unsafe source archive entry")
                if stat.S_ISLNK(info.external_attr>>16): raise ValueError("source symlink forbidden")
                target=site/Path(*relative.parts[1:]); target.parent.mkdir(parents=True,exist_ok=True)
                write(target,z.read(info))
        print("CAPSULE committed source "+repo+" "+commit,flush=True)
    check()
    body=dict(schema="G3B_ISOLATED_IMPORT_CAPSULE_V1",python_version=sys.version,
        platform=platform.platform(),runtime=runtime_files(),git=git_identity(),
        distributions=versions,siblings=sources,files=scan(site))
    check(); write(output/"environment.json",canonical(body))
    print("ENVIRONMENT "+str(output/"environment.json"),flush=True)
    print(digest(output/"environment.json"),flush=True)
    return body


def verify(path,expected_hash):
    raw=regular(path).read_bytes()
    if sha256(raw).hexdigest()!=expected_hash: raise ValueError("environment authority hash mismatch")
    body=strict(raw)
    if (type(body) is not dict or set(body)!={"schema","python_version","platform","runtime","git",
            "distributions","siblings","files"} or body["schema"]!="G3B_ISOLATED_IMPORT_CAPSULE_V1" or
            body["python_version"]!=sys.version or body["platform"]!=platform.platform() or
            body["git"]!=git_identity() or body["runtime"]!=runtime_files() or
            body["files"]!=scan(Path(path).parent/"site")):
        raise ValueError("frozen import environment mismatch")
    if set(body["distributions"])!=set(DISTRIBUTIONS) or [
            (r["repository"],r["package"],r["commit"]) for r in body["siblings"]]!=list(SIBLINGS):
        raise ValueError("environment registry mismatch")
    return body


if __name__=="__main__":
    p=argparse.ArgumentParser(); p.add_argument("--capture",type=Path,required=True)
    capture(p.parse_args().capture)
