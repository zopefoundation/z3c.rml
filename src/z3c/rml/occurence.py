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
"""Condition Implementation
"""
import reportlab
import six
import sys
import zope.interface
import zope.schema
from zope.schema import fieldproperty

class ICondition(zope.interface.Interface):
    """Condition that is checked before a  directive is available."""

    __doc__ = zope.schema.TextLine(
        title=u'Description',
        description=u'The description of the condition.',
        required=True)

    def __call__(directive):
        """Check whether the condition is fulfilled for the given directive."""


class IOccurence(zope.interface.Interface):
    """Description of the occurence of a sub-directive."""

    __doc__ = zope.schema.TextLine(
        title=u'Description',
        description=u'The description of the occurence.',
        required=True)

    if six.PY2:
        tag = zope.schema.BytesLine(
            title=u'Tag',
            description=u'The tag of the sub-directive within the directive',
            required=True)
    else:
        tag = zope.schema.TextLine(
            title=u'Tag',
            description=u'The tag of the sub-directive within the directive',
            required=True)

    signature = zope.schema.Field(
        title=u'Signature',
        description=u'The signature of the sub-directive.',
        required=True)

    condition = zope.schema.Field(
        title=u'Condition',
        description=u'The condition that the directive is available.',
        required=False)


@zope.interface.implementer(ICondition)
def laterThanReportlab21(directive):
    """The directive is only available in Reportlab 2.1 and higher."""
    return [int(num) for num in reportlab.Version.split('.')] >= (2, 0)


def containing(*occurences):
    frame = sys._getframe(1)
    f_locals = frame.f_locals
    f_globals = frame.f_globals

    if not (f_locals is not f_globals
            and f_locals.get('__module__')
            and f_locals.get('__module__') == f_globals.get('__name__')
            ):
        raise TypeError("contains not called from signature interface")

    f_locals['__interface_tagged_values__'] = {'directives': occurences}


@zope.interface.implementer(IOccurence)
class Occurence(object):
    tag = fieldproperty.FieldProperty(IOccurence['tag'])
    signature = fieldproperty.FieldProperty(IOccurence['signature'])
    condition = fieldproperty.FieldProperty(IOccurence['condition'])

    def __init__(self, tag, signature, condition=None):
        self.tag = tag
        self.signature = signature
        self.condition = condition


class ZeroOrMore(Occurence):
    """Zero or More

    This sub-directive can occur zero or more times.
    """

class ZeroOrOne(Occurence):
    """Zero or one

    This sub-directive can occur zero or one time.
    """

class OneOrMore(Occurence):
    """One or More

    This sub-directive can occur one or more times.
    """

class One(Occurence):
    """One

    This sub-directive must occur exactly one time.
    """
