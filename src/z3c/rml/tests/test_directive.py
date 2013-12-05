###############################################################################
#
# Copyright (c) 2012 Zope Foundation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
###############################################################################
"""Tests for the Book Documentation Module"""

import doctest
import unittest

bad_rml = '''\
<document filename="bad.pdf">
  <bad />
</document>
'''

def test_abort_on_invalid_tag():
    """

    We can set a flag that aborts execution when a bad tag/directive is
    encountered:

      >>> from z3c.rml import directive
      >>> directive.ABORT_ON_INVALID_DIRECTIVE = True

    Let's now render a template:

      >>> from z3c.rml import rml2pdf
      >>> rml2pdf.parseString(bad_rml, True, 'bad.rml')
      Traceback (most recent call last):
      ...
      ValueError: Directive 'bad' could not be processed and was ignored.
      (file bad.rml, line 2)

    Cleanup:

      >>> directive.ABORT_ON_INVALID_DIRECTIVE = False

    """

def test_suite():
    return doctest.DocTestSuite(
        optionflags=doctest.NORMALIZE_WHITESPACE|doctest.ELLIPSIS)

