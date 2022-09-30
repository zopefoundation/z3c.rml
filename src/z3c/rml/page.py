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
import io

from z3c.rml import attr
from z3c.rml import directive
from z3c.rml import interfaces


try:
    import pikepdf
    from pikepdf import Object  # noqa: F401 imported but unused
except ImportError:
    # We don't want to require pikepdf, if you do not want to use the features
    # in this module.
    pikepdf = None


def mergePage(layerPage, mainPage, pdf, name) -> None:
    contentsForName = pdf.copy_foreign(
        pikepdf.Page(layerPage).as_form_xobject()
    )
    newContents = b'q\n %s Do\nQ\n' % (name.encode())
    if not mainPage.Resources.get("/XObject"):
        mainPage.Resources["/XObject"] = pikepdf.Dictionary({})
    mainPage.Resources["/XObject"][name] = contentsForName
    # Use the MediaBox from the merged page
    mainPage.MediaBox = pikepdf.Array(layerPage.MediaBox)
    mainPage.contents_add(
        contents=pikepdf.Stream(pdf, newContents),
        prepend=True
    )


class MergePostProcessor:

    def __init__(self):
        self.operations = {}

    def process(self, inputFile1):
        input1 = pikepdf.open(inputFile1)
        count = 0
        for (num, page) in enumerate(input1.pages):
            if num in self.operations:
                for mergeFile, mergeNumber in self.operations[num]:
                    mergePdf = pikepdf.open(mergeFile)
                    toMerge = mergePdf.pages[mergeNumber]
                    name = f"/Fx{count}"
                    mergePage(toMerge, page, input1, name)

        outputFile = io.BytesIO()
        input1.save(outputFile)
        return outputFile


class IMergePage(interfaces.IRMLDirectiveSignature):
    """Merges an existing PDF Page into the one to be generated."""

    filename = attr.File(
        title='File',
        description=('Reference to the PDF file to extract the page from.'),
        required=True)

    page = attr.Integer(
        title='Page Number',
        description='The page number of the PDF file that is used to merge..',
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
        if pikepdf is None:
            raise Exception(
                'pikepdf is not installed, so this feature is not available.')
        inputFile, inPage = self.getAttributeValues(valuesOnly=True)
        manager = attr.getManager(self, interfaces.ICanvasManager)
        outPage = manager.canvas.getPageNumber() - 1

        proc = self.getProcessor()
        pageOperations = proc.operations.setdefault(outPage, [])
        pageOperations.append((inputFile, inPage))


class MergePageInPageTemplate(MergePage):

    def process(self):
        if pikepdf is None:
            raise Exception(
                'pikepdf is not installed, so this feature is not available.')
        inputFile, inPage = self.getAttributeValues(valuesOnly=True)

        onPage = self.parent.pt.onPage

        def drawOnCanvas(canvas, doc):
            onPage(canvas, doc)
            outPage = canvas.getPageNumber() - 1
            proc = self.getProcessor()
            pageOperations = proc.operations.setdefault(outPage, [])
            pageOperations.append((inputFile, inPage))

        self.parent.pt.onPage = drawOnCanvas
