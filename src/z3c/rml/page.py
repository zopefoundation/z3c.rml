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
"""Page Drawing Related Element Processing

$Id$
"""
__docformat__ = "reStructuredText"
import cStringIO
from z3c.rml import attr, directive, interfaces

try:
    import pyPdf
except ImportError:
    # We don't want to require pyPdf, if you do not want to use the features
    # in this module.
    pyPdf = None

class MergePostProcessor(object):

    def __init__(self):
        self.operations = {}

    def process(self, inputFile1):
        input1 = pyPdf.PdfFileReader(inputFile1)
        output = pyPdf.PdfFileWriter()
        for (num, page) in enumerate(input1.pages):
            if num in self.operations:
                for mergeFile, mergeNumber in self.operations[num]:
                    merger = pyPdf.PdfFileReader(mergeFile)
                    mergerPage = merger.getPage(mergeNumber)
                    mergerPage.mergePage(page)
                    page = mergerPage
            output.addPage(page)

        outputFile = cStringIO.StringIO()
        output.write(outputFile)
        return outputFile


class IMergePage(interfaces.IRMLDirectiveSignature):
    """Merges an existing PDF Page into the one to be generated."""

    filename = attr.File(
        title=u'File',
        description=(u'Reference to the PDF file to extract the page from.'),
        required=True)

    page = attr.Integer(
        title=u'Page Number',
        description=u'The page number of the PDF file that is used to merge..',
        required=True)


class MergePage(directive.RMLDirective):
    signature = IMergePage

    def getProcessor(self):
        manager = attr.getManager(self, interfaces.IPostProcessorManager)
        procs = dict(manager.postProcessors)
        if 'MERGE' not in procs:
            proc = MergePostProcessor()
            manager.postProcessors.append(('MERGE', proc))
            return proc
        return procs['MERGE']

    def process(self):
        if pyPdf is None:
            raise Exception(
                'pyPdf is not installed, so this feature is not available.')
        inputFile, inPage = self.getAttributeValues(valuesOnly=True)
        manager = attr.getManager(self, interfaces.ICanvasManager)
        outPage = manager.canvas.getPageNumber()-1

        proc = self.getProcessor()
        pageOperations = proc.operations.setdefault(outPage, [])
        pageOperations.append((inputFile, inPage))
