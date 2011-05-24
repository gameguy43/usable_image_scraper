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
        'type' : 'string',
        'dc_mapping' : 'dcterms:title',
        },
    'contact' : {
        'full_name' : 'Contact',
        'type' : 'string',
        },
    'creator' : {
        'full_name' : 'Creator',
        'type' : 'string',
        'dc_mapping' : 'dcterms:creator',
        },
    'desc' : {
        'full_name' : 'Description',
        'type' : 'string',
        'dc_mapping' : 'dcterms:description',
        },
    'subject' : {
        'full_name' : 'Subject',
        'type' : 'string',
        'repr_as_html' : subject_to_html,
        'serialize' : True,
        },
    'location' : {
        'full_name' : 'Location',
        'type' : 'string',
        #'dc_mapping' : 'dcterms:coverage',
        # actually, i don't think this qualifies as the "The spatial or temporal topic of the resource"
        },
    'publisher' : {
        'full_name' : 'Publisher',
        'type' : 'string',
        'dc_mapping' : 'dcterms:publisher',
        },
    'date_of_original' : {
        'full_name' : 'Date of Original',
        'type' : 'string',
        'dc_mapping' : 'dcterms:date',
        },
    'type' : {
        'full_name' : 'Type',
        'type' : 'string',
        'dc_mapping' : 'dcterms:format',
        },
    'format' : {
        'full_name' : 'Format',
        'type' : 'string',
        'dc_mapping' : 'dcterms:format',
        },
    'file_size' : {
        'full_name' : 'File Size',
        'type' : 'string',
        'dc_mapping' : 'dcterms:format',
        },
    'height' : {
        'full_name' : 'Height',
        'type' : 'string',
        'dc_mapping' : 'dcterms:format',
        },
    'width' : {
        'full_name' : 'Width',
        'type' : 'string',
        'dc_mapping' : 'dcterms:format',
        },
    'color_space' : {
        'full_name' : 'Color Space',
        'type' : 'string',
        'dc_mapping' : 'dcterms:format',
        },
    'item_id' : {
        'full_name' : 'Item ID',
        'type' : 'string',
        'dc_mapping' : 'dcterms:identifier',
        },
    'source' : {
        'full_name' : 'Source',
        'type' : 'string',
        },
    'language' : {
        'full_name' : 'Language',
        'type' : 'string',
        'dc_mapping' : 'dcterms:language',
        },
    'rights' : {
        'full_name' : 'Rights',
        'type' : 'string',
        'dc_mapping' : 'dcterms:rights',
        },
    'audience' : {
        'full_name' : 'Audience',
        'type' : 'string',
        },
    'date_created' : {
        'full_name' : 'Date created',
        'type' : 'string',
        'dc_mapping' : 'dcterms:date',
        },
    'date_modified' : {
        'full_name' : 'Date modified',
        'type' : 'string',
        'dc_mapping' : 'dcterms:date',
        },
    }

def get_field_key_by_full_name(full_name):
    for key, data in their_fields.items():
        if not data['full_name']:
            continue
        if data['full_name'] == full_name:
            return key
    return False
