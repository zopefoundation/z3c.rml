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
from reportlab.pdfbase import pdfform
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
    for f in testshapes._setup():
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
