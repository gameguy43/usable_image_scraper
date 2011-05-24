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


class DB:
    def __init__(self, data_schema, db_url, metadata_table_name, scraper=None):
        self.scraper = scraper
        self.their_fields = copy.deepcopy(data_schema.their_fields)
        self.resolutions = data_schema.resolutions

    
        self.our_fields = {
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
            #'is_color = Column(Boolean)
            }

        resolutions_columns = []
        for resolution, data in self.resolutions.items():
            resolutions_columns.append((data['status_column_name'], {'column' : Column(Boolean, default=False)}))
            resolutions_columns.append((data['url_column_name'], {'column' : Column(String)}))
            resolutions_columns.append((data['too_big_column_name'], {'column' : Column(Boolean, default=False)}))
        self.our_fields.update(dict(resolutions_columns))

        def column_type_to_column_obj(type):
            if type == 'string':
                return Column(String)
            else:
                print "what the heck kind of type is that?!?!?!?"

        for index in self.their_fields.keys():
            self.their_fields[index]['column'] = column_type_to_column_obj(self.their_fields[index]['type'])
            
        ## glue all of the fields together
        self.all_fields = dict(self.their_fields.items() + self.our_fields.items())

        ## generate the metadata class
        Base = declarative_base()
        class OurMetadata(Base):
            __tablename__ = data_schema.table_name
            id = Column(Integer, primary_key=True)
        for fieldname, fieldinfo in self.all_fields.items():
            setattr(OurMetadata, fieldname, fieldinfo['column'])
        
        ## create the db
        self.db = SqlSoup(db_url)
        #from sqlalchemy.orm import scoped_session, sessionmaker
        #db = SqlSoup(sql_url, session=scoped_session(sessionmaker(autoflush=False, expire_on_commit=False, autocommit=True)))

        # make the tables if they don't already exist
        Base.metadata.create_all(self.db.engine)
        self.db.commit()

        # make it easier to grab metadata table object
        self.metadata_table = getattr(self.db, metadata_table_name)
        if not self.metadata_table:
            print "crap, something has gone really wrong. couldn't grab the metadata table"
            

        #TODO: i think that maybe i can remove this. but not sure. probs need for sqlite.
        self.db_lock = threading.Lock()


    def repr_as_html(self, image_as_dict, image_resolution_to_local_file_location_fxn):
        if not image_as_dict:
            return ""
        floorified = usable_image_scraper.scraper.floorify(image_as_dict['id'])
        id_zfilled = str(image_as_dict['id']).zfill(5)
        image_urls = {}
        for resolution in self.resolutions:
            image_urls[resolution] = image_resolution_to_local_file_location_fxn(resolution)

        # add link rel=license
        #image_as_dict['copyright'] = image_as_dict['copyright'].strip("'").replace('None', '<a href="http://creativecommons.org/licenses/publicdomain/" rel="license">None</a>')

        
        image_as_dict['next_id'] = int(image_as_dict['id']) + 1
        image_as_dict['prev_id'] = int(image_as_dict['id']) - 1

        
        image_as_dict['their_data'] = ''
        for key, data in self.their_fields.items():
            if not key in image_as_dict or not image_as_dict[key]:
                continue
            html_block = '<p class="datapoint">'
            # if there's a pre-perscribed way to represent this field:
            html_block = html_block + '<strong class="label">' + self.their_fields[key]['full_name'] + ':</strong>'
            if 'repr_as_html' in data:
                html_block = html_block + data['repr_as_html'](image_as_dict[key])
            # if not:
            else:
                html_block = html_block + '<span class="' + key + '">' + str(image_as_dict[key]) + '</span>'
            html_block = ''.join([html_block, '</p>'])
            image_as_dict['their_data'] = ''.join([image_as_dict['their_data'], html_block])
            

        '''
        template_str = get_template_str()
        template = Template(template_str)
        context = Context({'image': image_as_dict, 'image_urls': image_urls})
        html = template.render(context)
        '''
        return html_block

    def prep_data_for_insertion(self, data_dict):
        if not data_dict:
            return data_dict
        for key, data in data_dict.items():
            if key in self.all_fields and 'serialize' in self.all_fields[key] and self.all_fields[key]['serialize']:
                data_dict[key] = json.dumps(data_dict[key])
        return data_dict

    def re_objectify_data(self, data_dict):
        if not data_dict:
            return data_dict
        for key, data in data_dict.items():
            if key in self.all_fields and 'serialize' in self.all_fields[key] and self.all_fields[key]['serialize']:
                if data_dict[key]:
                    data_dict[key] = json.loads(data_dict[key])
        return data_dict

    '''
    def get_template_str():
        path = os.path.dirname(__file__)
        relpath = os.path.relpath(path)
        template_relpath = relpath + '/' + template_file
        fp = open(template_relpath, 'r')
        template_as_str = fp.read()
        return template_as_str
    '''


    def get_field_key_by_full_name(self, full_name):
        for key, data in self.their_fields.items():
            if not data['full_name']:
                continue
            if data['full_name'] == full_name:
                return key
        return False

    def get_resolution_url(self, resolution, id):
        row = self.metadata_table.get(id)
        url_column_name = self.get_resolution_url_column_name(resolution)
        return getattr(row, url_column_name)

    def get_resolution_url_column_name(self, resolution):
        return self.resolutions[resolution]['url_column_name']
        
    def get_resolution_url_column(self, resolution):
        column_name = self.get_resolution_url_column_name(resolution)
        return getattr(self.db, column_name)
        
    def get_resolution_status_column_name(self, resolution):
        return self.resolutions[resolution]['status_column_name']

    def get_resolution_too_big_column_name(self, resolution):
        return self.resolutions[resolution]['too_big_column_name']

    def get_resolution_too_big_column(self, resolution):
        column_name = self.get_resolution_too_big_column_name(resolution)
        column = getattr(self.metadata_table, column_name)
        return column
        
    def get_resolution_status_column(self, resolution):
        the_status_column_name = self.get_resolution_status_column_name(resolution)
        the_status_column = getattr(self.metadata_table, the_status_column_name)
        return the_status_column

    def get_resolution_image_url(self, id, resolution):
        metadata_url_column_name = self.resolutions[resolution]['url_column_name']
        url = getattr(self.metadata_table.get(id), metadata_url_column_name)
        return url

    def mark_img_as_not_downloaded(self, id, resolution):
        status_column_name = self.get_resolution_status_column_name(resolution)
        data = {}
        data['id'] = id
        data[status_column_name] = False
        self.store_metadata_row(data)

    def mark_img_as_too_big(self, id, resolution):
        status_column_name = self.get_resolution_too_big_column_name(resolution)
        data = {}
        data['id'] = id
        data[status_column_name] = True
        self.store_metadata_row(data)

    def mark_img_as_downloaded(self, id, resolution):
        status_column_name = self.get_resolution_status_column_name(resolution)
        data = {}
        data['id'] = id
        data[status_column_name] = True
        self.store_metadata_row(data)

    def get_next_successful_image_id(self, id):
        where1 = sqlalchemy.or_(self.metadata_table.we_couldnt_parse_it == False, self.metadata_table.we_couldnt_parse_it == None)
        where2 = self.metadata_table.id > id
        higher_id = retval = self.metadata_table.filter(where2).first()
        if not higher_id:
            return id
        retval = int(higher_id.id)
        print retval
        return retval

    def get_prev_successful_image_id(self, id):
        where1 = sqlalchemy.or_(self.metadata_table.we_couldnt_parse_it == False, self.metadata_table.we_couldnt_parse_it == None)
        where2 = self.metadata_table.id < id
        lower_id = retval = self.metadata_table.filter(where2).order_by(sqlalchemy.desc(self.metadata_table.id)).first()
        if not lower_id:
            return id
        retval = int(lower_id.id)
        print retval
        return retval

    #TODO: we probably shouldn't ever use this, since it doesn't "uncompress" the data after pulling it from the db
    def get_image_metadata(self, id):
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

    def get_is_marked_as_too_big(self, id, resolution):
        dict = self.get_image_metadata_dict(id)
        too_big_column_name = self.get_resolution_too_big_column_name(resolution)
        if dict[too_big_column_name]:
            return True
        return False
        
    #TODO: the below can be rewritten to use the above
    def get_set_images_to_dl(self,resolution):
        ## input: resolution, as a string (hires, lores, thumb)
        ## returns: list of tuples in form: (id, url)
        the_status_column = self.get_resolution_status_column(resolution)
        where = sqlalchemy.or_(the_status_column == False, the_status_column == None)
        rows_to_dl = self.metadata_table.filter(where).all()
        ids_to_dl = map(lambda row: row.id, rows_to_dl)
        metadata_url_column_name = self.get_resolution_url_column_name(resolution)
        tuples = map(lambda id: (id, getattr(self.metadata_table.get(id), metadata_url_column_name)), ids_to_dl)
        # throw away tuples that have a null value in either position
        # TODO: maybe we should throw an exception here?
        tuples = filter(lambda tuple: tuple[0] and tuple[1], tuples)
        return tuples

    def store_metadata_row(self, metadata_dict):
        if not metadata_dict.has_key('we_couldnt_parse_it'):
            metadata_dict['we_couldnt_parse_it'] = 0
        metadata_dict = self.prep_data_for_insertion(metadata_dict)
        import pprint
        pprint.pprint(metadata_dict)
        self.insert_or_update_table_row(self.metadata_table, metadata_dict)

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
            with self.db_lock:
                self.db.delete(existing_row)
                self.db.commit()
        else: 
            final_row_data_dict = new_data_dict
        with self.db_lock:
            table.insert(**final_row_data_dict)
            self.db.commit()

    def get_highest_id_in_our_db(self):
        try:
            id = int(self.metadata_table.order_by(sqlalchemy.desc(self.metadata_table.id)).first().id)
        except:
            id = 0
        return id

    def get_num_images(self):
        # yeah, the below where statement really sucks
        # i can't just filter by != True. it returns 0 results. i don't know why.
        mywhere = sqlalchemy.or_(self.metadata_table.we_couldnt_parse_it == False, self.metadata_table.we_couldnt_parse_it == None)
        return self.metadata_table.filter(mywhere).count()
