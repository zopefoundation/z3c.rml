##############################################################################
#
# Copyright (c) 2007 Zope Foundation and Contributors.
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
"""Style Related Element Processing
"""
import reportlab.platypus.flowables


class TestFlowable(reportlab.platypus.flowables.Flowable):

    def __init__(self, text):
        self.text = text

    def wrap(self, *args):
        return (400, 100)

    def draw(self):
        self.canv.saveState()
        self.canv.rect(0, 0, 400, 100)
        self.canv.drawString(0, 50, self.text)
        self.canv.restoreState()
