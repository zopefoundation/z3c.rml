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
from reportlab.pdfbase import pdfform, pdfmetrics, ttfonts
from reportlab.pdfbase.pdfpattern import PDFPattern
from reportlab.graphics import testshapes

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

def setSideLabels():
    from reportlab.graphics.charts import piecharts
    piecharts.Pie3d.sideLabels = 0
setSideLabels()

from reportlab.rl_config import register_reset
register_reset(resetPdfForm)
register_reset(resetFonts)
del register_reset
