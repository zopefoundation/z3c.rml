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

def alltests():
    import os
    import sys
    import unittest
    # use the zope.testrunner machinery to find all the
    # test suites we've put under ourselves
    import zope.testrunner.find
    import zope.testrunner.options
    here = os.path.abspath(os.path.join(os.path.dirname(__file__), 'src'))
    args = sys.argv[:]
    defaults = ["--test-path", here]
    options = zope.testrunner.options.get_options(args, defaults)
    suites = list(zope.testrunner.find.find_suites(options))
    return unittest.TestSuite(suites)

TESTS_REQUIRE = [
    'Pillow',
    'coverage',
    'zope.pagetemplate',
    'zope.testrunner',
    ]

setup (
    name="z3c.rml",
    version='3.0.0',
    author="Stephan Richter and the Zope Community",
    author_email="zope-dev@zope.org",
    description="An alternative implementation of RML",
    long_description=(
        read('README.rst')
        + '\n\n' +
        read('CHANGES.rst')
        ),
    license="ZPL 2.1",
    keywords="zope3 rml reportlab pdf pagetemplate",
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Zope Public License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: Implementation :: CPython',
        'Natural Language :: English',
        'Operating System :: OS Independent'],
    url='http://pypi.python.org/pypi/z3c.rml',
    packages=find_packages('src'),
    package_dir={'':'src'},
    namespace_packages=['z3c'],
    extras_require=dict(
        test=TESTS_REQUIRE,
        pagetemplate=[
            'zope.pagetemplate']
        ),
    install_requires=[
        'Pygments',
        'lxml',
        'PyPDF2>=1.25.1',
        'reportlab>=3.1.44',
        'setuptools',
        'six',
        'zope.interface',
        'zope.schema',
        ],
    entry_points={
        'console_scripts': [
            'rml2pdf = z3c.rml.rml2pdf:main',
            'dtd = z3c.rml.dtd:main',
            'reference = z3c.rml.reference:main'],
        },
    tests_require=TESTS_REQUIRE,
    test_suite='__main__.alltests',
    include_package_data=True,
    zip_safe=False,
    )
