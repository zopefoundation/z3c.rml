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
"""``ul``, ``ol``, and ``li`` directives.
"""
__docformat__ = "reStructuredText"
import copy
import reportlab.lib.styles
import reportlab.platypus
import zope.schema
from reportlab.platypus import flowables

from z3c.rml import attr, directive, flowable, interfaces, occurence, stylesheet


class IListItem(stylesheet.IMinimalListStyle, flowable.IFlow):
    """A list item in an ordered or unordered list."""

    style = attr.Style(
        title=u'Style',
        description=u'The list style that is applied to the list.',
        required=False)

class ListItem(flowable.Flow):
    signature = IListItem
    klass = reportlab.platypus.ListItem
    attrMapping = {}

    styleAttributes = zope.schema.getFieldNames(stylesheet.IMinimalListStyle)

    def processStyle(self, style):
        attrs = self.getAttributeValues(select=self.styleAttributes)
        if attrs or not hasattr(style, 'value'):
            style = copy.deepcopy(style)
            # Sigh, this is needed since unordered list items expect the value.
            style.value = style.start
            for name, value in attrs:
                setattr(style, name, value)
        return style

    def process(self):
        self.processSubDirectives()
        args = dict(self.getAttributeValues(ignore=self.styleAttributes))
        if 'style' not in args:
            args['style'] = self.parent.baseStyle
        args['style'] = self.processStyle(args['style'])
        li = self.klass(self.flow, **args)
        self.parent.flow.append(li)


class IOrderedListItem(IListItem):
    """An ordered list item."""

    value = attr.Integer(
        title=u'Bullet Value',
        description=u'The counter value.',
        required=False)

class OrderedListItem(ListItem):
    signature = IOrderedListItem


class IUnorderedListItem(IListItem):
    """An ordered list item."""

    value = attr.Choice(
        title=u'Bullet Value',
        description=u'The type of bullet character.',
        choices=interfaces.UNORDERED_BULLET_VALUES,
        required=False)

class UnorderedListItem(ListItem):
    signature = IUnorderedListItem

    styleAttributes = ListItem.styleAttributes + ['value']


class IListBase(stylesheet.IBaseListStyle):

    style = attr.Style(
        title=u'Style',
        description=u'The list style that is applied to the list.',
        required=False)

class ListBase(directive.RMLDirective):
    klass = reportlab.platypus.ListFlowable
    factories = {'li': ListItem}
    attrMapping = {}

    styleAttributes = zope.schema.getFieldNames(stylesheet.IBaseListStyle)

    def __init__(self, *args, **kw):
        super(ListBase, self).__init__(*args, **kw)
        self.flow = []

    def processStyle(self, style):
        attrs = self.getAttributeValues(
            select=self.styleAttributes, attrMapping=self.attrMapping)
        if attrs:
            style = copy.deepcopy(style)
            for name, value in attrs:
                setattr(style, name, value)
        return style

    def process(self):
        args = dict(self.getAttributeValues(
                ignore=self.styleAttributes, attrMapping=self.attrMapping))
        if 'style' not in args:
            args['style'] = reportlab.lib.styles.ListStyle('List')
        args['style'] = self.baseStyle = self.processStyle(args['style'])
        self.processSubDirectives()
        li = self.klass(self.flow, **args)
        self.parent.flow.append(li)


class IOrderedList(IListBase):
    """An ordered list."""
    occurence.containing(
        occurence.ZeroOrMore('li', IOrderedListItem),
        )

    bulletType = attr.Choice(
        title=u'Bullet Type',
        description=u'The type of bullet formatting.',
        choices=interfaces.ORDERED_LIST_TYPES,
        doLower=False,
        required=False)

class OrderedList(ListBase):
    signature = IOrderedList
    factories = {'li': OrderedListItem}

    styleAttributes = ListBase.styleAttributes + ['bulletType']


class IUnorderedList(IListBase):
    """And unordered list."""
    occurence.containing(
        occurence.ZeroOrMore('li', IUnorderedListItem),
        )

    value = attr.Choice(
        title=u'Bullet Value',
        description=u'The type of bullet character.',
        choices=interfaces.UNORDERED_BULLET_VALUES,
        default='disc',
        required=False)

class UnorderedList(ListBase):
    signature = IUnorderedList
    attrMapping = {'value': 'start'}
    factories = {'li': UnorderedListItem}

    def getAttributeValues(self, *args, **kw):
        res = super(UnorderedList, self).getAttributeValues(*args, **kw)
        res.append(('bulletType', 'bullet'))
        return res

flowable.Flow.factories['ol'] = OrderedList
flowable.IFlow.setTaggedValue(
    'directives',
    flowable.IFlow.getTaggedValue('directives') +
    (occurence.ZeroOrMore('ol', IOrderedList),)
    )

flowable.Flow.factories['ul'] = UnorderedList
flowable.IFlow.setTaggedValue(
    'directives',
    flowable.IFlow.getTaggedValue('directives') +
    (occurence.ZeroOrMore('ul', IUnorderedList),)
    )
