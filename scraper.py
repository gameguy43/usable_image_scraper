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

#import libs.cdc_phil_lib as imglib
# .scraper
# .parser
# .data_storer


import config




def mkdir(dirname):
    if not os.path.isdir(dirname + "/"):
        os.makedirs(dirname + "/")

def floorify(id):
    ## mod 100 the image id numbers to make smarter folders
    floor = id - id % 100
    floored = str(floor).zfill(5)[0:3]+"XX"
    return floored

# make a scraper based on the config
def mkscraper(image_db_key):
    img_db_config = config.image_databases[image_db_key]
    data_base_dir = config.data_root_dir + img_db_config['data_subdir']

    kwargs = {}
    kwargs['imglib'] = getattr(__import__(config.img_libraries_metalib, fromlist=[img_db_config['python_lib']]),img_db_config['python_lib'])
    kwargs['thumb_dir'] = data_base_dir + config.thumb_subdir
    kwargs['lores_dir'] = data_base_dir + config.lores_subdir
    kwargs['hires_dir'] = data_base_dir + config.hires_subdir
    kwargs['html_dir'] = data_base_dir + config.html_subdir
    print kwargs

    kwargs['db'] = config.db
    kwargs['data_table_prefix'] = img_db_config['data_table_prefix']

    return Scraper(**kwargs)




class Scraper:
    # imglib is the string name of the 
    def __init__(self, imglib, thumb_dir, lores_dir, hires_dir, html_dir, db, data_table_prefix, max_daemons=config.max_daemons):
        self.imglib = imglib 
        self.thumb_dir = thumb_dir 
        self.lores_dir = lores_dir 
        self.hires_dir = hires_dir 
        self.html_dir = html_dir 

        self.db = db
        metadata_table_name = data_table_prefix + "metadata"
        hires_status_table_name = data_table_prefix + "hires_status"
        lores_status_table_name = data_table_prefix + "lores_status"
        thumb_status_table_name = data_table_prefix + "thumb_status"

        # make the table if it isn't already existent
        imglib.data_schema.Base.metadata.create_all(self.db.engine)
        #from sqlalchemy import *
        #imglib.data_schema.Base.metadata.create_all(create_engine('sqlite:///data/metadata.sqlite'))

        # then grab it with something like this:
        self.metadata_table = getattr(self.db, metadata_table_name)
        self.hires_status_table = getattr(self.db, hires_status_table_name)
        self.lores_status_table = getattr(self.db, lores_status_table_name)
        self.thumb_status_table = getattr(self.db, thumb_status_table_name)

        self.bootstrap_filestructure()

        self.max_daemons = max_daemons
        #TODO: i think that maybe i can remove this. but not sure. probs need for sqlite.
        self.db_lock = threading.RLock()

    def bootstrap_filestructure(self):
        mkdir(self.thumb_dir)    
        mkdir(self.lores_dir)    
        mkdir(self.hires_dir)    
        mkdir(self.html_dir)    

    # this is data structure bootstrapping--make the right data subdirs
    def make_directories(self, ids, root_dir):
        ## directories for image downloads
        floors = map(floorify, ids)
        # this removes duplicates
        floor_dirs = set(floors)
        # convert the floors into strings of format like 015XX
        # also, make the effing directories
        map((lambda dirname: mkdir(root_dir + '/' + dirname)), floor_dirs)

    # huge thanks to http://www.ibm.com/developerworks/aix/library/au-threadingpython/
    # this threading code is mostly from there
    class ImgDownloader(threading.Thread):
        def __init__(self, queue, root_dir, flag_table , db_lock, scraper):
            threading.Thread.__init__(self)
            self.queue = queue
            self.root_dir = root_dir
            self.flag_table = flag_table
            self.db_lock = db_lock
            self.scraper = scraper
        def run(self):
            while True:
                ## grab url/id tuple from queue
                id_url_tuple = self.queue.get()
                try:
                    print id_url_tuple
                    id = id_url_tuple[0]
                    url = id_url_tuple[1]
                    path = self.root_dir + '/' + floorify(id) + '/' + str(id).zfill(5) + url[-4:]
                    urllib.urlretrieve(url, path)
                    print "finished downloading " + url
                    id_status_dict = {'id': id, 'status': 1}
                    # signal to db that we're done downloading
                    with self.db_lock:
                        self.scraper.insert_or_update_table_row(self.flag_table, id_status_dict)
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


    def resolution_to_status_table(self,resolution):
        if resolution == 'hires':
            table = self.hires_status_table
        elif resolution == 'lores':
            table = self.lores_status_table
        elif resolution == 'thumb':
            table = self.thumb_status_table
        # TODO: actually throw an error here
        else:
            print "cmon. give me a valid resolution"
            return None
        return table

    def bootstrap_status_tables(self):
        self.bootstrap_status_table('hires')
        self.bootstrap_status_table('lores')
        self.bootstrap_status_table('thumb')

    def bootstrap_status_table(self, resolution):
        ids = map(lambda row: row.id, self.metadata_table.all())
        status_table = self.resolution_to_status_table(resolution)
        #TODO: dbug: import pdb ; pdb.set_trace()
        for id in ids:
            if not status_table.get(id):
                data = {'id': id, 'status': 0}
                self.insert_or_update_table_row(status_table, data)

    def get_set_images_to_dl(self,resolution):
        # returns tuples of (id, url)
        statuses = self.resolution_to_status_table(resolution).all()
        rows_to_dl = filter(lambda row: row.status != 1, statuses)
        ids_to_dl = map(lambda row: row.id, rows_to_dl)
        metadata_url_column_name = self.imglib.data_schema.get_metadata_url_column_name(resolution)
        tuples = map(lambda id: (id, getattr(self.metadata_table.get(id), metadata_url_column_name)), ids_to_dl)
        tuples = filter(lambda tuple: tuple[0] and tuple[1], tuples)
        return tuples

    def get_images(self, root_dir, resolution):
        # grab the status flag table
        status_table = self.resolution_to_status_table(resolution)
        ## takes: a directory global, url_to? from phil table, an image status table
        ## returns: images to folder structure and stores downloaded status table
        queue = Queue.Queue()
        # MAKE OUR THREADZZZ
        # note: they wont do anything until we put stuff in the queue
        for i in range(self.max_daemons):
            t = self.ImgDownloader(queue, root_dir, status_table, self.db_lock, self)
            t.setDaemon(True)
            t.start()

        #list of (id, url) tuples to download images from
        dl_these_tuples = self.get_set_images_to_dl(resolution)
        ids = map(lambda tuple: tuple[0], dl_these_tuples)

        # bootstrap our file structure for our download
        self.make_directories(ids, root_dir)
        map(queue.put, dl_these_tuples)

        # wait on the queue until everything has been processed
        queue.join()


    def get_all_images(self):
        self.get_images(self.thumb_dir, 'thumb')
        self.get_images(self.lores_dir, 'lores')
        self.get_images(self.hires_dir, 'hires')

    def store_raw_html(self,id, html):
        ## stores an html dump from the scraping process, just in case
        idstr = str(id).zfill(5)
        floor = id - (id%100)
        ceiling = str(floor + 100).zfill(5)
        floor = str(floor).zfill(5)
        mkdir(self.html_dir + floor + '-' + ceiling)
        fp = open(self.html_dir + floor + '-' + ceiling + '/' + idstr + '.html', 'w')
        fp.write(html)
        fp.close()

    def get_local_raw_html(self, id):
        # TODO: this function should use floorify
        # except we also need the ceiling
        idstr = str(id).zfill(5)
        floor = id - (id%100)
        ceiling = str(floor + 100).zfill(5)
        floor = str(floor).zfill(5)
        html = open(self.html_dir + '/' + floor + '-' + ceiling + '/' + idstr + '.html', 'r').read()
        return html

    def store_metadata_row(self, metadata_dict):
        self.insert_or_update_table_row(self.metadata_table, metadata_dict)
            

    #NOTE: this only works if the primary key is 'id'
    def insert_or_update_table_row(self, table, data_dict):
        existing_row = table.get(data_dict['id'])
        if existing_row:
            self.db.delete(existing_row)
            self.db.commit()
        table.insert(**data_dict)
        self.db.commit()
        
    def scrape_indeces(self, indeces, dl_images=True, from_hd=False):
        ## main glue function
        from_hd = True #TODO:DEBUG
        
        failed_indices = []
        if not from_hd:
            #TODO: i think i can cut this cookie stuff
            try:
                cookiejar = self.imglib.scraper.get_me_a_cookie()
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

        print "bootstrapping status tables..."
        self.bootstrap_status_tables()
        print "HOLY CRAP WE ARE DONE"
        if not len(failed_indices) == 0:
            print "Failed at " + str(len(failed_indices)) + " indices :"
            print failed_indices
        if dl_images:
            print "k, trying to get the images now"
            self.get_all_images()


    # run this if you update the parser in a way that should affect the whole dataset
    # this will use the local copies of the html, not the live ones on the cdc site
    # TODO: untested so far
    def re_parse_all_metadata(self):
        #TODO: truncate the current db... also, maybe back it up first?
        start_from = 1
        cdc_phil_scrape_range_from_hd(start_from, end_with)



