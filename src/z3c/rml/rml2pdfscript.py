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
"""RML to PDF Converter
"""
import subprocess
import sys
import os

_fileOpen = None

def excecuteSubProcess(xmlInputName, outputFileName, testing=None):
    # set the sys path given from the parent process
    sysPath = os.environ['Z3CRMLSYSPATH']
    sys.path[:] = sysPath.split(';')

    # now it come the ugly thing, but we need to hook our test changes into
    # our subprocess.
    if testing is not None:

        # set some globals
        import z3c.rml.attr
        import z3c.rml.directive
        global _fileOpen
        _fileOpen = z3c.rml.attr.File.open
        def testOpen(img, filename):
            # cleanup win paths like:
            # ....\\input\\file:///D:\\trunk\\...
            if sys.platform[:3].lower() == "win":
                if filename.startswith('file:///'):
                    filename = filename[len('file:///'):]
            path = os.path.join(os.path.dirname(xmlInputName), filename)
            return open(path, 'rb')
        # override some testing stuff for our tests
        z3c.rml.attr.File.open = testOpen
        import z3c.rml.tests.module
        sys.modules['module'] = z3c.rml.tests.module
        sys.modules['mymodule'] = z3c.rml.tests.module

    # import rml and process the pdf
    from z3c.rml import rml2pdf
    rml2pdf.go(xmlInputName, outputFileName)

    if testing is not None:
        # reset some globals
        z3c.rml.attr.File.open = _fileOpen
        del sys.modules['module']
        del sys.modules['mymodule']


def goSubProcess(xmlInputName, outputFileName, testing=False):
    """Processes PDF rendering in a sub process.

    This method is much slower then the ``go`` method defined in rml2pdf.py
    because each PDF generation is done in a sub process. But this will make
    sure, that we do not run into problems. Note, the ReportLab lib is not
    threadsafe.

    Use this method from python and it will dispatch the pdf generation
    to a subprocess.

    Note: this method does not take care on how much process will started.
    Probably it's a good idea to use a queue or a global utility which only
    start a predefined amount of sub processes.
    """
    # get the sys path used for this python process
    env = os.environ
    sysPath = ';'.join(sys.path)
    # set the sys path as env var for the new sub process
    env['Z3CRMLSYSPATH'] = sysPath
    py = sys.executable

    # setup the cmd
    program = [py, __file__, 'excecuteSubProcess', xmlInputName, outputFileName]
    if testing is True:
        program.append('testing=1')
    program = " ".join(program)

    # run the subprocess in the rml input file folder, this will make it easy
    # to include images. If this doesn't fit, feel free to add a additional
    # home argument, and let this be the default, ri
    os.chdir(os.path.dirname(xmlInputName))

    # start processing in a sub process, raise exception or return None
    try:
        p = subprocess.Popen(program, executable=py, env=env,
            stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE)
    except Exception as e:
        raise Exception("Subprocess error: %s" % e)

    # Do we need to improve the implementation and kill the subprocess which will
    # fail? ri
    stdout, stderr = p.communicate()
    error = stderr
    if error:
        raise Exception("Subprocess error: %s" % error)


if __name__ == '__main__':
    if len(sys.argv) == 5:
        #testing support
        canvas = excecuteSubProcess(sys.argv[2], sys.argv[3], sys.argv[4])
    else:
        canvas = excecuteSubProcess(sys.argv[2], sys.argv[3])

