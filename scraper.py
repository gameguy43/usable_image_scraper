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

import urllib
import os.path
import Queue
import sys
import threading
import traceback
from sqlalchemy.ext.sqlsoup import SqlSoup
import sqlalchemy

#import libs.cdc_phil_lib as imglib
# .scraper
# .parser
# .data_storer


import config

def load_module(name):
    fp, pathname, description = imp.find_module(name)
    return imp.load_module(name, fp, pathname, description)

def mkdir(dirname):
    if not os.path.isdir(dirname + "/"):
        os.makedirs(dirname + "/")

def floorify(id):
    ## mod 100 the image id numbers to make smarter folders
    floor = id - id % 100
    floored = str(floor).zfill(5)[0:3]+"XX"
    return floored

def ceilingify(id):
    ## mod 100 the image id numbers to make smarter folders
    ceiling = id - id % 100 + 100
    ceilinged = str(ceiling).zfill(5)[0:3]+"XX"
    return ceilinged 

def get_subdir_for_id(id):
    return floorify(id) + '-' + ceilingify(id) + '/'

def get_filename_base_for_id(id):
    return str(id).zfill(5)

def get_extension_from_path(path):
    basename, extension = os.path.splitext(path)
    return extension

# make a scraper based on the config
def mkscraper(image_db_key):
    img_db_config = config.image_databases[image_db_key]
    data_base_dir = config.data_root_dir + img_db_config['data_subdir']

    kwargs = {}
    kwargs['imglib'] = getattr(config.img_libraries_metalib, img_db_config['python_lib'])
    kwargs['data_dir'] = data_base_dir
    kwargs['html_subdir'] = config.html_subdir

    kwargs['db_url'] = config.db_url
    kwargs['data_table_prefix'] = img_db_config['data_table_prefix']
    kwargs['max_daemons'] = config.max_daemons

    return Scraper(**kwargs)




