#!/usr/bin/env python

from setuptools import setup

def local_requirements():
    req_list = []
    with open('requirements.txt') as requirements_file:
        req_list = [line.strip() for line in requirements_file.readlines()]
    install_reqs = list(filter(None, req_list))
    return install_reqs

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
