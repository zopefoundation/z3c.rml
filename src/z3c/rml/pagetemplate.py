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
"""Page Template Support
"""
import zope

from z3c.rml import rml2pdf


try:
    import zope.pagetemplate.pagetemplatefile
except ImportError:
    raise
    # zope.pagetemplate package has not been installed, uncomment this to mock
    # import types
    # zope.pagetemplate = types.ModuleType('pagetemplate')
    # zope.pagetemplate.pagetemplatefile = types.ModuleType('pagetemplatefile')
    # zope.pagetemplate.pagetemplatefile.PageTemplateFile = object


class RMLPageTemplateFile(zope.pagetemplate.pagetemplatefile.PageTemplateFile):

    def pt_getContext(self, args=(), options=None, **ignore):
        rval = {'template': self,
                'args': args,
                'nothing': None,
                'context': options
                }
        rval.update(self.pt_getEngine().getBaseNames())
        return rval

    def __call__(self, *args, **kwargs):
        rml = super().__call__(*args, **kwargs)

        return rml2pdf.parseString(
            rml, filename=self.pt_source_file()).getvalue()
