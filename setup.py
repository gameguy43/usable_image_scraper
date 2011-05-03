#!/usr/bin/env python

from distutils.core import setup

setup(name='usable_image_scraper',
    version='1.0',
    description='package for scraping out images and metadata from public domain image libraries',
    author='Parker Phinney',
    author_email='parker@madebyparker.com',
    url='http://releaseourdata.com',
    packages=[
        'usable_image_scraper.sites.cdc_phil_lib',
        'usable_image_scraper.sites.fema_lib',
        ],
    install_requires=[
        'SQLAlchemy<=0.6.8',
        'unittest2',
        ],
    )
