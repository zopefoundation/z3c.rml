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
"""RML to PDF Converter

$Id$
"""
__docformat__ = "reStructuredText"
import os
import sys
import zope.interface
from lxml import etree
from z3c.rml import document, interfaces

zope.interface.moduleProvides(interfaces.IRML2PDF)


def go(xmlInputName, outputFileName=None, outDir=None, dtdDir=None):
    if dtdDir is not None:
        sys.stderr.write('The ``dtdDir`` option is not yet supported.')

    xmlFile = open(xmlInputName, 'r')
    root = etree.parse(xmlFile).getroot()
    doc = document.Document(root)

    outputFile = None

    # If an output filename is specified, create an output filepointer for it
    if outputFileName is not None:
        if outDir is not None:
            outputFileName = os.path.join(outDir, outputFileName)
        outputFile = open(outputFileName, 'w')

    # Create a Reportlab canvas by processing the document
    doc.process(outputFile)


if __name__ == '__main__':
    canvas = go(sys.argv[1])
