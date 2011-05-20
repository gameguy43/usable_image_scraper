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

def subject_to_html(list):
    retval = "<ul>"
    for category in list:
        retval += '<li>' + category + '</li>\n'
    retval += "</ul>"
    return retval

resolutions = {
    'hires' : {
        'status_column_name' : 'hires_status',
        'url_column_name'    : 'url_to_hires_img',
        'subdir'             : 'hires/',
        'extension'          : '.tif',
        },
    'lores' : {
        'status_column_name' : 'lores_status',
        'url_column_name'    : 'url_to_lores_img',
        'subdir'             : 'lores/',
        'extension'          : '.jpg',
        },
    'thumb' : {
        'status_column_name' : 'thumb_status',
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

our_fields = {
    'url_to_lores_img': {
        'column' : Column(String),
        },
    'url_to_hires_img': {
        'column' : Column(String),
        },
    'url_to_thumb_img': {
        'column' : Column(String),
        },
    'hires_status' : {
        'column': Column(Boolean, default=False),
        },
    'lores_status' : {
        'column': Column(Boolean, default=False),
        },
    'thumb_status' : {
        'column': Column(Boolean, default=False),
        },
    'page_permalink' : {
        'column': Column(String),
        },
    'access_time' : {
        'column': Column(Integer),
        },
    'doesnt_exist' : {
        'column': Column(Boolean),
        },
    'we_couldnt_parse_it' : {
        'column': Column(Boolean),
        },
#   'is_color = Column(Boolean)
    }



template_file = 'django_template.html'

def repr_as_html(image_as_dict, image_resolution_to_local_file_location_fxn):
    floorified = usable_image_scraper.scraper.floorify(image_as_dict['id'])
    id_zfilled = str(image_as_dict['id']).zfill(5)
    image_urls = {}
    for resolution in resolutions:
        image_urls[resolution] = image_resolution_to_local_file_location_fxn(resolution)

    # add link rel=license
    #image_as_dict['copyright'] = image_as_dict['copyright'].strip("'").replace('None', '<a href="http://creativecommons.org/licenses/publicdomain/" rel="license">None</a>')

    
    image_as_dict['next_id'] = int(image_as_dict['id']) + 1
    image_as_dict['prev_id'] = int(image_as_dict['id']) - 1

    
    image_as_dict['their_data'] = ''
    for key, data in their_fields.items():
        html_block = ''
        # if there's a pre-perscribed way to represent this field:
        if 'repr_as_html' in data:
            html_block = data['repr_as_html'](image_as_dict[key])
        # if not:
        else:
            html_block = '<span class="' + key + '">' + str(image_as_dict[key]) + '</span>'
        image_as_dict['their_data'] = ''.join([image_as_dict['their_data'], html_block])
        

    template_str = get_template_str()
    template = Template(template_str)
    context = Context({'image': image_as_dict, 'image_urls': image_urls})
    html = template.render(context)
    return html



# the stuff below here should stand on its own

def prep_data_for_insertion(data_dict):
    if not data_dict:
        return data_dict
    for key, data in data_dict.items():
        if key in all_fields and 'serialize' in all_fields[key] and all_fields[key]['serialize']:
            data_dict[key] = json.dumps(data_dict[key])
    return data_dict

def re_objectify_data(data_dict):
    if not data_dict:
        return data_dict
    for key, data in data_dict.items():
        if key in all_fields and 'serialize' in all_fields[key] and all_fields[key]['serialize']:
            data_dict[key] = json.loads(data_dict[key])
    return data_dict

def get_template_str():
    path = os.path.dirname(__file__)
    relpath = os.path.relpath(path)
    template_relpath = relpath + '/' + template_file
    fp = open(template_relpath, 'r')
    template_as_str = fp.read()
    return template_as_str

Base = declarative_base()

class OurMetadata(Base):
    __tablename__ = table_name
    id = Column(Integer, primary_key=True)

all_fields = dict(their_fields.items() + our_fields.items())

for fieldname, fieldinfo in all_fields.items():
    setattr(OurMetadata, fieldname, fieldinfo['column'])

def get_field_key_by_full_name(full_name):
    for key, data in their_fields.items():
        if not data['full_name']:
            continue
        if data['full_name'] == full_name:
            return key
    return False
