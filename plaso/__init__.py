# -*- coding: utf-8 -*-

__version__ = '1.4.0'

VERSION_DEV = False
VERSION_DATE = '20160123'


def GetVersion():
  """Returns version information for plaso."""
  if not VERSION_DEV:
    return __version__

  return u'{0:s}_{1:s}'.format(__version__, VERSION_DATE)
