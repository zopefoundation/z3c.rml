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
import six
import sys
import reportlab.lib.fonts
import reportlab.lib.styles
import reportlab.lib.utils
import reportlab.platypus.paraparser
import reportlab.platypus.paragraph

class ParaFragWrapper(reportlab.platypus.paraparser.ParaFrag):
    @property
    def text(self):
        key = self._get_pass_key()
        if not hasattr(self, key):
            setattr(self, key, self._get_text())
        return getattr(self, key)

    @text.setter
    def text(self, value):
        key = self._get_pass_key()
        setattr(self, key, value)

    def _get_pass_key(self):
        canvas = self._get_canvas()
        return '_text_%s_%s' % (
            canvas._doctemplate.current_pass, canvas.getPageNumber()
        )

    def _get_canvas(self):
        canvas = None
        i = 5

        while canvas is None:
            try:
                frame = sys._getframe(i)
            except ValueError:
                raise Exception(
                    "Can't use <%s> in this location." % self.__tag__)

            # Guess 1: We're in a paragraph in a story.
            canvas = frame.f_locals.get('canvas', None)

            if canvas is None:
                # Guess 2: We're in a template
                canvas = frame.f_locals.get('canv', None)

            if canvas is None:
                # Guess 3: We're in evalString or namedString
                canvas = getattr(frame.f_locals.get('self', None), 'canv', None)

            i += 1

        return canvas


class PageNumberFragment(ParaFragWrapper):
    """A fragment whose `text` is computed at access time."""

    __tag__ = 'pageNumber'

    def __init__(self, **attributes):
        reportlab.platypus.paraparser.ParaFrag.__init__(self, **attributes)
        self.counting_from = attributes.get('countingFrom', 1)

    def _get_text(self):
        canvas = self._get_canvas()
        return str(canvas.getPageNumber() + int(self.counting_from) - 1)


class GetNameFragment(ParaFragWrapper):
    """A fragment whose `text` is computed at access time."""

    __tag__ = 'getName'

    def __init__(self, **attributes):
        reportlab.platypus.paraparser.ParaFrag.__init__(self, **attributes)
        self.id = attributes['id']
        self.default = attributes.get('default')

    def _get_text(self):
        canvas = self._get_canvas()
        return canvas.manager.get_name(self.id, self.default)


class EvalStringFragment(ParaFragWrapper):
    """A fragment whose `text` is evaluated at access time."""

    __tag__ = 'evalString'

    def __init__(self, **attributes):
        reportlab.platypus.paraparser.ParaFrag.__init__(self, **attributes)
        self.frags = attributes.get('frags', [])

    def _get_text(self):
        text = u''
        for frag in self.frags:
            if isinstance(frag, six.string_types):
                text += frag
            else:
                text += frag.text
        from z3c.rml.special import do_eval
        return do_eval(text)


class NameFragment(ParaFragWrapper):
    """A fragment whose attribute `value` is set to a variable."""

    __tag__ = 'name'

    def __init__(self, **attributes):
        reportlab.platypus.paraparser.ParaFrag.__init__(self, **attributes)

    def _get_text(self):
        canvas = self._get_canvas()
        canvas.manager.names[self.id] = self.value
        return u''


class SpanStyle(reportlab.lib.styles.PropertySet):
    # Do not specify defaults, so that all attributes can be inherited.
    defaults = {}


class Z3CParagraphParser(reportlab.platypus.paraparser.ParaParser):
    """Extensions to paragraph-internal XML parsing."""

    _lineAttrs = ('color', 'width', 'offset', 'gap', 'kind')

    def __init__(self, manager, *args, **kwargs):
        reportlab.platypus.paraparser.ParaParser.__init__(self, *args, **kwargs)
        self.manager = manager
        self.in_eval = False

    def findSpanStyle(self, style):
        from z3c.rml import attr
        return attr._getStyle(self.manager, style)

    def startDynamic(self, attributes, klass):
        frag = klass(**attributes)
        frag.__dict__.update(self._stack[-1].__dict__)
        frag.__tag__ = klass.__tag__
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

    def start_para(self, attr):
        reportlab.platypus.paraparser.ParaParser.start_para(self, attr)

        # Support for underline.
        if getattr(self._style, 'underline', False):
            attrs = {}
            for name in self._lineAttrs:
                styleName = 'underline' + name.title()
                if hasattr(self._style, styleName):
                    attrs[name] = getattr(self._style, styleName)
            self.start_u(attrs)

        # Support for strike.
        if getattr(self._style, 'strike', False):
            attrs = {}
            for name in self._lineAttrs:
                styleName = 'strike' + name.title()
                if hasattr(self._style, styleName):
                    attrs[name] = getattr(self._style, styleName)
            self.start_strike(attrs)

    def end_para(self):
        if getattr(self._style, 'strike', False):
            self.end_strike()
        if getattr(self._style, 'underline', False):
            self.end_u()
        reportlab.platypus.paraparser.ParaParser.end_para(self)

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


class Z3CParagraph(reportlab.platypus.paragraph.Paragraph):
    """Support for custom paraparser with sytles knowledge.

    Methods mostly copied from reportlab.
    """

    def __init__(self, text, style, bulletText = None, frags=None,
                 caseSensitive=1, encoding='utf8', manager=None):
        self.caseSensitive = caseSensitive
        self.encoding = encoding
        self._setup(
            text, style, bulletText or getattr(style,'bulletText',None), frags,
            reportlab.platypus.paragraph.cleanBlockQuotedText, manager)

    def _setup(self, text, style, bulletText, frags, cleaner, manager):

        # This used to be a global parser to save overhead.  In the interests
        # of thread safety it is being instantiated per paragraph.  On the
        # next release, we'll replace with a cElementTree parser

        if frags is None:
            text = cleaner(text)
            _parser = Z3CParagraphParser(manager)
            _parser.caseSensitive = self.caseSensitive
            style, frags, bulletTextFrags = _parser.parse(text, style)
            if frags is None:
                raise ValueError(
                    "xml parser error (%s) in paragraph beginning\n'%s'"\
                    % (_parser.errors[0],text[:min(30,len(text))]))
            reportlab.platypus.paragraph.textTransformFrags(frags,style)
            if bulletTextFrags:
                bulletText = bulletTextFrags

        # AR hack
        self.text = text
        self.frags = frags  # either the parse fragments or frag word list
        self.style = style
        self.bulletText = bulletText
        self.debug = 0


class ImageReader(reportlab.lib.utils.ImageReader):

    def __init__(self, fileName, ident=None):
        if isinstance(fileName, six.string_types):
            # Avoid circular imports. The filename resolutions hould be added
            # to a utility module.
            from z3c.rml import attr
            _srcAttr = attr.File(doNotOpen=True)
            fileName = _srcAttr.fromUnicode(fileName)
        return super(ImageReader, self).__init__(fileName, ident)


# Monkey Patch reportlab image reader, so that <img> tags inside paragraphs
# can also benefit from package-local file paths.
reportlab.platypus.paraparser.ImageReader = ImageReader
