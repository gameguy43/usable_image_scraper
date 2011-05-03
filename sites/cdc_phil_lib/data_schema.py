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
    'desc' : {
        'column' : Column(String),
        },
    'categories' : {
        'column' : Column(String),
        },
    'credit' : {
        'column' : Column(String),
        },
    'links' : {
        'column' : Column(String),
        },
    'provider' : {
        'column': Column(String),
        },
    'source' : {
        'column': Column(String),
        },
    # the following 3 /need/ to have these names
    # or at least make sure they're consistent with the below fxn
    'copyright' : {
        'column': Column(String),
        },
    'creation' : {
        'column': Column(String),
        },
}

our_fields = {
    'url_to_hires_img' : {
        'column': Column(String),
        },
    'url_to_lores_img' : {
        'column': Column(String),
        },
    'url_to_thumb_img' : {
        'column': Column(String),
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
    'hires_status' : {
        'column': Column(Boolean, default=False),
        },
    'lores_status' : {
        'column': Column(Boolean, default=False),
        },
    'thumb_status' : {
        'column': Column(Boolean, default=False),
        },
#   'is_color = Column(Boolean)
    }

def prep_data_for_insertion(data_dict):
    if 'links' in data_dict:
        data_dict['links'] = json.dumps(data_dict['links'])
    if 'categories' in data_dict:
        data_dict['categories'] = json.dumps(data_dict['categories'])
    return data_dict

def re_objectify_data(data_dict):
    if 'links' in data_dict:
        data_dict['links'] = json.loads(data_dict['links'])
    if 'categories' in data_dict:
        data_dict['categories'] = json.loads(data_dict['categories'])
    return data_dict


'''

    def floorify(id):
        ## mod 100 the image id numbers to make smarter folders
        floor = id - id % 100
        floored = str(floor).zfill(5)[0:3]+"XX"
        return floored


    floorified = floorify(image['id'])
    id_zfilled = str(image['id']).zfill(5)
    image_urls = {
        'hires':  settings.RELATIVE_DATA_ROOT + 'hires/' + floorified + "/" + id_zfilled + ".tif",
        'lores':  settings.RELATIVE_DATA_ROOT + 'lores/' + floorified + "/" + id_zfilled + ".jpg",
        'thumb':  settings.RELATIVE_DATA_ROOT + 'thumbs/' + floorified + "/" + id_zfilled + ".jpg",
    }

    # add link rel=license
    image['copyright'] = image['copyright'].strip("'").replace('None', '<a href="http://creativecommons.org/licenses/publicdomain/" rel="license">None</a>')
'''


def links_to_html(json_str):
    parsed = json.loads(json_str)
    retval = "<ul>"
    for string, url in parsed:
        retval += '<li><a href="' + url + '">' + string + "</a></li>\n";
    retval += "</ul>"
    return retval

def categories_to_html(json_str):
    retval = "<ul>"
    parsed = json.loads(json_str)
    def print_with_spaces(dictionary, spaces):
        retval = ''
        if dictionary:
            for key in dictionary.keys():
                retval += "<li>" + "&nbsp;"*spaces + key + "</li>\n"
                retval += print_with_spaces(dictionary[key], spaces+1)
        return retval
    retval += print_with_spaces(parsed, 0)
    retval += "</ul>"
    return retval

template_file = 'django_template.html'

def get_template_str():
    path = os.path.dirname(__file__)
    relpath = os.path.relpath(path)
    template_relpath = relpath + '/' + template_file
    fp = open(template_relpath, 'r')
    template_as_str = fp.read()
    return template_as_str

def floorify(id):
    ## mod 100 the image id numbers to make smarter folders
    floor = id - id % 100
    floored = str(floor).zfill(5)[0:3]+"XX"
    return floored

def repr_as_html(image_as_dict, image_resolution_to_local_file_location_fxn):
    floorified = floorify(image_as_dict['id'])
    id_zfilled = str(image_as_dict['id']).zfill(5)
    image_urls = {}
    for resolution in resolutions:
        image_urls[resolution] = image_resolution_to_local_file_location_fxn(resolution)

    # add link rel=license
    image_as_dict['copyright'] = image_as_dict['copyright'].strip("'").replace('None', '<a href="http://creativecommons.org/licenses/publicdomain/" rel="license">None</a>')

    if image_as_dict['links']:
        image_as_dict['links'] = links_to_html(image_as_dict['links'])
    if image_as_dict['categories']:
        image_as_dict['categories'] = categories_to_html(image_as_dict['categories'])

    image_as_dict['next_id'] = int(image_as_dict['id']) + 1
    image_as_dict['prev_id'] = int(image_as_dict['id']) - 1
    template_str = get_template_str()
    template = Template(template_str)
    context = Context({'image': image_as_dict, 'image_urls': image_urls})
    html = template.render(context)
    return html


Base = declarative_base()

class CDCPhilMetadata(Base):
    __tablename__ = 'cdc_phil_metadata'
    id = Column(Integer, primary_key=True)

all_fields = dict(their_fields.items() + our_fields.items())

for fieldname, fieldinfo in all_fields.items():
    setattr(CDCPhilMetadata, fieldname, fieldinfo['column'])
