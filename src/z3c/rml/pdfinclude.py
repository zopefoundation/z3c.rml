try:
    import pyPdf
except ImportError:
    pyPdf = None
from reportlab.platypus import flowables

from z3c.rml import attr, flowable, interfaces, occurence, page


class PDFIncludeFlowable(flowables.Flowable):

    def __init__(self, pdf_file, mergeprocessor):
        flowables.Flowable.__init__(self)
        self.pdf_file = pdf_file
        self.proc = mergeprocessor

        pdf = pyPdf.PdfFileReader(pdf_file)
        self.num_pages = pdf.getNumPages()
        self.width = 10<<32
        self.height = 10<<32

    def draw():
        return NotImplementedError('PDFPages shall be drawn not me')

    def split(self, availWidth, availheight):
        result = []
        for i in range(self.num_pages):
            result.append(flowables.PageBreak())
            result.append(PDFPageFlowable(self, i, availWidth, availheight))
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

class IPDFInclude(interfaces.IRMLDirectiveSignature):
    """Inserts a PDF"""

    filename = attr.File(
        title=u'Path to file',
        description=u'The pdf file to include.',
        required=True)


class PDFInclude(flowable.Flowable):
    signature = IPDFInclude

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
        (pdf_file,) = self.getAttributeValues(valuesOnly=True)
        proc = self.getProcessor()
        self.parent.flow.append(PDFIncludeFlowable(pdf_file, proc))


flowable.Flow.factories['pdfInclude'] = PDFInclude
flowable.IFlow.setTaggedValue(
    'directives',
    flowable.IFlow.getTaggedValue('directives') +
    (occurence.ZeroOrMore('pdfInclude', IPDFInclude),)
    )
