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
"""RML to PDF Converter Interfaces

$Id$
"""
__docformat__ = "reStructuredText"
import zope.interface

class IRML2PDF(zope.interface.Interface):
    """This is the main public API of z3c.rml"""

    def go(xmlInputName, outputFileName=None, outDir=None, dtdDir=None):
        """Convert RML 2 PDF.

        The generated file will be located in the ``outDir`` under the name
        ``outputFileName``.
        """

class IStylesManager(zope.interface.Interface):
    """Manages custom styles"""

    styles = zope.interface.Attribute("Styles dict")
