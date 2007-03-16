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
import zope.interface
from reportlab.pdfbase import pdfmetrics, ttfonts, cidfonts
from z3c.rml import attr, element, error, interfaces
from z3c.rml import canvas, stylesheet, template


class RegisterType1Face(element.Element):
    args = ( attr.Attribute('afmFile'), attr.Attribute('pfbFile') )

    def process(self):
        args = element.extractPositionalArguments(self.args, self.element, self)
        face = pdfmetrics.EmbeddedType1Face(*args)
        pdfmetrics.registerTypeFace(face)


class RegisterFont(element.Element):
    args = (
        attr.Attribute('name'),
        attr.Attribute('faceName'),
        attr.Attribute('encName') )

    def process(self):
        args = element.extractPositionalArguments(self.args, self.element, self)
        font = pdfmetrics.Font(*args)
        pdfmetrics.registerFont(font)


class RegisterTTFont(element.Element):
    args = (
        attr.Attribute('faceName'),
        attr.Attribute('fileName') )

    def process(self):
        args = element.extractPositionalArguments(self.args, self.element, self)
        font = ttfonts.TTFont(*args)
        pdfmetrics.registerFont(font)


class RegisterCidFont(element.Element):
    args = ( attr.Attribute('faceName'), )

    def process(self):
        args = element.extractPositionalArguments(self.args, self.element, self)
        pdfmetrics.registerFont(cidfonts.UnicodeCIDFont(*args))


class ColorDefinition(element.FunctionElement):
    args = (
        attr.Text('id'),
        attr.Color('RGB'), )

    def process(self):
        id, value = self.getPositionalArguments()
        manager = attr.getManager(self, interfaces.IColorsManager)
        manager.colors[id] = value


class DocInit(element.ContainerElement):

    subElements = {
        'registerType1Face': RegisterType1Face,
        'registerFont': RegisterFont,
        'registerTTFont': RegisterTTFont,
        'registerCidFont': RegisterCidFont,
        'color': ColorDefinition,
        }


class Document(element.ContainerElement):
    zope.interface.implements(
        interfaces.INamesManager,
        interfaces.IStylesManager,
        interfaces.IColorsManager)

    subElements = {
        'docinit': DocInit
        }

    def __init__(self, element):
        self.element = element
        self.names = {}
        self.styles = {}
        self.colors = {}

    def process(self, outputFile=None):
        """Process document"""
        if outputFile is None:
            # TODO: This is relative to the input file *not* the CWD!!!
            outputFile = open(self.element.get('filename'), 'w')

        self.processSubElements(None)

        if self.element.find('pageDrawing') is not None:
            canvas.Canvas(self.element, self, None).process(outputFile)

        if self.element.find('template') is not None:
            template.Template(self.element, self, None).process(outputFile)