class Scraper:
    # imglib is the string name of the 
    def __init__(self, imglib, db_url, data_dir, html_subdir, data_table_prefix, max_daemons=10):
        self.imglib = imglib 
        self.resolutions = imglib.data_schema.resolutions
        self.max_daemons = max_daemons

        self.data_dir = data_dir
        self.html_dir = data_dir + html_subdir 

        # make sure we have all the right directories set up for storing html and images
        self.bootstrap_filestructure()

        metadata_table_name = data_table_prefix + "metadata"
        '''
        hires_status_table_name = data_table_prefix + "hires_status"
        lores_status_table_name = data_table_prefix + "lores_status"
        thumb_status_table_name = data_table_prefix + "thumb_status"
        '''

        self.db = SqlSoup(db_url)
        #from sqlalchemy.orm import scoped_session, sessionmaker
        #db = SqlSoup(sql_url, session=scoped_session(sessionmaker(autoflush=False, expire_on_commit=False, autocommit=True)))

        # make the tables if they don't already exist
        imglib.data_schema.Base.metadata.create_all(self.db.engine)

        # some nice shortcuts for grabbing various tables later
        self.metadata_table = getattr(self.db, metadata_table_name)
        '''
        self.hires_status_table = getattr(self.db, hires_status_table_name)
        self.lores_status_table = getattr(self.db, lores_status_table_name)
        self.thumb_status_table = getattr(self.db, thumb_status_table_name)
        '''



        #TODO: i think that maybe i can remove this. but not sure. probs need for sqlite.
        self.db_lock = threading.RLock()

    #TODO: can we delete this?
    def bootstrap_filestructure(self):
        #TODO: replace these
        '''
        mkdir(self.thumb_dir)    
        mkdir(self.lores_dir)    
        mkdir(self.hires_dir)    
        '''
        mkdir(self.html_dir)    

    # this is data structure bootstrapping--make the right data subdirs
    def make_directories(self, ids, root_dir):
        ## directories for image downloads
        subdirs = map(get_subdir_for_id, ids)
        # this removes duplicates
        subdirs = set(subdirs)
        # convert the floors into strings of format like 015XX
        # also, make the effing directories
        map((lambda dirname: mkdir(root_dir + dirname)), subdirs)

    def get_resolution_local_image_location(self, resolution, id, remote_url=None):
        try:
            remote_url = self.get_resolution_url(resolution, id)
            extension = get_extension_from_path(remote_url)
        except:
            extension = self.resolutions[resolution]['extension']
        return self.get_resolution_download_dir(resolution) + get_subdir_for_id(id) + get_filename_base_for_id(id) + extension

    # huge thanks to http://www.ibm.com/developerworks/aix/library/au-threadingpython/
    # this threading code is mostly from there
    class ImgDownloader(threading.Thread):
        def __init__(self, queue, resolution, db_lock, scraper):
            threading.Thread.__init__(self)
            self.queue = queue
            self.resolution = resolution
            self.db_lock = db_lock
            self.scraper = scraper
        def run(self):
            while True:
                ## grab url/id tuple from queue
                id_url_tuple = self.queue.get()
                try:
                    print id_url_tuple #TODO: make this output more useful
                    id = id_url_tuple[0]
                    url = id_url_tuple[1]
                    #TODO: NOTE: this breaks if the extension is something other than 3 chars long
                    local_filename = self.scraper.get_resolution_local_image_location(self.resolution, id, url)
                    urllib.urlretrieve(url, local_filename)
                    print "finished downloading " + url
                    id_status_dict = {'id': id, 'status': 1}
                    # signal to db that we're done downloading
                    with self.db_lock:
                        self.scraper.mark_img_as_downloaded(id, self.resolution)
                        print "finished marking as downloaded" + url

                    # signals to queue job is done
                    self.queue.task_done()
                except KeyboardInterrupt:
                    sys.exit(0)
                    self.queue.task_done()
                except:
                    print "ERROR: trouble dling image apparently... " + str(id)
                    traceback.print_exc()
                    self.queue.task_done()
                    return None



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
        
    def get_resolution_status_column(self, resolution):
        the_status_column_name = self.get_resolution_status_column_name(resolution)
        the_status_column = getattr(self.metadata_table, the_status_column_name)
        return the_status_column

    def get_resolution_image_url(self, id, resolution):
        metadata_url_column_name = self.resolutions[resolution]['url_column_name']
        url = getattr(self.metadata_table.get(id), metadata_url_column_name)
        return url

    def get_resolution_download_dir(self, resolution):
        return self.data_dir + self.resolutions[resolution]['subdir']

    def mark_img_as_not_downloaded(self, id, resolution):
        status_column_name = self.get_resolution_status_column_name(resolution)
        data = {}
        data['id'] = id
        data[status_column_name] = False
        self.insert_or_update_table_row(self.metadata_table, data)

    def mark_img_as_downloaded(self, id, resolution):
        status_column_name = self.get_resolution_status_column_name(resolution)
        data = {}
        data['id'] = id
        data[status_column_name] = True
        self.insert_or_update_table_row(self.metadata_table, data)


    # TODO: make sure that we're actually defaulting the downloaded status to false, as we'd hope

    def get_image_metadata(self, id):
        return self.metadata_table.get(id)

    def get_image_metadata_dict(self, id):
        return self.metadata_table.get(id).__dict__

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

    def get_images(self, resolution):
        queue = Queue.Queue()
        # MAKE OUR THREADZZZ
        # note: they wont do anything until we put stuff in the queue
        for i in range(self.max_daemons):
            t = self.ImgDownloader(queue, resolution, self.db_lock, self)
            t.setDaemon(True)
            t.start()

        #list of (id, url) tuples to download images from
        dl_these_tuples = self.get_set_images_to_dl(resolution)
        print dl_these_tuples
        ids = map(lambda tuple: tuple[0], dl_these_tuples)

        # bootstrap our file structure for our download
        root_dir = self.get_resolution_download_dir(resolution) 
        self.make_directories(ids, root_dir)
        map(queue.put, dl_these_tuples)

        # wait on the queue until everything has been processed
        queue.join()


    def get_all_images(self):
        for resolution, resolution_data in self.resolutions.items():
            self.get_images(resolution)


    def get_local_html_file_location(self, id):
        filename_base = get_filename_base_for_id(id)
        subdir = get_subdir_for_id(id)
        #TODO: let's not do this any more
        mkdir(self.html_dir + subdir)
        return self.html_dir + subdir + filename_base + '.html'
        

    def store_raw_html(self,id, html):
        local_html_file_location = self.get_local_html_file_location(id)
        ## stores an html dump from the scraping process, just in case
        fp = open(local_html_file_location, 'w')
        fp.write(html)
        fp.close()

    def get_local_raw_html(self, id):
        local_html_file_location = self.get_local_html_file_location(id)
        fp = open(local_html_file_location, 'r')
        html = fp.read()
        return html

    def store_metadata_row(self, metadata_dict):
        self.insert_or_update_table_row(self.metadata_table, metadata_dict)

    #NOTE: this only works if the primary key is 'id'
    def insert_or_update_table_row(self, table, new_data_dict):
        # merge the new and the old into a fresh dict
        existing_row = table.get(new_data_dict['id'])
        if existing_row:
            existing_row_data_dict = existing_row.__dict__
            final_row_data_dict = existing_row_data_dict
            for key, value in new_data_dict.items():
                final_row_data_dict[key] = value

            #write over the current row contents with it
            self.db.delete(existing_row)
            self.db.commit()
        else: 
            final_row_data_dict = new_data_dict
        table.insert(**final_row_data_dict)
        self.db.commit()
        
    def scrape_indeces(self, indeces, dl_images=True, from_hd=False):
        ## main glue function
        #from_hd = True #TODO:DEBUG
        
        failed_indices = []
        if not from_hd:
            try:
                #TODO: i think i can cut this cookie stuff
                #cookiejar = self.imglib.scraper.get_me_a_cookie()
                cookiejar = None
            except KeyboardInterrupt:
                sys.exit(0)
            except:
                print "ERROR: WE COULDN'T EVEN GET A COOKIE"
                traceback.print_exc()
                return None

        for current_id in indeces:
            print "STARTING: " + str(current_id)
            if not from_hd:
                try:
                    # 1: fetching html of id, for store and parse
                    html = self.imglib.scraper.scrape_out_img_page(current_id, cookiejar)
                except KeyboardInterrupt:
                    sys.exit(0)
                except:
                    print "ERROR: couldn't scrape out html for id " + str(current_id)
                    failed_indices.append(current_id)
                    traceback.print_exc()
                    continue
                # if we got a session error page:
                #TODO: pretty sure this doesn't work any more. we won't try the id again if we get a session error page
                if self.imglib.scraper.is_session_expired_page(html):
                    times_to_try_getting_cookie = 3
                    print "SESSION error. Getting a new cookie...we'll give this " + str(times_to_try_getting_cookie) + " tries..."
                    try_num = 1
                    while try_num <= times_to_try_getting_cookie:
                        try:
                            cookiejar = get_me_a_cookie()
                        except KeyboardInterrupt:
                            sys.exit(0)
                        except:
                            print "eep, no luck. giving it another shot..."
                            try_num+=1
                            continue
                        # refreshed cookie, returning to loop
                        print "SESSION success. got a new cookie."
                        break
                # but if we didn't get a session error page
                else:
                    try:
                        # 2: write html to disk
                        self.store_raw_html(current_id, html)
                    except KeyboardInterrupt:
                        sys.exit(0)
                    except:
                        print "ERROR: couldn't store raw html for id " + str(current_id)
                        failed_indices.append(current_id)
                        traceback.print_exc()
                        continue
            # if we wanted to get the html from disk
            else:
                html = self.get_local_raw_html(current_id)
            try:
                # 3: parse the metadata out of their html
                metadata = self.imglib.parser.parse_img(html)
            except KeyboardInterrupt:
                sys.exit(0)
            except:
                print "ERROR: couldn't parse raw html for id " + str(current_id)
                metadata = {
                        'id': current_id,
                        'we_couldnt_parse_it': True,
                        }
                self.store_metadata_row(metadata)
                print "we just recorded in the DB the fact that we couldn't parse this one"
                failed_indices.append(current_id)
                traceback.print_exc()
                continue
            try:
                self.store_metadata_row(metadata)
            except KeyboardInterrupt:
                sys.exit(0)
            except:
                print "ERROR: couldn't store metadata for id " + str(current_id)
                failed_indices.append(current_id)
                traceback.print_exc()
                continue
            # These lines will only run if everthing went according to plan
            print "SUCCESS: everything went according to plan for id " + str(current_id)

        #print "bootstrapping status tables..."
        #self.bootstrap_status_tables()
        print "HOLY CRAP WE ARE DONE"
        if not len(failed_indices) == 0:
            print "Failed at " + str(len(failed_indices)) + " indices :"
            print failed_indices
        if dl_images:
            print "k, trying to get the images now"
            self.get_all_images()



    # NOTE: this will add rows even for ids that we don't have rows for yet
    def update_resolution_download_status_based_on_fs(self, resolution, ceiling_id=50000):
        ## go through ids and check if we have them
        # TODO: this doesn't work currently because we don't know the extension of 
        root_dir = self.get_resolution_download_dir(resolution)
        ids = range(1, ceiling_id+1)
        for id in ids:
            local_file_location = self.get_resolution_local_image_location(resolution, id)
            we_have_it = os.access(local_file_location,os.F_OK)
            if we_have_it:
                self.mark_img_as_downloaded(id, resolution)
            else:
                self.mark_img_as_not_downloaded(id, resolution)

    def update_download_statuses_based_on_fs(self, ceiling_id=50000):
        for resolution, res_data in self.resolutions.items():
            self.update_resolution_download_status_based_on_fs(resolution, ceiling_id)
        

    # run this if you update the parser in a way that should affect the whole dataset
    # this will use the local copies of the html, not the live ones on the cdc site
    # TODO: untested so far
    def re_parse_all_metadata(self):
        #TODO: truncate the current db... also, maybe back it up first?
        start_from = 1
        cdc_phil_scrape_range_from_hd(start_from, end_with)



def main():
    myscraper = mkscraper('cdc_phil')

    # grab known good indeces
    known_good_indeces = self.imglib.tests.known_good_indeces

    scrape_these = known_good_indeces

    # do a scrape on them
    self.myscraper.scrape_indeces(scrape_these, from_hd=True)

if __name__ == '__main__':
    main()
