##############################################################################
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
##############################################################################
"""``pdfInclude`` Directive.
"""
__docformat__ = "reStructuredText"
import cStringIO
try:
    import PyPDF2
    from PyPDF2.generic import NameObject
except ImportError:
    PyPDF2 = None
from reportlab.platypus import flowables

from z3c.rml import attr, flowable, interfaces, occurence, page

class ConcatenationPostProcessor(object):

    def __init__(self):
        self.operations = []

    def process(self, inputFile1):
        input1 = PyPDF2.PdfFileReader(inputFile1)
        merger = PyPDF2.PdfFileMerger()
        merger.output._info.getObject().update(input1.documentInfo)

        prev_insert = 0
        for start_page, inputFile2, pages, num_pages in self.operations:
            if prev_insert < start_page:
                merger.append(inputFile1, pages=(prev_insert, start_page))
            if not pages:
                merger.append(inputFile2)
            else:
                # Note, users start counting at 1. ;-)
                for page in pages:
                    merger.append(inputFile2, pages=(page-1, page))
            prev_insert = start_page + num_pages

        input1 = PyPDF2.PdfFileReader(inputFile1)
        num_pages = input1.getNumPages()
        if prev_insert < num_pages:
            merger.append(
                inputFile1, pages=(prev_insert, num_pages))

        outputFile = cStringIO.StringIO()
        merger.write(outputFile)
        return outputFile


class PDFPageFlowable(flowables.Flowable):

    def __init__(self, width, height):
        flowables.Flowable.__init__(self)
        self.width = width
        self.height = height

    def draw(self):
        pass

    def split(self, availWidth, availheight):
        return [self]


class IncludePdfPagesFlowable(flowables.Flowable):

    def __init__(self, pdf_file, pages, concatprocessor):
        flowables.Flowable.__init__(self)
        self.pdf_file = pdf_file
        self.proc = concatprocessor
        self.pages = pages

        self.width = 10<<32
        self.height = 10<<32

    def draw():
        return NotImplementedError('PDFPages shall be drawn not me')

    def split(self, availWidth, availheight):
        pages = self.pages
        if not pages:
            pdf = PyPDF2.PdfFileReader(self.pdf_file)
            num_pages = pdf.getNumPages()
            pages = range(num_pages)
        else:
            num_pages = len(pages)

        start_page = self.canv.getPageNumber()
        self.proc.operations.append(
            (start_page, self.pdf_file, self.pages, num_pages))

        result = []
        for i in pages:
            result.append(flowables.PageBreak())
            result.append(PDFPageFlowable(availWidth, availheight))
        return result


class IIncludePdfPages(interfaces.IRMLDirectiveSignature):
    """Inserts a set of pages from a given PDF."""

    filename = attr.File(
        title=u'Path to file',
        description=u'The pdf file to include.',
        required=True)

    pages = attr.IntegerSequence(
        title=u'Pages',
        description=u'A list of pages to insert.',
        required=False)


class IncludePdfPages(flowable.Flowable):
    signature = IIncludePdfPages

    def getProcessor(self):
        manager = attr.getManager(self, interfaces.IPostProcessorManager)
        procs = dict(manager.postProcessors)
        if 'CONCAT' not in procs:
            proc = ConcatenationPostProcessor()
            manager.postProcessors.append(('CONCAT', proc))
            return proc
        return procs['CONCAT']

    def process(self):
        if PyPDF2 is None:
            raise Exception(
                'PyPDF2 is not installed, so this feature is not available.')
        args = dict(self.getAttributeValues())
        proc = self.getProcessor()
        self.parent.flow.append(
            IncludePdfPagesFlowable(args['filename'], args.get('pages'), proc))


flowable.Flow.factories['includePdfPages'] = IncludePdfPages
flowable.IFlow.setTaggedValue(
    'directives',
    flowable.IFlow.getTaggedValue('directives') +
    (occurence.ZeroOrMore('includePdfPages', IIncludePdfPages),)
    )
