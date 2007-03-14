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

from reportlab.pdfbase import pdfmetrics, ttfonts
from z3c.rml import attr, element, error
from z3c.rml import canvas, stylesheet, template


class RegisterType1Face(element.Element):
    args = ( attr.Attribute('afmFile'), attr.Attribute('pfbFile') )

    def process(self):
        args = element.extractPositionalArguments(self.args, self.element)
        face = pdfmetrics.EmbeddedType1Face(*args)
        pdfmetrics.registerTypeFace(face)


class RegisterFont(element.Element):
    args = (
        attr.Attribute('name'),
        attr.Attribute('faceName'),
        attr.Attribute('encName') )

    def process(self):
        args = element.extractPositionalArguments(self.args, self.element)
        font = pdfmetrics.Font(*args)
        pdfmetrics.registerFont(font)


class RegisterTTFont(element.Element):
    args = (
        attr.Attribute('faceName'),
        attr.Attribute('fileName') )

    def process(self):
        args = element.extractPositionalArguments(self.args, self.element)
        font = ttfonts.TTFont(*args)
        pdfmetrics.registerFont(font)


class DocInit(element.ContainerElement):

    subElements = {
        'registerType1Face': RegisterType1Face,
        'registerFont': RegisterFont,
        'registerTTFont': RegisterTTFont,
        }


class Document(element.ContainerElement):

    subElements = {
        'docinit': DocInit
        }

    def __init__(self, element):
        self.element = element

    def process(self, outputFile=None):
        """Process document"""
        if outputFile is None:
            # TODO: This is relative to the input file *not* the CWD!!!
            outputFile = open(self.element.get('filename'), 'w')

        self.processSubElements(None)

        if self.element.find('pageDrawing') is not None:
            canvas.Canvas(self.element).process(outputFile)

        if self.element.find('template') is not None:
            template.Template(self.element).process(outputFile)
