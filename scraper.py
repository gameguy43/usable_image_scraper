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

    kwargs['db'] = data_base_dir + config.html_subdir
    kwargs['data_table_prefix'] = img_db_config['data_table_prefix']

    return Scraper(**kwargs)




class Scraper:
    # imglib is the string name of the 
    def __init__(self, imglib, thumb_dir, lores_dir, hires_dir, html_dir, db, data_table_prefix):
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

        #TODO: make the table if it isn't already existent

        # then grab it with something like this:
        self.metadata_table = getattr(db, metadata_table_name)
        self.hires_status_table = getattr(db, hires_status_table_name)
        self.lores_status_table = getattr(db, lores_status_table_name)
        self.thumb_status_table = getattr(db, thumb_status_table_name)

        self.bootstrap_filestructure()

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
    db_lock = threading.RLock()
    class ImgDownloader(threading.Thread):
        def __init__(self, queue, root_dir, flag_table_object):
            threading.Thread.__init__(self)
            self.queue = queue
            self.root_dir = root_dir
            self.flag_table_object = flag_table_object
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
                    with db_lock:
                        self.flag_table_object.insert().execute(id_status_dict)
                        print "finished marking as downloaded" + url

                    # signals to queue job is done
                    self.queue.task_done()
                except KeyboardInterrupt:
                    sys.exit(0)
                    self.queue.task_done()
                except:
                    print "ERROR: trouble dling image apparently... " + str(id)
                    print path
                    traceback.print_exc()
                    self.queue.task_done()
                    return None

    def get_images(self, root_dir, db_column_name, flag_table, flag_table_object):
        ## takes: a directory global, url_to? from phil table, an image status table
        ## returns: images to folder structure and stores downloaded status table
        queue = Queue.Queue()
        # MAKE OUR THREADZZZ
        # note: they wont do anything until we put stuff in the queue
        for i in range(MAX_DAEMONS):
            t = ImgDownloader(queue, root_dir, flag_table_object)
            t.setDaemon(True)
            t.start()

        #dict of urls to download images from
        id_dict = self.imglib.data_storer.get_dict_of_images_to_dl(db_column_name, flag_table)

        # generate list of ids from results dict
        ids = id_dict.keys()
        # bootstrap our file structure for our download
        make_directories(ids, root_dir)
        # enqueue all the results
        id_tuples = id_dict.items()
        map(queue.put, id_tuples)

        # wait on the queue until everything has been processed
        queue.join()
            

    def get_all_images(self):
        get_images(self.thumb_dir, 'url_to_thumb_img', 'thumb_status', self.imglib.data_storer.thumb_status_table)
        get_images(self.lores_dir, 'url_to_lores_img', 'lores_status', self.imglib.data_storer.lores_status_table)
        get_images(self.hires_dir, 'url_to_hires_img', 'hires_status', self.imglib.data_storer.hires_status_table)

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
        idstr = str(id).zfill(5)
        floor = id - (id%100)
        ceiling = str(floor + 100).zfill(5)
        floor = str(floor).zfill(5)
        html = open(self.html_dir + '/' + floor + '-' + ceiling + '/' + idstr + '.html', 'r').read()
        return html

    def store_metadata_row(self, metadata_dict):
        self.metadata_table.insert(**metadata_dict)

    def scrape_range_from_hd(self, start, end):
        bootstrap_filestructure()
        current_id = start
        failed_indices = []
        while current_id <= end:
            try:
                # 3: parse the metadata out of their html
                html = get_local_raw_html(current_id)
                metadata = parse_img(html)
            except KeyboardInterrupt:
                sys.exit(0)
            except:
                print "ERROR: couldn't parse raw html for id " + str(current_id)
                metadata = {
                        'id': current_id,
                        'we_couldnt_parse_it': True,
                        }
                self.imglib.data_storer.store_datum(metadata)
                print "we just recorded in the DB the fact that we couldn't parse this one"
                failed_indices.append(current_id)
                traceback.print_exc()
                current_id+=1
                continue
            try:
                self.imglib.data_storer.store_datum(metadata)
                #print metadata
            except KeyboardInterrupt:
                sys.exit(0)
            except:
                print "ERROR: couldn't store metadata for id " + str(current_id)
                failed_indices.append(current_id)
                traceback.print_exc()
                current_id+=1
                continue
            # These lines will only run if everthing went according to plan
            print "SUCCESS: everything went according to plan for id " + str(current_id)
            current_id+=1

    def scrape_indeces(self, range):
        ## main glue function
        #TODO: i think i can cut this cookie stuff
        try:
            cookiejar = self.imglib.scraper.get_me_a_cookie()
        except KeyboardInterrupt:
            sys.exit(0)
        except:
            print "ERROR: WE COULDN'T EVEN GET A COOKIE"
            traceback.print_exc()
            return None

        failed_indices = []
        for current_id in range:
            print "STARTING: " + str(current_id)
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
            # if we didn't get a session error page:
            if not self.imglib.scraper.is_session_expired_page(html):
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
                    self.imglib.data_storer.store_datum(metadata)
                    print "we just recorded in the DB the fact that we couldn't parse this one"
                    failed_indices.append(current_id)
                    traceback.print_exc()
                    continue
                try:
                    self.imglib.data_storer.store_datum(metadata)
                except KeyboardInterrupt:
                    sys.exit(0)
                except:
                    print "ERROR: couldn't store metadata for id " + str(current_id)
                    failed_indices.append(current_id)
                    traceback.print_exc()
                    continue
                # These lines will only run if everthing went according to plan
                print "SUCCESS: everything went according to plan for id " + str(current_id)
            # but if we got a session error page
            else:
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

        print "HOLY CRAP WE ARE DONE"
        if not len(failed_indices) == 0:
            print "Failed at " + str(len(failed_indices)) + " indices :"
            print failed_indices


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
