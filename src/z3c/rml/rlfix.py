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
__docformat__ = "reStructuredText"
import copy
from reportlab.pdfbase import pdfform, pdfmetrics, ttfonts
from reportlab.pdfbase.pdfpattern import PDFPattern
from reportlab.graphics import testshapes
from reportlab.lib import fonts

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
    for f in ('Times-Roman','Courier','Helvetica','Vera', 'VeraBd', 'VeraIt',
              'VeraBI'):
        if f not in testshapes._FONTS:
            testshapes._FONTS.append(f)
    fonts._ps2tt_map = copy.deepcopy(_ps2tt_map_original)
    fonts._tt2ps_map = copy.deepcopy(_tt2ps_map_original)

def setSideLabels():
    from reportlab.graphics.charts import piecharts
    piecharts.Pie3d.sideLabels = 0
setSideLabels()

from reportlab.rl_config import register_reset
register_reset(resetPdfForm)
register_reset(resetFonts)
del register_reset

# Support more enumeration formats.

from z3c.rml import num2words
from reportlab.lib.sequencer import _type2formatter

_type2formatter.update({
    'l': lambda v: num2words.num2words(v),
    'L': lambda v: num2words.num2words(v).upper(),
    'o': lambda v: num2words.num2words(v, ordinal=True),
    'O': lambda v: num2words.num2words(v, ordinal=True).upper(),
    'r': lambda v: num2words.toOrdinal(v),
    'R': lambda v: num2words.toOrdinal(v).upper(),
})


# Make sure that the counter gets increased for our new formatters as well.

from reportlab.platypus.flowables import ListFlowable, LIIndenter, _LIParams, \
    _computeBulletWidth

def ListFlowable_getContent(self):
    value = self._start
    bt = self._bulletType
    # FIX TO ALLOW ALL FORMATTERS!!!
    inc = int(bt in _type2formatter.keys())
    if inc: value = int(value)

    bd = self._bulletDedent
    if bd=='auto':
        align = self._bulletAlign
        dir = self._bulletDir
        if dir=='ltr' and align=='left':
            bd = self._leftIndent
        elif align=='right':
            bd = self._rightIndent
        else:
            #we need to work out the maximum width of any of the labels
            tvalue = value
            maxW = 0
            for d,f in self._flowablesIter():
                if d:
                    maxW = max(maxW,_computeBulletWidth(self,tvalue))
                    if inc: tvalue += inc
                elif isinstance(f,LIIndenter):
                    b = f._bullet
                    if b:
                        if b.bulletType==bt:
                            maxW = max(maxW,_computeBulletWidth(b,b.value))
                            tvalue = int(b.value)
                    else:
                        maxW = max(maxW,_computeBulletWidth(self,tvalue))
                    if inc: tvalue += inc
            if dir=='ltr':
                if align=='right':
                    bd = self._leftIndent - maxW
                else:
                    bd = self._leftIndent - maxW*0.5
            elif align=='left':
                bd = self._rightIndent - maxW
            else:
                bd = self._rightIndent - maxW*0.5

    self._calcBulletDedent = bd

    S = []
    aS = S.append
    i=0
    for d,f in self._flowablesIter():
        fparams = {}
        if not i:
            i += 1
            spaceBefore = getattr(self,'spaceBefore',None)
            if spaceBefore is not None:
                fparams['spaceBefore'] = spaceBefore
        if d:
            aS(self._makeLIIndenter(f,bullet=self._makeBullet(value),params=fparams))
            if inc: value += inc
        elif isinstance(f,LIIndenter):
            b = f._bullet
            if b:
                if b.bulletType!=bt:
                    raise ValueError('Included LIIndenter bulletType=%s != OrderedList bulletType=%s' % (b.bulletType,bt))
                value = int(b.value)
            else:
                f._bullet = self._makeBullet(value,params=getattr(f,'params',None))
            if fparams:
                f.__dict__['spaceBefore'] = max(f.__dict__.get('spaceBefore',0),spaceBefore)
            aS(f)
            if inc: value += inc
        elif isinstance(f,_LIParams):
            fparams.update(f.params)
            z = self._makeLIIndenter(f.flowable,bullet=None,params=fparams)
            if f.first:
                if f.value is not None:
                    value = f.value
                    if inc: value = int(value)
                z._bullet = self._makeBullet(value,f.params)
                if inc: value += inc
            aS(z)
        else:
            aS(self._makeLIIndenter(f,bullet=None,params=fparams))

    spaceAfter = getattr(self,'spaceAfter',None)
    if spaceAfter is not None:
        f=S[-1]
        f.__dict__['spaceAfter'] = max(f.__dict__.get('spaceAfter',0),spaceAfter)
    return S

ListFlowable._getContent = ListFlowable_getContent
