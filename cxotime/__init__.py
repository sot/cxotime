from .cxotime import CxoTime

__version__ = '0.1'


def test(*args, **kwargs):
    '''
    Run py.test unit tests.
    '''
    import testr
    return testr.test(*args, **kwargs)
