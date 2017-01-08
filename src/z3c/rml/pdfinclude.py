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

import logging
import os
import subprocess
import six
from backports import tempfile

try:
    import PyPDF2
    from PyPDF2.generic import NameObject
except ImportError:
    PyPDF2 = None
from reportlab.platypus import flowables

from z3c.rml import attr, flowable, interfaces, occurence

log = logging.getLogger(__name__)

# by default False to avoid burping on
# PdfReadWarning: Multiple definitions in dictionary at byte xxx
STRICT = False

def _letter(val, base=ord('A'), radix=26):
    __traceback_info__ = val, base
    index = val - 1
    if index < 0:
        raise ValueError('Value must be greater than 0.')
    s = ''
    while True:
        val, off = divmod(index, radix)
        index = val - 1
        s = chr(base + off) + s
        if not val:
            return s

def do(cmd, cwd=None, captureOutput=True, ignoreErrors=False):
    log.debug('Command: ' + cmd)
    if captureOutput:
        stdout = stderr = subprocess.PIPE
    else:
        stdout = stderr = None
    p = subprocess.Popen(
        cmd, stdout=stdout, stderr=stderr,
        shell=True, cwd=cwd)
    stdout, stderr = p.communicate()
    if stdout is None:
        stdout = "See output above"
    if stderr is None:
        stderr = "See output above"
    if p.returncode != 0 and not ignoreErrors:
        log.error(u'An error occurred while running command: %s' % cmd)
        log.error('Error Output: \n%s' % stderr)
        raise ValueError('Shell Process had non-zero error code: {}. \n'
                         'Stdout: {}\n'
                         'StdErr: {}'.format(p.returncode, stdout, stderr))
    log.debug('Output: \n%s' % stdout)
    return stdout


class ConcatenationPostProcessor(object):

    def __init__(self):
        self.operations = []

    def process(self, inputFile1):
        input1 = PyPDF2.PdfFileReader(inputFile1, strict=STRICT)
        merger = PyPDF2.PdfFileMerger(strict=STRICT)
        merger.output._info.getObject().update(input1.documentInfo)

        merger.append(inputFile1)

        for start_page, inputFile2, page_ranges, num_pages in self.operations:
            # Remove blank pages, that we reserved in IncludePdfPagesFlowable
            # and insert real pdf here
            del merger.pages[start_page:start_page + num_pages]
            curr_page = start_page
            for page_range in page_ranges:
                prs, pre = page_range
                merger.merge(
                    curr_page, inputFile2, pages=(prs, pre),
                    import_bookmarks=False)

        outputFile = six.BytesIO()
        merger.write(outputFile)
        return outputFile


class PdfTkConcatenationPostProcessor(object):

    EXECUTABLE = 'pdftk'
    PRESERVE_OUTLINE = True

    def __init__(self):
        self.operations = []

    def _process(self, inputFile1, dir):
        file_path = os.path.join(dir, 'A.pdf')
        with open(file_path, 'wb') as file:
            file.write(inputFile1.read())

        file_map = {'A': file_path}
        file_id = 2
        merges = []

        curr_page = 0
        for start_page, inputFile2, page_ranges, num_pages in self.operations:
            # Catch up with the main file.
            if curr_page < start_page:
                # Convert curr_page to human counting, start_page is okay,
                # since pdftk is upper-bound inclusive.
                merges.append('A%i-%i' % (curr_page+1, start_page))
            curr_page = start_page + num_pages

            # Store file.
            file_letter = _letter(file_id)
            file_path = os.path.join(dir, file_letter+'.pdf')
            inputFile2.seek(0)
            with open(file_path, 'wb') as file:
                file.write(inputFile2.read())
            file_map[file_letter] = file_path
            file_id += 1

            for (prs, pre) in page_ranges:
                # pdftk uses lower and upper bound inclusive.
                merges.append('%s%i-%i' % (file_letter, prs+1, pre))

        mergedFile = os.path.join(dir, 'merged.pdf')
        do('%s %s cat %s output %s' % (
            self.EXECUTABLE,
            ' '.join('%s="%s"' % (l, p) for l, p in file_map.items()),
            ' '.join(merges),
            mergedFile))

        if not self.PRESERVE_OUTLINE:
            with open(mergedFile, 'rb') as file:
                return six.BytesIO(file.read())

        outputFile = os.path.join(dir, 'output.pdf')
        do('%s %s/A.pdf dump_data > %s/in.info' % (
            self.EXECUTABLE, dir, dir))
        do('%s %s update_info %s/in.info output %s' % (
            self.EXECUTABLE, mergedFile, dir, outputFile))

        with open(outputFile, 'rb') as file:
            return six.BytesIO(file.read())

    def process(self, inputFile1):
        with tempfile.TemporaryDirectory() as tmpdirname:
            return self._process(inputFile1, tmpdirname)


class IncludePdfPagesFlowable(flowables.Flowable):

    def __init__(self, pdf_file, pages, concatprocessor,
                 included_on_first_page):
        flowables.Flowable.__init__(self)
        self.pdf_file = pdf_file
        self.proc = concatprocessor
        self.pages = pages
        self.included_on_first_page = included_on_first_page

        if self.included_on_first_page:
            self.width = 0
            self.height = 0
        else:
            self.width = 10<<32
            self.height = 10<<32

    def draw(self):
        if self.included_on_first_page:
            self.split(None, None)

    def split(self, availWidth, availheight):
        pages = self.pages
        if not pages:
            pdf = PyPDF2.PdfFileReader(self.pdf_file, strict=STRICT)
            pages = [(0, pdf.getNumPages())]

        num_pages = sum(pr[1]-pr[0] for pr in pages)

        start_page = self.canv.getPageNumber()
        if self.included_on_first_page:
            start_page -= 1
        self.proc.operations.append(
            (start_page, self.pdf_file, pages, num_pages))

        # Insert blank pages instead of pdf for now, to correctly number the
        # pages. We will replace these blank pages with included PDF in
        # ConcatenationPostProcessor.
        result = []
        for i in range(num_pages):
            # Add empty spacer so platypus don't complain about too many empty
            # pages
            result.append(flowables.Spacer(0, 0))
            result.append(flowables.PageBreak())
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
        numberingStartsAt=1,
        required=False)


class IncludePdfPages(flowable.Flowable):
    signature = IIncludePdfPages

    ConcatenationPostProcessorFactory = ConcatenationPostProcessor

    def getProcessor(self):
        manager = attr.getManager(self, interfaces.IPostProcessorManager)
        procs = dict(manager.postProcessors)
        if 'CONCAT' not in procs:
            log.debug(
                'Using concetation post-processor: %s',
                self.ConcatenationPostProcessorFactory)
            proc = self.ConcatenationPostProcessorFactory()
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
            IncludePdfPagesFlowable(
                args['filename'], args.get('pages'), proc, not self.parent.flow
            ))


flowable.Flow.factories['includePdfPages'] = IncludePdfPages
flowable.IFlow.setTaggedValue(
    'directives',
    flowable.IFlow.getTaggedValue('directives') +
    (occurence.ZeroOrMore('includePdfPages', IIncludePdfPages),)
    )
