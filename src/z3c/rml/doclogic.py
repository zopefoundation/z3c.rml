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
"""``doc*`` directives.
"""
import reportlab.platypus
from z3c.rml import attr, directive, flowable, interfaces, occurence

class IDocAssign(interfaces.IRMLDirectiveSignature):
    """Assign a value to the namesapce."""

    var = attr.String(
        title=u'Variable Name',
        description=u'The name under which the value is stored.',
        required=True)

    expr = attr.String(
        title=u'Expression',
        description=u'The expression that creates the value when evaluated.',
        required=True)

class DocAssign(flowable.Flowable):
    signature = IDocAssign
    klass = reportlab.platypus.flowables.DocAssign


class IDocExec(interfaces.IRMLDirectiveSignature):
    """Execute a statement."""

    stmt = attr.String(
        title=u'Statement',
        description=u'The statement to be executed.',
        required=True)

class DocExec(flowable.Flowable):
    signature = IDocExec
    klass = reportlab.platypus.flowables.DocExec


class IDocPara(interfaces.IRMLDirectiveSignature):
    """Create a paragraph with the value returned from the expression."""

    expr = attr.String(
        title=u'Expression',
        description=u'The expression to be executed.',
        required=True)

    format = attr.String(
        title=u'Format',
        description=u'The format used to render the expression value.',
        required=False)

    style = attr.Style(
        title=u'Style',
        description=u'The style of the paragraph.',
        required=False)

    escape = attr.Boolean(
        title=u'Escape Text',
        description=u'When set (default) the expression value is escaped.',
        required=False)

class DocPara(flowable.Flowable):
    signature = IDocPara
    klass = reportlab.platypus.flowables.DocPara


class IDocAssert(interfaces.IRMLDirectiveSignature):
    """Assert a certain condition."""

    cond = attr.String(
        title=u'Condition',
        description=u'The condition to be asserted.',
        required=True)

    format = attr.String(
        title=u'Format',
        description=u'The text displayed if assertion fails.',
        required=False)

class DocAssert(flowable.Flowable):
    signature = IDocAssert
    klass = reportlab.platypus.flowables.DocAssert


class IDocElse(interfaces.IRMLDirectiveSignature):
    """Starts 'else' block."""

class DocElse(flowable.Flowable):
    signature = IDocElse

    def process(self):
        if not isinstance(self.parent, DocIf):
            raise ValueError("<docElse> can only be placed inside a <docIf>")
        self.parent.flow = self.parent.elseFlow


class IDocIf(flowable.IFlow):
    """Display story flow based on the value of the condition."""

    cond = attr.String(
        title=u'Condition',
        description=u'The condition to be tested.',
        required=True)

class DocIf(flowable.Flow):
    signature = IDocAssert
    klass = reportlab.platypus.flowables.DocIf

    def __init__(self, *args, **kw):
        super(flowable.Flow, self).__init__(*args, **kw)
        self.thenFlow = self.flow = []
        self.elseFlow = []

    def process(self):
        args = dict(self.getAttributeValues())
        self.processSubDirectives()
        dif = self.klass(
            thenBlock = self.thenFlow, elseBlock = self.elseFlow, **args)
        self.parent.flow.append(dif)

class IDocWhile(flowable.IFlow):
    """Repeat the included directives as long as the condition is true."""

    cond = attr.String(
        title=u'Condition',
        description=u'The condition to be tested.',
        required=True)

class DocWhile(flowable.Flow):
    signature = IDocAssert
    klass = reportlab.platypus.flowables.DocWhile

    def process(self):
        args = dict(self.getAttributeValues())
        self.processSubDirectives()
        dwhile = self.klass(whileBlock = self.flow, **args)
        self.parent.flow.append(dwhile)


flowable.Flow.factories['docAssign'] = DocAssign
flowable.Flow.factories['docExec'] = DocExec
flowable.Flow.factories['docPara'] = DocPara
flowable.Flow.factories['docAssert'] = DocAssert
flowable.Flow.factories['docIf'] = DocIf
flowable.Flow.factories['docElse'] = DocElse
flowable.Flow.factories['docWhile'] = DocWhile

flowable.IFlow.setTaggedValue(
    'directives',
    flowable.IFlow.getTaggedValue('directives') +
    (occurence.ZeroOrMore('docAssign', IDocAssign),
     occurence.ZeroOrMore('docExec', IDocExec),
     occurence.ZeroOrMore('docPara', IDocPara),
     occurence.ZeroOrMore('docIf', IDocIf),
     occurence.ZeroOrMore('docElse', IDocElse),
     occurence.ZeroOrMore('docWhile', IDocWhile),
     )
    )
