"""Setup for crutch."""

import io

from setuptools import setup


def requirements():
  with io.open('requirements.txt') as out:
    return out.read()


def version():
  with io.open('VERSION') as out:
    return out.read()


def readme():
  with io.open('README.rst') as out:
    return out.read()


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
    entry_points={'console_scripts': ['crutch = crutch:main']},
)
