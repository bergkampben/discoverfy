"""Discoverfy python package configuration."""

from setuptools import setup

setup(
    name='discoverfy',
    version='0.1.0',
    packages=['discoverfy'],
    include_package_data=True,
    install_requires=[
        'Flask==1.0',
        'html5validator==0.2.8',
        'pycodestyle==2.3.1',
        'pydocstyle==2.0.0',
        'pylint==1.8.1',
        'nodeenv==1.2.0',
        'sh==1.12.14',
        'arrow==0.10.0',
        'requests==2.18.4',
        'apscheduler'
    ],
)
