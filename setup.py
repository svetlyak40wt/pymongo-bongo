#!/usr/bin/env python

import sys
import os
try:
    import subprocess
    has_subprocess = True
except:
    has_subprocess = False
import shutil

from ez_setup import use_setuptools
use_setuptools()

from setuptools import setup
from setuptools import Feature
from distutils.cmd import Command
from distutils.command.build_ext import build_ext
from distutils.errors import CCompilerError
from distutils.errors import DistutilsPlatformError, DistutilsExecError
from distutils.core import Extension

requirements = []
try:
    import xml.etree.ElementTree
except ImportError:
    requirements.append('elementtree')

f = open('README.rst')
try:
    try:
        readme_content = f.read()
    except:
        readme_content = ''
finally:
    f.close()

version = '0.1.2'

class GenerateDoc(Command):
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        path = 'doc/%s' % version

        shutil.rmtree('doc', ignore_errors=True)
        os.makedirs(path)

        if has_subprocess:
            subprocess.call(['epydoc', '--config', 'epydoc-config', '-o', path])
        else:
            print """
`setup.py doc` is not supported for this version of Python.

Please ask in the user forums for help.
"""


setup(
    name = 'pymongo-bongo',
    version = version,
    description = 'Sytax sugar for PyMongo and MongoDB <http://www.mongodb.org>',
    long_description = readme_content,
    author = 'Alexander Artemenko',
    author_email = 'svetlyak.40wt@gmail.com',
    url = 'http://github.com/svetlyak40wt/pymongo-bongo/',
    packages = ['mongobongo', ],
    install_requires = requirements,
    license = 'New BSD License',
    test_suite = 'nose.collector',
    classifiers = [
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: MacOS :: MacOS X',
        'Operating System :: Microsoft :: Windows',
        'Operating System :: POSIX',
        'Programming Language :: Python',
        'Topic :: Database'],
    cmdclass = {'doc': GenerateDoc},
)

