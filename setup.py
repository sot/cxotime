# Licensed under a 3-clause BSD style license - see LICENSE.rst
import sys

from setuptools import Extension, setup

try:
    from testr.setup_helper import cmdclass
except ImportError:
    cmdclass = {}

# NOTE: add '-Rpass-missed=.*' to ``extra_compile_args`` when compiling with clang
# to report missed optimizations.
if sys.platform.startswith('win'):
    extra_compile_args = []
    extra_link_args = ['/EXPORT:parse_ymdhms_times', '/EXPORT:check_unicode']
else:
    extra_compile_args = ['-fPIC']
    extra_link_args = []

# Set up extension for C-based time parser. Numpy is required for build but is
# optional for other things like `python setup.py --version`.
try:
    import numpy

    ext_modules = [
        Extension(
            name='cxotime.parse_times',
            sources=['cxotime/parse_times.c'],
            extra_compile_args=extra_compile_args,
            extra_link_args=extra_link_args,
            include_dirs=[numpy.get_include()],
            language='c',
        )
    ]
except ImportError:
    ext_modules = []

entry_points = {
    "console_scripts": [
        "cxotime = cxotime.cxotime:print_time_conversions",
    ]
}

setup(
    name='cxotime',
    author='Tom Aldcroft',
    description='Chandra Time class base on astropy Time',
    author_email='taldcroft@cfa.harvard.edu',
    use_scm_version=True,
    ext_modules=ext_modules,
    setup_requires=['setuptools_scm', 'setuptools_scm_git_archive'],
    zip_safe=False,
    packages=['cxotime', 'cxotime.tests'],
    tests_require=['pytest'],
    cmdclass=cmdclass,
    entry_points=entry_points,
)
