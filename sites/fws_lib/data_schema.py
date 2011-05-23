################################################################################
################################################################################
#####################                                  #########################
#####################         Release Our Data         #########################
#####################                                  #########################
#####################       a HelloSilo Project        #########################
#####################       <ROD@hellosilo.com>        #########################
################################################################################
##                                                                            ##  
##     Copyright 2010                                                         ##
##                                                                            ##  
##         Parker Phinney   @gameguy43   <parker@madebyparker.com>            ##
##         Seth Woodworth   @sethish     <seth@sethish.com>                   ##
##                                                                            ##
##                                                                            ##
##     Licensed under the GPLv3 or later,                                     ##
##     see PERMISSION for copying permission                                  ##
##     and COPYING for the GPL License                                        ##
##                                                                            ##
################################################################################
################################################################################

#from sqlalchemy.ext.declarative import declarative_base
#from sqlalchemy.orm import sessionmaker, mapper

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import *
import json
import os.path
from django.template import Template, Context
import usable_image_scraper.scraper

table_name = 'fws_metadata'
template_file = 'django_template.html'

def subject_to_html(list):
    retval = "<ul>"
    for category in list:
        retval += '<li>' + category + '</li>\n'
    retval += "</ul>"
    return retval

resolutions = {
    'hires' : {
        'status_column_name' : 'hires_status',
        'too_big_column_name': 'hires_too_big',
        'url_column_name'    : 'url_to_hires_img',
        'subdir'             : 'hires/',
        'extension'          : '.tif',
        },
    'lores' : {
        'status_column_name' : 'lores_status',
        'too_big_column_name': 'lores_too_big',
        'url_column_name'    : 'url_to_lores_img',
        'subdir'             : 'lores/',
        'extension'          : '.jpg',
        },
    'thumb' : {
        'status_column_name' : 'thumb_status',
        'too_big_column_name': 'thumb_too_big',
        'url_column_name'    : 'url_to_thumb_img',
        'subdir'             : 'thumb/',
        'extension'          : '.jpg',
        },
    }

their_fields = {
    'title' : {
        'full_name' : 'Title',
        'column' : Column(String),
        },
    'contact' : {
        'full_name' : 'Contact',
        'column' : Column(String),
        },
    'creator' : {
        'full_name' : 'Creator',
        'column' : Column(String),
        },
    'desc' : {
        'full_name' : 'Description',
        'column' : Column(String),
        },
    'subject' : {
        'full_name' : 'Subject',
        'column' : Column(String),
        'repr_as_html' : subject_to_html,
        'serialize' : True,
        },
    'location' : {
        'full_name' : 'Location',
        'column' : Column(String),
        },
    'publisher' : {
        'full_name' : 'Publisher',
        'column' : Column(String),
        },
    'date_of_original' : {
        'full_name' : 'Date of Original',
        'column' : Column(String),
        },
    'type' : {
        'full_name' : 'Type',
        'column' : Column(String),
        },
    'format' : {
        'full_name' : 'Format',
        'column' : Column(String),
        },
    'item_id' : {
        'full_name' : 'Item ID',
        'column' : Column(String),
        },
    'source' : {
        'full_name' : 'Source',
        'column' : Column(String),
        },
    'language' : {
        'full_name' : 'Language',
        'column' : Column(String),
        },
    'rights' : {
        'full_name' : 'Rights',
        'column' : Column(String),
        },
    'file_size' : {
        'full_name' : 'File Size',
        'column' : Column(String),
        },
    'height' : {
        'full_name' : 'Height',
        'column' : Column(String),
        },
    'width' : {
        'full_name' : 'Width',
        'column' : Column(String),
        },
    'color_space' : {
        'full_name' : 'Color Space',
        'column' : Column(String),
        },
    'audience' : {
        'full_name' : 'Audience',
        'column' : Column(String),
        },
    'date_created' : {
        'full_name' : 'Date created',
        'column' : Column(String),
        },
    'date_modified' : {
        'full_name' : 'Date modified',
        'column' : Column(String),
        },
    }

def get_field_key_by_full_name(full_name):
    for key, data in their_fields.items():
        if not data['full_name']:
            continue
        if data['full_name'] == full_name:
            return key
    return False
