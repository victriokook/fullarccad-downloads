from pathlib import Path
from Cython.Build import cythonize
from setuptools import Extension
import os
root=Path(__file__).resolve().parent
modules=[Extension(p.stem,[str(p)]) for p in (root/'source-runtime').glob('*.py')]
cythonize(modules,build_dir=str(root/'private-build'/'cython'),nthreads=min(4,os.cpu_count() or 1),compiler_directives={'language_level':3,'binding':True,'annotation_typing':False,'infer_types':False,'embedsignature':False},quiet=True)
print('Cython translation passed:',len(modules))
