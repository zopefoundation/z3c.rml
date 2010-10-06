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
# FOR A PARTLAR PURPOSE.
#
##############################################################################
"""Testing all XML Locale functionality.

$Id$
"""
import reportlab.platypus
import reportlab.lib.styles

def myPreformatted(params):
    return reportlab.platypus.Preformatted('''
        Hey, this is a long text from a plugin. Hey, this is a long text from
        a plugin. Hey, this is a long text from a plugin. Hey, this is a long
        text from a plugin. Hey, this is a long text from a plugin. Hey, this
        is a long text from a plugin. Hey, this is a long text from a
        plugin. Hey, this is a long text from a plugin. Hey, this is a long
        text from a plugin. Hey, this is a long text from a plugin. Hey, this
        is a long text from a plugin. Hey, this is a long text from a
        plugin. Hey, this is a long text from a plugin. Hey, this is a long
        text from a plugin. Hey, this is a long text from a plugin. Hey, this
        is a long text from a plugin.''',
        reportlab.lib.styles.getSampleStyleSheet()['Normal'])

class LinkURL(reportlab.platypus.flowables.Flowable):
    def __init__(self, link):
        self.link = link

    def wrap(self, *args):
        return (0, 0)

    def draw(self):
        self.canv.linkURL(self.link, None)
        

def linkURL(params):
    params = eval(params)
    return (
        reportlab.platypus.Paragraph(
            params[0], reportlab.lib.styles.getSampleStyleSheet()['Normal']),
        LinkURL(*params))
