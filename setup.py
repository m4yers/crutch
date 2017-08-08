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
    description='Get a project running quickly',
    long_description=readme(),
    license='MIT',
    author='Artyom Goncharov',
    author_email='m4yers@gmail.com',
    url='https://github.com/m4yers/crutch',
    keywords='projects, bootstrap',
    install_requires=requirements(),
    python_requires='>=2.7, <3',
    package_data={
        'templates': ['*.*'],
    },
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Build Tools',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
    ],
    entry_points={'console_scripts': ['crutch = crutch:main']},
)
