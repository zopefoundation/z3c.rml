##############################################################################
#
# Copyright (c) 2007 Zope Foundation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""RML-specific XML tools

$Id$
"""
__docformat__ = "reStructuredText"
import sys

ERROR_FILE = sys.stderr

class ParseException(Exception):
    pass

class RequiredAttributeMissing(ParseException):

    def __init__(self, element, name):
        self.element = element
        self.name = name

    def __str__(self):
        return "%r attribute of %r element is required but missing." % (
            self.name, self.element.tag)



def reportUnsupportedAttribute(element, name):
    ERROR_FILE.write(
        "'%s' attribute of '%s' element is not yet supported." % (
            name, element.tag)
        )
