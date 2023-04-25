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
"""Setup"""
import os

from setuptools import find_packages
from setuptools import setup


def read(*rnames):
    return open(os.path.join(os.path.dirname(__file__), *rnames)).read()


TESTS_REQUIRE = [
    'mock',
    'Pillow',
    'coverage',
    'zope.pagetemplate',
    'zope.testrunner',
]


setup(
    name="z3c.rml",
    version='4.3.0',
    author="Stephan Richter and the Zope Community",
    author_email="zope-dev@zope.dev",
    description="An alternative implementation of RML",
    long_description=(
        read('README.rst')
        + '\n\n' +
        read('CHANGES.rst')
    ),
    license="ZPL 2.1",
    python_requires='>=3.7',
    keywords="rml reportlab pdf pagetemplate",
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Zope Public License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: Implementation :: CPython',
        'Natural Language :: English',
        'Operating System :: OS Independent',
    ],
    url='https://github.com/zopefoundation/z3c.rml',
    packages=find_packages('src'),
    package_dir={'': 'src'},
    namespace_packages=['z3c'],
    extras_require=dict(
        test=TESTS_REQUIRE,
        pagetemplate=[
            'zope.pagetemplate']
    ),
    install_requires=[
        'Pygments',
        'backports.tempfile',
        'lxml',
        'pikepdf>=3.0',
        'reportlab>=3.5.0',
        'setuptools',
        'svglib',
        'zope.interface',
        'zope.schema',
    ],
    entry_points={
        'console_scripts': [
            'rml2pdf = z3c.rml.rml2pdf:main',
            'dtd = z3c.rml.dtd:main',
            'reference = z3c.rml.reference:main'],
    },
    include_package_data=True,
    zip_safe=False,
)
