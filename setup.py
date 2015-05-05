#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

version = "0.1.1"

if sys.argv[-1] == 'publish':
    try:
        import wheel
    except ImportError:
        raise ImportError("Fix: pip install wheel")
    os.system('python setup.py sdist bdist_wheel upload')
    print("You probably want to also tag the version now:")
    print("  git tag -a %s -m 'version %s'" % (version, version))
    print("  git push --tags")
    sys.exit()


readme = open('README.rst').read()
history = open('HISTORY.rst').read().replace('.. :changelog:', '')

def get_requirements(filename):
    f = open(filename).read()
    reqs = [
            # loop through list of requirements
            x.strip() for x in f.splitlines()
                # filter out comments and empty lines
                if not x.strip().startswith('#')
            ]
    return reqs

setup(
    name='analyzerstrategies',
    version=version,
    description="""Analyzer Strategies""",
    long_description=readme + '\n\n' + history,
    author='Leonardo Lazzaro',
    author_email='llazzaro@dc.uba.ar',
    url='https://github.com/llazzaro/analyzerstrategies',
    include_package_data=True,
    py_modules=['analyzerstrategies'],
    install_requires=get_requirements('requirements.txt'),
    license="BSD",
    zip_safe=False,
    keywords='analyzerstrategies',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Natural Language :: English',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
    ],

)
