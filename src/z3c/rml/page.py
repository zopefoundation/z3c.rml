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
"""
import six
from z3c.rml import attr, directive, interfaces

try:
    import PyPDF2
    from PyPDF2.generic import NameObject
except ImportError:
    # We don't want to require pyPdf, if you do not want to use the features
    # in this module.
    PyPDF2 = None


if PyPDF2 is not None and six.PY3:
    # Monkey patch PyPDF2 for Python 3 compatibility
    # https://github.com/mstamy2/PyPDF2/pull/172
    class ASCII85Decode(object):
        def decode(data, decodeParms=None):
            if isinstance(data, str):
                data = data.encode('ascii')
            import struct
            n = b = 0
            out = bytearray()
            for c in data:
                if ord('!') <= c and c <= ord('u'):
                    n += 1
                    b = b*85+(c-33)
                    if n == 5:
                        out += struct.pack(b'>L',b)
                        n = b = 0
                elif c == ord('z'):
                    assert n == 0
                    out += b'\0\0\0\0'
                elif c == ord('~'):
                    if n:
                        for _ in range(5-n):
                            b = b*85+84
                        out += struct.pack(b'>L',b)[:n-1]
                    break
            return bytes(out)
        decode = staticmethod(decode)
    PyPDF2.filters.ASCII85Decode = ASCII85Decode


class MergePostProcessor(object):

    def __init__(self):
        self.operations = {}

    def process(self, inputFile1):
        input1 = PyPDF2.PdfFileReader(inputFile1)
        output = PyPDF2.PdfFileWriter()
        # TODO: Do not access protected classes
        output._info.getObject().update(input1.documentInfo)
        if output._root:
            # Backwards-compatible with PyPDF2 version 1.21
            output._root.getObject()[NameObject("/Outlines")] = (
                output._addObject(input1.trailer["/Root"]["/Outlines"]))
        else:
            # Compatible with PyPDF2 version 1.22+
            output._root_object[NameObject("/Outlines")] = (
                output._addObject(input1.trailer["/Root"]["/Outlines"]))
        for (num, page) in enumerate(input1.pages):
            if num in self.operations:
                for mergeFile, mergeNumber in self.operations[num]:
                    merger = PyPDF2.PdfFileReader(mergeFile)
                    mergerPage = merger.getPage(mergeNumber)
                    mergerPage.mergePage(page)
                    page = mergerPage
            output.addPage(page)

        outputFile = six.BytesIO()
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
        if PyPDF2 is None:
            raise Exception(
                'pyPdf is not installed, so this feature is not available.')
        inputFile, inPage = self.getAttributeValues(valuesOnly=True)
        manager = attr.getManager(self, interfaces.ICanvasManager)
        outPage = manager.canvas.getPageNumber()-1

        proc = self.getProcessor()
        pageOperations = proc.operations.setdefault(outPage, [])
        pageOperations.append((inputFile, inPage))


class MergePageInPageTemplate(MergePage):

    def process(self):
        if PyPDF2 is None:
            raise Exception(
                'pyPdf is not installed, so this feature is not available.')
        inputFile, inPage = self.getAttributeValues(valuesOnly=True)

        onPage = self.parent.pt.onPage
        def drawOnCanvas(canvas, doc):
            onPage(canvas, doc)
            outPage = canvas.getPageNumber()-1
            proc = self.getProcessor()
            pageOperations = proc.operations.setdefault(outPage, [])
            pageOperations.append((inputFile, inPage))

        self.parent.pt.onPage = drawOnCanvas
