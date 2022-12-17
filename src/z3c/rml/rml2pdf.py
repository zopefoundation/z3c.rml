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
"""
import argparse
import io
import os
import sys

import zope.interface
from lxml import etree

from z3c.rml import document
from z3c.rml import interfaces


zope.interface.moduleProvides(interfaces.IRML2PDF)


def parseString(xml, removeEncodingLine=True, filename=None):
    if isinstance(xml, str) and removeEncodingLine:
        # RML is a unicode string, but oftentimes documents declare their
        # encoding using <?xml ...>. Unfortuantely, I cannot tell lxml to
        # ignore that directive. Thus we remove it.
        if xml.startswith('<?xml'):
            xml = xml.split('\n', 1)[-1]
    root = etree.fromstring(xml)
    doc = document.Document(root)
    if filename:
        doc.filename = filename
    output = io.BytesIO()
    doc.process(output)
    output.seek(0)
    return output


def go(xmlInputName, outputFileName=None, outDir=None, dtdDir=None):
    if dtdDir is not None:
        sys.stderr.write('The ``dtdDir`` option is not yet supported.\n')

    if hasattr(xmlInputName, 'read'):
        # it is already a file-like object
        xmlFile = xmlInputName
        xmlInputName = 'input.pdf'
        should_close_xml = False
    else:
        xmlFile = open(xmlInputName, 'rb')
        should_close_xml = True
    root = etree.parse(xmlFile).getroot()
    doc = document.Document(root)
    doc.filename = xmlInputName

    outputFile = None

    # If an output filename is specified, create an output filepointer for it
    if outputFileName is not None:
        if hasattr(outputFileName, 'write'):
            # it is already a file-like object
            outputFile = outputFileName
            outputFileName = 'output.pdf'
            should_close_output = False
        else:
            if outDir is not None:
                outputFileName = os.path.join(outDir, outputFileName)
            outputFile = open(outputFileName, 'wb')
            should_close_output = True

    # Create a Reportlab canvas by processing the document
    try:
        doc.process(outputFile)
    finally:
        if outputFile and should_close_output:
            outputFile.close()
        if should_close_xml:
            xmlFile.close()


def main(args=None):
    if args is None:
        parser = argparse.ArgumentParser(
            prog='rml2pdf',
            description='Converts file in RML format into PDF file.',
            epilog='Copyright (c) 2007 Zope Foundation and Contributors.'
        )
        parser.add_argument('xmlInputName', help='RML file to be processed')
        parser.add_argument(
            'outputFileName',
            nargs='?',
            help='output PDF file name')
        parser.add_argument('outDir', nargs='?', help='output directory')
        parser.add_argument(
            'dtdDir',
            nargs='?',
            help='directory with XML DTD (not yet supported)')
        pargs = parser.parse_args()
        args = (
            pargs.xmlInputName,
            pargs.outputFileName,
            pargs.outDir,
            pargs.dtdDir)

    go(*args)


if __name__ == '__main__':
    canvas = go(sys.argv[1])
