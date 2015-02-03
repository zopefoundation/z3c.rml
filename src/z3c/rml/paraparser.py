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
"""
import copy
import inspect

import reportlab.lib.fonts
import reportlab.platypus.paraparser


class PageNumberFragment(reportlab.platypus.paraparser.ParaFrag):
    """A fragment whose `text` is computed at access time."""

    def __init__(self, **attributes):
        reportlab.platypus.paraparser.ParaFrag.__init__(self, **attributes)
        self.counting_from = attributes.get('countingFrom', 1)

    @property
    def text(self):
        # Guess 1: We're in a paragraph in a story.
        frame = inspect.currentframe(4)
        canvas = frame.f_locals.get('canvas', None)

        if canvas is None:
            # Guess 2: We're in a template
            canvas = frame.f_locals.get('canv', None)

        if canvas is None:
            # Guess 3: We're in evalString or namedString
            canvas = getattr(frame.f_locals.get('self', None), 'canv', None)

        if canvas is None:
            raise Exception("Can't use <pageNumber/> in this location.")

        return str(canvas.getPageNumber() + int(self.counting_from) - 1)


class GetNameFragment(reportlab.platypus.paraparser.ParaFrag):
    """A fragment whose `text` is computed at access time."""

    def __init__(self, **attributes):
        reportlab.platypus.paraparser.ParaFrag.__init__(self, **attributes)
        self.id = attributes['id']
        self.default = attributes.get('default')

    @property
    def text(self):
        # Guess 1: We're in a paragraph in a story.
        frame = inspect.currentframe(4)
        canvas = frame.f_locals.get('canvas', None)

        if canvas is None:
            # Guess 2: We're in a template
            canvas = frame.f_locals.get('canv', None)

        if canvas is None:
            # Guess 3: We're in evalString or namedString
            canvas = getattr(frame.f_locals.get('self', None), 'canv', None)

        if canvas is None:
            raise Exception("Can't use <getName/> in this location.")

        return canvas.manager.get_name(self.id, self.default)


class EvalStringFragment(reportlab.platypus.paraparser.ParaFrag):
    """A fragment whose `text` is evaluated at access time."""

    def __init__(self, **attributes):
        reportlab.platypus.paraparser.ParaFrag.__init__(self, **attributes)
        self.frags = []

    @property
    def text(self):
        text = u''
        for frag in self.frags:
            if isinstance(frag, basestring):
                text += frag
            else:
                text += frag.text
        from z3c.rml.special import do_eval
        return do_eval(text)


class NameFragment(reportlab.platypus.paraparser.ParaFrag):
    """A fragment whose attribute `value` is set to a variable."""

    def __init__(self, **attributes):
        reportlab.platypus.paraparser.ParaFrag.__init__(self, **attributes)

    @property
    def text(self):
        # Guess 1: We're in a paragraph in a story.
        frame = inspect.currentframe(4)
        canvas = frame.f_locals.get('canvas', None)

        if canvas is None:
            # Guess 2: We're in a template
            canvas = frame.f_locals.get('canv', None)

        if canvas is None:
            # Guess 3: We're in evalString or namedString
            canvas = getattr(frame.f_locals.get('self', None), 'canv', None)

        if canvas is None:
            raise Exception("Can't use <name> in this location.")

        canvas.manager.names[self.id] = self.value
        return u''


class Z3CParagraphParser(reportlab.platypus.paraparser.ParaParser):
    """Extensions to paragraph-internal XML parsing."""

    def __init__(self, *args, **kwargs):
        reportlab.platypus.paraparser.ParaParser.__init__(self, *args, **kwargs)
        self.in_eval = False

    def startDynamic(self, attributes, klass):
        frag = klass(**attributes)
        frag.__dict__.update(self._stack[-1].__dict__)
        frag.fontName = reportlab.lib.fonts.tt2ps(
            frag.fontName, frag.bold, frag.italic)
        if self.in_eval:
            self._stack[-1].frags.append(frag)
        else:
            self.fragList.append(frag)
            self._stack.append(frag)

    def endDynamic(self):
        if not self.in_eval:
            self._stack.pop()

    def start_pagenumber(self, attributes):
        self.startDynamic(attributes, PageNumberFragment)

    def end_pagenumber(self):
        self.endDynamic()

    def start_getname(self, attributes):
        self.startDynamic(attributes, GetNameFragment)

    def end_getname(self):
        self.endDynamic()

    def start_name(self, attributes):
        self.startDynamic(attributes, NameFragment)

    def end_name(self):
        self.endDynamic()

    def start_evalstring(self, attributes):
        self.startDynamic(attributes, EvalStringFragment)
        self.in_eval = True

    def end_evalstring(self):
        self.in_eval = False
        self.endDynamic()

    def handle_data(self, data):
        if not self.in_eval:
            reportlab.platypus.paraparser.ParaParser.handle_data(self, data)
        else:
            frag = self._stack[-1].frags.append(data)


# Monkey-patch reportlabs global parser instance. Wah.
import reportlab.platypus.paragraph
reportlab.platypus.paragraph.ParaParser = Z3CParagraphParser
