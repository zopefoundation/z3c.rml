#!python
from setuptools import setup, find_packages

setup (
    name='z3c.rml',
    version='0.5',
    author = "Stephan Richter and the Zope Community",
    author_email = "zope3-dev@zope.org",
    description = "An alternative implementation of RML",
    license = "ZPL 2.1",
    keywords = "zope3 rml reportlab pdf pagetemplate",
    url = 'svn://svn.zope.org/repos/main/z3c.rml',
    packages = find_packages('src'),
    include_package_data = True,
    package_dir = {'':'src'},
    namespace_packages = ['z3c'],
    extras_require = dict(
        test = ['zope.testing'],
        pagetemplate = ['zope.pagetemplate']
        ),
    install_requires = [
        # ReportLab does not seem to upload their packages to PyPI
        # 'reportlab',
        'setuptools',
        'zope.interface',
        ],
    dependency_links = ['http://download.zope.org/distribution']
    )

