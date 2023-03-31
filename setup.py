# Licensed under a 3-clause BSD style license - see LICENSE.rst
from setuptools import setup

try:
    from testr.setup_helper import cmdclass
except ImportError:
    cmdclass = {}

entry_points = {
    "console_scripts": [
        "cxotime = cxotime.scripts.print_time_conversions:main",
    ]
}

setup(
    name="cxotime",
    author="Tom Aldcroft",
    description="Chandra Time class base on astropy Time",
    author_email="taldcroft@cfa.harvard.edu",
    use_scm_version=True,
    setup_requires=["setuptools_scm", "setuptools_scm_git_archive"],
    zip_safe=False,
    packages=["cxotime", "cxotime.tests"],
    tests_require=["pytest"],
    cmdclass=cmdclass,
    entry_points=entry_points,
)
