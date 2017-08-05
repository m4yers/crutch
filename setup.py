"""Setup for crutch."""

import io
import sys
import ast

from setuptools import setup


def requirements():
  with io.open('requirements.txt') as file:
    return file.read()


def version():
  with io.open('VERSION') as file:
    return file.read()


def readme():
  with io.open('README.rst') as file:
    return file.read()


setup(
  name='crutch',
  version=version(),
  description='Gets a project running quickly',
  long_description=readme(),
  license='MIT',
  author='Artyom Goncharov',
  author_email='m4yers@gmail.com',
  url='https://github.com/m4yers/crutch',
  keywords='projects, bootstrap',
  install_requires=requirements(),
  package_data={
        'templates': ['*.*'],
  },
  # test_suite='test.test_crutch',
  # py_modules=['crutch'],
  # zip_safe=False,
  entry_points={'console_scripts': ['crutch = crutch:main']},
)
