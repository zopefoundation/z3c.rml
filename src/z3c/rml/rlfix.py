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
"""ReportLab fixups.
"""
from reportlab.lib.sequencer import _type2formatter
from reportlab.platypus.flowables import LIIndenter
from reportlab.platypus.flowables import ListFlowable
from reportlab.platypus.flowables import _computeBulletWidth
from reportlab.platypus.flowables import _LIParams
from reportlab.rl_config import register_reset

from z3c.rml import num2words


__docformat__ = "reStructuredText"
import copy

from reportlab.graphics import testshapes
from reportlab.lib import fonts
from reportlab.pdfbase import pdfform
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase import ttfonts
from reportlab.pdfbase.pdfpattern import PDFPattern


_ps2tt_map_original = copy.deepcopy(fonts._ps2tt_map)
_tt2ps_map_original = copy.deepcopy(fonts._tt2ps_map)


def resetPdfForm():
    pdfform.PDFDOCENC = PDFPattern(pdfform.PDFDocEncodingPattern)
    pdfform.ENCODING = PDFPattern(
        pdfform.EncodingPattern, PDFDocEncoding=pdfform.PDFDOCENC)
    pdfform.GLOBALFONTSDICTIONARY = pdfform.FormFontsDictionary()
    pdfform.GLOBALRESOURCES = pdfform.FormResources()
    pdfform.ZADB = PDFPattern(pdfform.ZaDbPattern)


def resetFonts():
    # testshapes._setup registers the Vera fonts every time which is a little
    # slow on all platforms. On Windows it lists the entire system font
    # directory and registers them all which is very slow.
    pdfmetrics.registerFont(ttfonts.TTFont("Vera", "Vera.ttf"))
    pdfmetrics.registerFont(ttfonts.TTFont("VeraBd", "VeraBd.ttf"))
    pdfmetrics.registerFont(ttfonts.TTFont("VeraIt", "VeraIt.ttf"))
    pdfmetrics.registerFont(ttfonts.TTFont("VeraBI", "VeraBI.ttf"))
    for f in (
        'Times-Roman',
        'Courier',
        'Helvetica',
        'Vera',
        'VeraBd',
        'VeraIt',
            'VeraBI'):
        if f not in testshapes._FONTS:
            testshapes._FONTS.append(f)
    fonts._ps2tt_map = copy.deepcopy(_ps2tt_map_original)
    fonts._tt2ps_map = copy.deepcopy(_tt2ps_map_original)


def setSideLabels():
    from reportlab.graphics.charts import piecharts
    piecharts.Pie3d.sideLabels = 0


setSideLabels()


register_reset(resetPdfForm)
register_reset(resetFonts)
del register_reset

# Support more enumeration formats.


_type2formatter.update({
    'l': lambda v: num2words.num2words(v),
    'L': lambda v: num2words.num2words(v).upper(),
    'o': lambda v: num2words.num2words(v, ordinal=True),
    'O': lambda v: num2words.num2words(v, ordinal=True).upper(),
    'r': lambda v: num2words.toOrdinal(v),
    'R': lambda v: num2words.toOrdinal(v).upper(),
})


# Make sure that the counter gets increased for our new formatters as well.


ListFlowable._numberStyles += ''.join(_type2formatter.keys())


def ListFlowable_getContent(self):
    bt = self._bulletType
    value = self._start
    if isinstance(value, (list, tuple)):
        values = value
        value = values[0]
    else:
        values = [value]
    autov = values[0]
    # FIX TO ALLOW ALL FORMATTERS!!!
    inc = int(bt in _type2formatter.keys())
    if inc:
        try:
            value = int(value)
        except BaseException:
            value = 1

    bd = self._bulletDedent
    if bd == 'auto':
        align = self._bulletAlign
        dir = self._bulletDir
        if dir == 'ltr' and align == 'left':
            bd = self._leftIndent
        elif align == 'right':
            bd = self._rightIndent
        else:
            # we need to work out the maximum width of any of the labels
            tvalue = value
            maxW = 0
            for d, f in self._flowablesIter():
                if d:
                    maxW = max(maxW, _computeBulletWidth(self, tvalue))
                    if inc:
                        tvalue += inc
                elif isinstance(f, LIIndenter):
                    b = f._bullet
                    if b:
                        if b.bulletType == bt:
                            maxW = max(maxW, _computeBulletWidth(b, b.value))
                            tvalue = int(b.value)
                    else:
                        maxW = max(maxW, _computeBulletWidth(self, tvalue))
                    if inc:
                        tvalue += inc
            if dir == 'ltr':
                if align == 'right':
                    bd = self._leftIndent - maxW
                else:
                    bd = self._leftIndent - maxW * 0.5
            elif align == 'left':
                bd = self._rightIndent - maxW
            else:
                bd = self._rightIndent - maxW * 0.5

    self._calcBulletDedent = bd

    S = []
    aS = S.append
    i = 0
    for d, f in self._flowablesIter():
        if isinstance(f, ListFlowable):
            fstart = f._start
            if isinstance(fstart, (list, tuple)):
                fstart = fstart[0]
            if fstart in values:
                # my kind of ListFlowable
                if f._auto:
                    autov = values.index(autov) + 1
                    f._start = values[autov:] + values[:autov]
                    autov = f._start[0]
                    if inc:
                        f._bulletType = autov
                else:
                    autov = fstart
        fparams = {}
        if not i:
            i += 1
            spaceBefore = getattr(self, 'spaceBefore', None)
            if spaceBefore is not None:
                fparams['spaceBefore'] = spaceBefore
        if d:
            aS(self._makeLIIndenter(
                f, bullet=self._makeBullet(value), params=fparams))
            if inc:
                value += inc
        elif isinstance(f, LIIndenter):
            b = f._bullet
            if b:
                if b.bulletType != bt:
                    raise ValueError(
                        'Included LIIndenter bulletType=%s != OrderedList'
                        ' bulletType=%s' % (b.bulletType, bt))
                value = int(b.value)
            else:
                f._bullet = self._makeBullet(
                    value, params=getattr(f, 'params', None))
            if fparams:
                f.__dict__['spaceBefore'] = max(
                    f.__dict__.get('spaceBefore', 0), spaceBefore)
            aS(f)
            if inc:
                value += inc
        elif isinstance(f, _LIParams):
            fparams.update(f.params)
            z = self._makeLIIndenter(f.flowable, bullet=None, params=fparams)
            if f.first:
                if f.value is not None:
                    value = f.value
                    if inc:
                        value = int(value)
                z._bullet = self._makeBullet(value, f.params)
                if inc:
                    value += inc
            aS(z)
        else:
            aS(self._makeLIIndenter(f, bullet=None, params=fparams))

    spaceAfter = getattr(self, 'spaceAfter', None)
    if spaceAfter is not None:
        f = S[-1]
        f.__dict__['spaceAfter'] = max(
            f.__dict__.get('spaceAfter', 0), spaceAfter)
    return S


ListFlowable._getContent = ListFlowable_getContent
