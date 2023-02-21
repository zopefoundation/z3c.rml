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

import io
import logging
import os
import subprocess

from backports import tempfile


try:
    import pikepdf
    from pikepdf import Dictionary  # noqa: F401 imported but unused
except ImportError:
    pikepdf = None
from reportlab.platypus import flowables

from z3c.rml import attr
from z3c.rml import flowable
from z3c.rml import interfaces
from z3c.rml import occurence


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
        log.error(f'An error occurred while running command: {cmd}')
        log.error(f'Error Output: \n{stderr}')
        raise ValueError(
            f'Shell Process had non-zero error code: {p.returncode}. \n'
            f'Stdout: {stdout}\n'
            f'StdErr: {stderr}'
        )
    log.debug(f'Output: \n{stdout}')
    return stdout


class ConcatenationPostProcessor:

    def __init__(self):
        self.operations = []

    def process(self, inputFile1):
        input1 = pikepdf.open(inputFile1)
        offset = 0
        for (
                start_page, inputFile2, page_ranges, num_pages, on_first_page
        ) in self.operations:
            sp = start_page + offset
            for page_range in page_ranges:
                prs, pre = page_range
                input2 = pikepdf.open(inputFile2)
                for i in range(num_pages):
                    if on_first_page and i > 0:
                        # The platypus pipeline doesn't insert blank pages if
                        # we are including on the first page. So we need to
                        # insert our additional pages between start_page and
                        # the next.
                        input1.pages.insert(sp + i, input2.pages[prs + i])
                        offset += 1
                    else:
                        # Here, Platypus has added more blank pages, so we'll
                        # emplace our pages. Doing this copy will preserve
                        # references to the original pages if there is a
                        # TOC/Bookmarks.
                        input1.pages.append(input2.pages[prs + i])
                        input1.pages[sp + i].emplace(input1.pages[-1])
                        del input1.pages[-1]

        outputFile = io.BytesIO()
        input1.save(outputFile)
        return outputFile


class PdfTkConcatenationPostProcessor:

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
        for (
                start_page, inputFile2, page_ranges, num_pages, on_first_page
        ) in self.operations:
            # Catch up with the main file.
            if curr_page < start_page:
                # Convert curr_page to human counting, start_page is okay,
                # since pdftk is upper-bound inclusive.
                merges.append('A%i-%i' % (curr_page + 1, start_page))
            curr_page = start_page + num_pages

            # Store file.
            file_letter = _letter(file_id)
            file_path = os.path.join(dir, file_letter + '.pdf')
            inputFile2.seek(0)
            with open(file_path, 'wb') as file:
                file.write(inputFile2.read())
            file_map[file_letter] = file_path
            file_id += 1

            for (prs, pre) in page_ranges:
                # pdftk uses lower and upper bound inclusive.
                merges.append('%s%i-%i' % (file_letter, prs + 1, pre))

        mergedFile = os.path.join(dir, 'merged.pdf')
        do('{} {} cat {} output {}'.format(
            self.EXECUTABLE,
            ' '.join(f'{l_}="{p}"' for l_, p in file_map.items()),
            ' '.join(merges),
            mergedFile))

        if not self.PRESERVE_OUTLINE:
            with open(mergedFile, 'rb') as file:
                return io.BytesIO(file.read())

        outputFile = os.path.join(dir, 'output.pdf')
        do('{} {}/A.pdf dump_data > {}/in.info'.format(
            self.EXECUTABLE, dir, dir))
        do('{} {} update_info {}/in.info output {}'.format(
            self.EXECUTABLE, mergedFile, dir, outputFile))

        with open(outputFile, 'rb') as file:
            return io.BytesIO(file.read())

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
            self.width = 10 << 32
            self.height = 10 << 32

    def draw(self):
        if self.included_on_first_page:
            self.split(None, None)

    def split(self, availWidth, availheight):
        pages = self.pages
        if not pages:
            pdf = pikepdf.open(self.pdf_file)
            pages = [(0, len(pdf.pages))]

        num_pages = sum(pr[1] - pr[0] for pr in pages)

        start_page = self.canv.getPageNumber()
        if self.included_on_first_page:
            start_page -= 1
        self.proc.operations.append(
            (start_page, self.pdf_file, pages,
             num_pages, self.included_on_first_page))

        # Insert blank pages instead of pdf for now, to correctly number the
        # pages. We will replace these blank pages with included PDF in
        # ConcatenationPostProcessor.
        result = []
        for i in range(num_pages):
            # Add empty spacer so platypus don't complain about too many empty
            # pages
            result.append(flowables.Spacer(0, 0))
            result.append(flowables.PageBreak())
        if start_page >= len(pages):
            # Make sure we get a flowable at the end of the document for the
            # last page.
            result.append(flowables.Spacer(0, 0))
        return result


class IIncludePdfPages(interfaces.IRMLDirectiveSignature):
    """Inserts a set of pages from a given PDF."""

    filename = attr.File(
        title='Path to file',
        description='The pdf file to include.',
        required=True)

    pages = attr.IntegerSequence(
        title='Pages',
        description='A list of pages to insert.',
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
        if pikepdf is None:
            raise Exception(
                'pikepdf is not installed, so this feature is not available.')
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
