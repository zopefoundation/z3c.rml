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
"""RML Reference Generator

$Id$
"""
__docformat__ = "reStructuredText"
import zope.schema
import zope.schema.interfaces
from z3c.rml import attr, document, pagetemplate

IGNORE_ATTRIBUTES = ('RMLAttribute', 'BaseChoice')

def getAttributeTypes():
    types = []
    candidates = sorted(attr.__dict__.items(), key=lambda e: e[0])
    for name, candidate in candidates:
        if not (isinstance(candidate, type) and
                zope.schema.interfaces.IField.implementedBy(candidate) and
                name not in IGNORE_ATTRIBUTES):
            continue
        types.append({
            'name': name,
            'description': candidate.__doc__
            })
    return types


def formatField(field):
    return field.__class__.__name__

def formatChoice(field):
    choices = ', '.join([repr(choice) for choice in field.choices.keys()])
    return '%s of (%s)' %(field.__class__.__name__, choices)

def formatSequence(field):
    vtFormatter = typeFormatters.get(field.value_type.__class__, formatField)
    return '%s of %s' %(field.__class__.__name__, vtFormatter(field.value_type))

typeFormatters = {
    attr.Choice: formatChoice,
    attr.Sequence: formatSequence}

def processSignature(name, signature, directives=None):
    if directives is None:
        directives = {}
    # Process this directive
    if signature not in directives:
        info = {'name': name, 'description': signature.getDoc()}
        attrs = []
        for name, field in zope.schema.getFieldsInOrder(signature):
            typeFormatter = typeFormatters.get(field.__class__, formatField)
            attrs.append({
                'name': name,
                'type': typeFormatter(field),
                'title': field.title,
                'description': field.description,
                'required': field.required,
                })
        info['attributes'] = attrs

        subs = []
        for occurence in signature.queryTaggedValue('directives', ()):
            subs.append({
                'name': occurence.tag,
                'occurence': occurence.__class__.__name__,
                })
        info['sub-directives'] = subs
        directives[signature] = info
    # Process Children
    for occurence in signature.queryTaggedValue('directives', ()):
        processSignature(occurence.tag, occurence.signature, directives)


if __name__ == '__main__':
    template = pagetemplate.RMLPageTemplateFile('rml-reference.pt')

    directives = {}
    processSignature('document', document.IDocument, directives)
    directives = sorted(directives.values(), key=lambda d: d['name'])

    pdf = template(types=getAttributeTypes(), directives=directives)
    open('rml-reference.pdf', 'w').write(pdf)
