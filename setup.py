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
"""Setup
"""
import os
from setuptools import setup, find_packages

def read(*rnames):
    return open(os.path.join(os.path.dirname(__file__), *rnames)).read()

setup (
    name='z3c.rml',
    version='1.0.0',
    author = "Stephan Richter and the Zope Community",
    author_email = "zope-dev@zope.org",
    description = "An alternative implementation of RML",
    long_description=(
        read('README.txt')
        + '\n\n' +
        read('CHANGES.txt')
        ),
    license = "ZPL 2.1",
    keywords = "zope3 rml reportlab pdf pagetemplate",
    classifiers = [
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Zope Public License',
        'Programming Language :: Python',
        'Natural Language :: English',
        'Operating System :: OS Independent'],
    url = 'http://pypi.python.org/pypi/z3c.rml',
    packages = find_packages('src'),
    package_dir = {'':'src'},
    namespace_packages = ['z3c'],
    extras_require = dict(
        test = [
            'zope.pagetemplate',
            'zope.testing',
            'PIL'],
        pagetemplate = [
            'zope.pagetemplate']
        ),
    install_requires = [
        'lxml',
        'pyPdf',
        'reportlab',
        'setuptools',
        'zope.interface',
        'zope.schema',
        ],
    entry_points = {
        'console_scripts': [
            'dtd = z3c.rml.dtd:main',
            'reference = z3c.rml.reference:main'],
        },
    include_package_data = True,
    zip_safe = False,
    )

