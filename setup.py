#!/usr/bin/env python

from distutils.core import setup
import setuptools

setup(
    name='usable_image_scraper',
    version='1.0',
    description='package for scraping out images and metadata from public domain image libraries',
    author='Parker Phinney',
    author_email='parker@madebyparker.com',
    url='http://releaseourdata.com',
    py_modules = [
        'scraper',
        'config',
        'imginfo',
        'tests',
        ],
    packages=[
        'sites.cdc_phil_lib',
        'sites.fema_lib',
        ],
    install_requires=[
        'SQLAlchemy>=0.6.7',
        'unittest2',
        'BeautifulSoup',
        ],
    )
