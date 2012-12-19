##############################################################################
#
# Copyright (c) 2007-2008 Zope Foundation and Contributors.
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
"""Paragraph-internal XML parser extensions.

$Id: flowable.py 76814 2007-06-19 20:12:41Z srichter $
"""
__docformat__ = "reStructuredText"

import copy
import inspect

import reportlab.lib.fonts
import reportlab.platypus.paraparser


class PageNumberFragment(reportlab.platypus.paraparser.ParaFrag):
    """A fragment whose `text` is computed at access time."""

    def __init__(self, attributes):
        reportlab.platypus.paraparser.ParaFrag.__init__(self)

    @property
    def text(self):
        # Guess 1: We're in a paragraph in a story.
        frame = inspect.currentframe(4)
        canvas = frame.f_locals.get('canvas', None)

        if canvas is None:
            # Guess 2: We're in a template
            canvas = frame.f_locals.get('canv', None)

        if canvas is None:
            raise Exception("Can't use <pageNumber/> in this location.")

        return str(canvas.getPageNumber())


class GetNameFragment(reportlab.platypus.paraparser.ParaFrag):
    """A fragment whose `text` is computed at access time."""

    def __init__(self, attributes):
        reportlab.platypus.paraparser.ParaFrag.__init__(self)
        self.id = attributes['id']

    @property
    def text(self):
        # Guess 1: We're in a paragraph in a story.
        frame = inspect.currentframe(4)
        canvas = frame.f_locals.get('canvas', None)

        if canvas is None:
            # Guess 2: We're in a template
            canvas = frame.f_locals.get('canv', None)

        if canvas is None:
            raise Exception("Can't use <getName/> in this location.")

        return canvas.manager.names[self.id]


class Z3CParagraphParser(reportlab.platypus.paraparser.ParaParser):
    """Extensions to paragraph-internal XML parsing."""

    def startDynamic(self, attributes, klass):
        frag = klass(attributes)
        frag.__dict__.update(self._stack[-1].__dict__)
        frag.fontName = reportlab.lib.fonts.tt2ps(
            frag.fontName, frag.bold, frag.italic)
        self.fragList.append(frag)
        self._stack.append(frag)

    def endDynamic(self):
        self._pop()

    def start_pageNumber(self, attributes):
        self.startDynamic(attributes, PageNumberFragment)

    def end_pageNumber(self):
        self.endDynamic()

    def start_getName(self, attributes):
        self.startDynamic(attributes, GetNameFragment)

    def end_getName(self):
        self.endDynamic()


# Monkey-patch reportlabs global parser instance. Wah.
import reportlab.platypus.paragraph
reportlab.platypus.paragraph._parser = Z3CParagraphParser()