def main():
    #TODO: this doesn't work now that the scraper is objectified
    # NOTE: if you don't set these the right way, you'll never even touch their servers
    WORK_LOCALLY = False
    GET_IMAGES = True
    #end_with = get_highest_index_at_phil()
    #end_with = 500

    # NOTE: hard-coded
    start_from = 1
    end_with = 10
    #cdc_phil_scrape_range_from_hd(start_from, end_with)
    #return
    # NOTE: end hard-coded


    # note that we re-do our most recent thing.  just in case we died halfway through it or something
    # note also that we don't download any images until we run get_all_images()
    if self.imglib.data_storer.database_is_empty():
        print "looks like the database is empty"
        start_from = 1
    else:
        start_from = self.imglib.data_storer.get_highest_index_in_our_db() + 1
    if start_from >= end_with:
        print "looks like our database is already up to date. i wont scrape anything, but i might grab some images if we need them"
    else:
        print "looks like the highest index in their db is %s, so i'll end with that" % end_with
        print "i'm about to scrape out raw dumps and grab metadata for %s - %s" % (start_from, end_with)
        if WORK_LOCALLY:
            cdc_phil_scrape_range_from_hd(start_from, end_with)
        else:
            bootstrap_filestructure()
            cdc_phil_scrape_range(start_from, end_with)
    # don't worry--this only downloads images that we don't already have marked as downloaded in our database
    if GET_IMAGES:
        get_all_images()



if __name__ == '__main__':
    main()
