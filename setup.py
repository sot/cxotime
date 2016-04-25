from setuptools import setup

from cxotime import __version__

setup(name='cxotime',
      author='Tom Aldcroft',
      description='Chandra Time class base on astropy Time',
      author_email='taldcroft@cfa.harvard.edu',
      version=__version__,
      packages=['cxotime'],
      )
