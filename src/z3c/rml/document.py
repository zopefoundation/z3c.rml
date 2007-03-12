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
"""RML ``document`` element

$Id$
"""
__docformat__ = "reStructuredText"
import sys

from z3c.rml import attr, element, error
from z3c.rml import canvas, stylesheet, template


class Document(element.Element):

    def __init__(self, element):
        self.element = element

    def process(self, outputFile=None):
        """Process document"""
        if outputFile is None:
            # TODO: This is relative to the input file *not* the CWD!!!
            outputFile = open(self.element.get('filename'), 'w')

        if self.element.find('pageDrawing') is not None:
            canvas.Canvas(self.element).process(outputFile)

        if self.element.find('template') is not None:
            template.Template(self.element).process(outputFile)
