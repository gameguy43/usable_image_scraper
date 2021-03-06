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
from sqlalchemy.ext.sqlsoup import SqlSoup
import sqlalchemy
import threading
import copy
import random

# thanks, http://farmdev.com/talks/unicode/
def to_unicode_or_bust(obj, encoding='utf-8'):
    if isinstance(obj, basestring):
        if not isinstance(obj, unicode):
            obj = unicode(obj, encoding)
    return obj

class DB:
    ##### INSTANTIATION
    def __init__(self, data_schema, db_url, metadata_table_name, scraper=None):
        self.scraper = scraper
        self.their_fields = copy.deepcopy(data_schema.their_fields)
        self.resolutions = data_schema.resolutions
        self.db_url = db_url

    
        self.our_fields = {
            'page_permalink' : {
                'column': Column(String(1000, convert_unicode=True)),
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
            #'is_color = Column(Boolean)
            }

        resolutions_columns = []
        for resolution, data in self.resolutions.items():
            resolutions_columns.append((data['status_column_name'], {'column' : Column(Boolean, default=False)}))
            resolutions_columns.append((data['url_column_name'], {'column' : Column(String(1000, convert_unicode=True))}))
            resolutions_columns.append((data['too_big_column_name'], {'column' : Column(Boolean, default=False)}))
        self.our_fields.update(dict(resolutions_columns))

        def column_type_to_column_obj(type):
            if type == 'string':
                return Column(Text(9000, convert_unicode=True))
            else:
                print "what the heck kind of type is that?!?!?!?"

        for index in self.their_fields.keys():
            self.their_fields[index]['column'] = column_type_to_column_obj(self.their_fields[index]['type'])
            
        ## glue all of the fields together
        self.all_fields = dict(self.their_fields.items() + self.our_fields.items())

        ## generate the metadata class
        self.base = declarative_base()
        class OurMetadata(self.base):
            __tablename__ = data_schema.table_name
            id = Column(Integer, primary_key=True)
        for fieldname, fieldinfo in self.all_fields.items():
            setattr(OurMetadata, fieldname, fieldinfo['column'])
        
        ## create the db
        #self.db = SqlSoup(db_url + '?charset=utf8&use_unicode=0', expire_on_commit=True)
        from sqlalchemy.orm import scoped_session, sessionmaker
        self.db = SqlSoup(db_url + '?charset=utf8&use_unicode=0', session=scoped_session(sessionmaker(expire_on_commit=True)))
        self.db.engine.raw_connection().connection.text_factory = unicode

        # make the tables if they don't already exist
        self.base.metadata.create_all(self.db.engine)
        self.db.commit()

        # make it easier to grab metadata table object
        self.metadata_table = getattr(self.db, metadata_table_name)
        if not self.metadata_table:
            print "crap, something has gone really wrong. couldn't grab the metadata table"
            
        #TODO: i think that maybe i can remove this. but not sure. probs need for sqlite.
        self.db_lock = threading.Lock()



    ### SERIALIZATION

    # serialize data before putting it in the database
    def prep_data_for_insertion(self, data_dict):
        if not data_dict:
            return data_dict
        for key, data in data_dict.items():
            if key in self.all_fields and 'serialize' in self.all_fields[key] and self.all_fields[key]['serialize']:
                data_dict[key] = json.dumps(data_dict[key])
        return data_dict

    # de-serialize and decode to unicode the data after pulling it from the database
    def re_objectify_data(self, data_dict):
        if not data_dict:
            return data_dict
        data_dict['id'] = int(data_dict['id'])
        for key, data in data_dict.items():
            if key in self.all_fields and 'serialize' in self.all_fields[key] and self.all_fields[key]['serialize']:
                if data_dict[key]:
                    data_dict[key] = json.loads(data_dict[key])
            else:
                data_dict[key] = to_unicode_or_bust(data_dict[key])
        return data_dict




    ##### READ-ONLY OPERATIONS

    ### BASE: Actually grab things from the database.
    ### many of the below functions use these
    # NOTE: careful about using this directly. it doesn't "uncompress" the data after pulling it from the db
    def get_image_metadata(self, id):
        #with self.db_lock:
        return self.metadata_table.get(id)

    def get_image_metadata_dict(self, id):
        # we run this through dict() so that we're manipulating a copy, not the actual object, which it turns out is cached or something
        row = self.get_image_metadata(id)
        if not row:
            return None
        row_dict = dict(row.__dict__)
        objectified_dict = self.re_objectify_data(row_dict)
        del objectified_dict['_sa_instance_state'] # sqlalchemy throws this sucker in. dont want it.
        return objectified_dict
        
    def get_resolution_url_column_name(self, resolution):
        return self.resolutions[resolution]['url_column_name']
    def get_resolution_url_column(self, resolution):
        column_name = self.get_resolution_url_column_name(resolution)
        return getattr(self.db, column_name)
    def get_resolution_url(self, resolution, id):
        row = self.metadata_table.get(id)
        url_column_name = self.get_resolution_url_column_name(resolution)
        return getattr(row, url_column_name)
    #TODO: pretty sure these are the same function
    def get_resolution_image_url(self, id, resolution):
        metadata_url_column_name = self.resolutions[resolution]['url_column_name']
        url = getattr(self.metadata_table.get(id), metadata_url_column_name)
        return url
        
    def get_resolution_status_column_name(self, resolution):
        return self.resolutions[resolution]['status_column_name']
    def get_resolution_status_column(self, resolution):
        the_status_column_name = self.get_resolution_status_column_name(resolution)
        the_status_column = getattr(self.metadata_table, the_status_column_name)
        return the_status_column
    def get_resolution_status(self, id, resolution):
        dict = self.get_image_metadata_dict(id)
        column_name = self.get_resolution_status_column_name(resolution)
        return dict.get(column_name)


    def get_resolution_too_big_column_name(self, resolution):
        return self.resolutions[resolution]['too_big_column_name']
    def get_resolution_too_big_column(self, resolution):
        column_name = self.get_resolution_too_big_column_name(resolution)
        column = getattr(self.metadata_table, column_name)
        return column
    def get_is_marked_as_too_big(self, id, resolution):
        dict = self.get_image_metadata_dict(id)
        too_big_column_name = self.get_resolution_too_big_column_name(resolution)
        if dict[too_big_column_name]:
            return True
        return False

    def get_valid_images(self):
        criteria = []
        for resolution in self.resolutions.keys():
            criteria.append(self.get_resolution_status_column(resolution) == True)
        where = sqlalchemy.or_(*criteria)
        return self.metadata_table.filter(where)
        
    def get_next_successful_image_id(self, id):
        where = self.metadata_table.id > id
        higher_id = self.get_valid_images().filter(where).first()
        if not higher_id:
            return id
        retval = int(higher_id.id)
        return retval
    def get_prev_successful_image_id(self, id):
        where = self.metadata_table.id < id
        lower_id = self.get_valid_images().filter(where).order_by(sqlalchemy.desc(self.metadata_table.id)).first()
        if not lower_id:
            return id
        retval = int(lower_id.id)
        return retval

    ## input: resolution, as a string (hires, lores, thumb)
    ## returns: list of tuples in form: (id, url)
    def get_set_images_to_dl(self,resolution):
        the_status_column = self.get_resolution_status_column(resolution)
        where = sqlalchemy.or_(the_status_column == False, the_status_column == None)
        #rows_to_dl = self.metadata_table.filter(where).filter(sqlalchemy.not_(self.get_resolution_too_big_column(resolution) == True)).all()
        rows_to_dl = self.metadata_table.filter(where).all()
        ids_to_dl = map(lambda row: row.id, rows_to_dl)
        metadata_url_column_name = self.get_resolution_url_column_name(resolution)
        tuples = map(lambda id: (id, getattr(self.metadata_table.get(id), metadata_url_column_name)), ids_to_dl)
        # throw away tuples that have a null value in either position
        # TODO: maybe we should throw an exception here?
        tuples = filter(lambda tuple: tuple[0] and tuple[1], tuples)
        return tuples

    def get_highest_id_in_our_db(self):
        try:
            id = int(self.metadata_table.order_by(sqlalchemy.desc(self.metadata_table.id)).first().id)
        except:
            id = 1
        return id

    def get_random_valid_image_id(self):
        possibilities = self.get_valid_images()
        num_possibilities = possibilities.count()
        choice = random.randrange(num_possibilities)
        return possibilities[choice].id

    def get_num_images(self):
        # yeah, the below where statement really sucks
        # i can't just filter by != True. it returns 0 results. i don't know why.
        mywhere = sqlalchemy.or_(self.metadata_table.we_couldnt_parse_it == False, self.metadata_table.we_couldnt_parse_it == None)
        return self.metadata_table.filter(mywhere).count()



    ##### WRITE-ONLY OPERATIONS

    ### BASE: Actually insert or update a row in the database
    ### many of the below functions use these
    #NOTE: this only works if the primary key is 'id'
    def insert_or_update_table_row(self, table, new_data_dict):
        if not new_data_dict:
            print "you're trying to insert a blank dict. that's pretty lame."
            return False
        # merge the new and the old into a fresh dict
        existing_row = table.get(new_data_dict['id'])
        if existing_row:
            existing_row_data_dict = existing_row.__dict__
            final_row_data_dict = existing_row_data_dict
            for key, value in new_data_dict.items():
                final_row_data_dict[key] = value
            #write over the current row contents with it
            #with self.db_lock:
            self.db.delete(existing_row)
            self.db.commit()
        else: 
            final_row_data_dict = new_data_dict
        #with self.db_lock:
        table.insert(**final_row_data_dict)
        self.db.commit()
    def store_metadata_row(self, metadata_dict):
        if not metadata_dict.has_key('we_couldnt_parse_it'):
            metadata_dict['we_couldnt_parse_it'] = 0
        metadata_dict = self.prep_data_for_insertion(metadata_dict)
        self.insert_or_update_table_row(self.metadata_table, metadata_dict)

    def mark_img_as_not_downloaded(self, id, resolution):
        status_column_name = self.get_resolution_status_column_name(resolution)
        data = {}
        data['id'] = id
        data[status_column_name] = False
        self.store_metadata_row(data)
    def mark_img_as_downloaded(self, id, resolution):
        status_column_name = self.get_resolution_status_column_name(resolution)
        data = {}
        data['id'] = id
        data[status_column_name] = True
        self.store_metadata_row(data)
    def mark_img_as_too_big(self, id, resolution):
        status_column_name = self.get_resolution_too_big_column_name(resolution)
        data = {}
        data['id'] = id
        data[status_column_name] = True
        self.store_metadata_row(data)

    # DELETE EVERYTHING. CAREFUL!
    def truncate_all_tables(self):
        print "================================"
        print "LIKE SERIOUSLY I AM ABOUT TO DELETE ALL THE TABLES RIGHT NOW OH BOY"
        print self.db_url
        print "================================"
        meta = MetaData(self.db.engine)
        meta.reflect()
        meta.drop_all()
        meta.create_all()

        '''
        for table in reversed(self.base.metadata.sorted_tables):
            print table
            table.delete()
            self.db.commit()
        self.base.metadata.create_all(self.db.engine)
        self.db.commit()
        '''


    ### HELPERS

    def get_field_key_by_full_name(self, full_name):
        for key, data in self.their_fields.items():
            if not data['full_name']:
                continue
            if data['full_name'] == full_name:
                return key
        return False


    ##### OTHER
    def repr_as_html(self, image_as_dict, image_resolution_to_local_file_location_fxn):
        if not image_as_dict:
            return u""
        floorified = usable_image_scraper.scraper.floorify(image_as_dict['id'])
        id_zfilled = str(image_as_dict['id']).zfill(5)
        image_urls = {}
        for resolution in self.resolutions:
            image_urls[resolution] = image_resolution_to_local_file_location_fxn(resolution)

        # add link rel=license
        #image_as_dict['copyright'] = image_as_dict['copyright'].strip("'").replace('None', '<a href="http://creativecommons.org/licenses/publicdomain/" rel="license">None</a>')

        image_as_dict['next_id'] = int(image_as_dict['id']) + 1
        image_as_dict['prev_id'] = int(image_as_dict['id']) - 1
        
        image_as_dict['their_data'] = u''
        for key, data in self.their_fields.items():
            if not key in image_as_dict or not image_as_dict[key]:
                continue
            html_block = '<p class="datapoint">'
            # if there's a pre-perscribed way to represent this field:
            html_block += '<label for="' + key + '">' + self.their_fields[key]['full_name'] + ': </label>'
            rdfa_clause = ''
            if 'dc_mapping' in data:
                rdfa_clause = ' property="' + data['dc_mapping'] + '"'
            if 'repr_as_html' in data:
                html_block += data['repr_as_html'](image_as_dict[key])
            # if not:
            else:
                html_block += '<span id="' + key + '"' + rdfa_clause + '>' + unicode(image_as_dict[key]) + '</span>'
            html_block += '</p>'
            image_as_dict['their_data'] += html_block
            
        def get_template_str():
            template_file = 'django_template.html'
            path = os.path.dirname(__file__)
            relpath = os.path.relpath(path)
            template_relpath = relpath + '/' + template_file
            fp = open(template_relpath, 'r')
            template_as_str = fp.read()
            return template_as_str

        # the table of image downloads
        image_as_dict['download_links'] = u'<table id="download_links">'
        for resolution, data in self.scraper.resolutions.items():
            image_as_dict['download_links'] += u'<tr>'
            image_as_dict['download_links'] += u'<td>' + resolution + ':</td>'
            orig_url = self.get_resolution_url(resolution, image_as_dict['id'])
            #image_as_dict['download_links'] += u'<td><a href="' + orig_url + '">' + self.scraper.abbrev.upper() + '</a></td>'
            image_as_dict['download_links'] += u'<td><a href="' + orig_url + '">Original</a></td>'
            # if we've downloaded the image
            if self.get_resolution_status(image_as_dict['id'], resolution):
                our_url = self.scraper.get_web_resolution_local_image_location(resolution, image_as_dict['id'], remote_url=orig_url)
                image_as_dict['download_links'] += u'<td><a href="' + our_url + '">Usable Image Mirror</a></td>'
            else:
                image_as_dict['download_links'] += u'<td></td>'
        image_as_dict['download_links'] += u'</table>'
                

        template_str = get_template_str()
        template = Template(template_str)
        context = Context({'image': image_as_dict, 'image_urls': image_urls})
        html = template.render(context)
        return html
