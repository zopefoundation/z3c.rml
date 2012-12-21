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
try:
    import pyPdf
except ImportError:
    pyPdf = None
from reportlab.platypus import flowables

from z3c.rml import attr, flowable, interfaces, occurence, page


class IncludePdfPagesFlowable(flowables.Flowable):

    def __init__(self, pdf_file, pages, mergeprocessor):
        flowables.Flowable.__init__(self)
        self.pdf_file = pdf_file
        self.proc = mergeprocessor

        pdf = pyPdf.PdfFileReader(pdf_file)
        self.num_pages = pdf.getNumPages()
        self.pages = pages if pages else range(1, self.num_pages+1)

        self.width = 10<<32
        self.height = 10<<32

    def draw():
        return NotImplementedError('PDFPages shall be drawn not me')

    def split(self, availWidth, availheight):
        result = []
        for i in self.pages:
            result.append(flowables.PageBreak())
            result.append(PDFPageFlowable(self, i-1, availWidth, availheight))
        return result


class PDFPageFlowable(flowables.Flowable):

    def __init__(self, parent, pagenumber, width, height):
        flowables.Flowable.__init__(self)
        self.parent = parent
        self.pagenumber = pagenumber
        self.width = width
        self.height = height

    def draw(self):
        # FIXME : scale and rotate ?
        # self.canv.addLiteral(self.page.getContents())
        proc = self.parent.proc
        outPage = self.canv.getPageNumber()-1
        pageOperations = proc.operations.setdefault(outPage, [])
        pageOperations.append((self.parent.pdf_file, self.pagenumber))
        # flowable.NextPage()

    def split(self, availWidth, availheight):
        return [self]

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
        if 'MERGE' not in procs:
            proc = page.MergePostProcessor()
            manager.postProcessors.append(('MERGE', proc))
            return proc
        return procs['MERGE']

    def process(self):
        if pyPdf is None:
            raise Exception(
                'pyPdf is not installed, so this feature is not available.')
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
