#!/usr/bin/env python3

from setuptools import setup, find_packages

setup(
    name='emharvest',
    version='1.0.0',
    packages=['emharvest'],
    package_dir={'emharvest': 'core'},
    description='A system for parsing TFS EPU and SerialEM data structures',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    license='BSD 3-Clause License',
    author='Kyle Morris',
    author_email='kyle@ebi.ac.uk',
    url='https://github.com/emdb-empiar/EMharvest',
    install_requires=[
        'glom',
        'tqdm',
        'pandas',
        'numpy',
        'scikit-learn',
        'matplotlib',
        'seaborn',
        'scipy',
        'xmltodict',
        'rich',
        'starparser',
        'mrcfile',
        'gemmi',
        'starfile',
        'pyem',
        'fpdf',
        'Pillow',
        'PyQt5',
        'mmcif'
        # Add any additional dependencies here
    ],
    python_requires='>=3.6', # Specify your Python version requirement
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        # More classifiers: https://pypi.org/classifiers/
    ],
)
