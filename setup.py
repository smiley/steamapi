#!/usr/bin/env python

from setuptools import setup
from pip.req import parse_requirements

def local_requirements():
    install_reqs = parse_requirements('./requirements.txt')
    return [str(ir.req) for ir in install_reqs]

setup(name='steamapi',
      version='0.1',
      description='An object-oriented Python 2.7+ library for accessing the Steam Web API',
      url='https://github.com/smiley/steamapi',
      author='Smiley',
      author_email='',
      license='MIT',
      packages=['steamapi'],
      install_requires=local_requirements(),
      zip_safe=False)
