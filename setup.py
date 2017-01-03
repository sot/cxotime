from setuptools import setup

from cxotime import __version__

try:
    from testr.setup_helper import cmdclass
except ImportError:
    cmdclass = {}

setup(name='cxotime',
      author='Tom Aldcroft',
      description='Chandra Time class base on astropy Time',
      author_email='taldcroft@cfa.harvard.edu',
      version=__version__,
      zip_safe=False,
      packages=['cxotime', 'cxotime.tests'],
      tests_require=['pytest'],
      cmdclass=cmdclass,
      )
