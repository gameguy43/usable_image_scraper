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

import urllib2
import os.path
import Queue
import sys
import threading
import traceback
import db
import shutil

#import libs.cdc_phil_lib as imglib
# .scraper
# .parser
# .data_storer


import config

### General Utilites
def load_module(name):
    fp, pathname, description = imp.find_module(name)
    return imp.load_module(name, fp, pathname, description)
def mkdir(dirname):
    if not os.path.isdir(dirname + "/"):
        os.makedirs(dirname + "/")
def get_filename_base_for_id(id):
    return str(id).zfill(5)
def get_extension_from_path(path):
    basename, extension = os.path.splitext(path)
    return extension

### Utils for filesystem stuff
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

### HIGH-LEVEL FUNCTIONS
## For Automating
def nightly(dl_images=True, from_hd=False):
    scrape_all_sites(dl_images=dl_images, from_hd=from_hd)
def scrape_all_sites(dl_images=True, from_hd=False):
    image_databases = config.image_databases
    for name, data in image_databases.items():
        myscraper = mkscraper(name)
        myscraper.scrape_all(dl_images=dl_images, from_hd=from_hd)
## For Testing
def generate_test_dataset(dl_images=True, from_hd=False, to_test_db=False):
    image_databases = config.image_databases
    for name, data in image_databases.items():
        myscraper = mkscraper(name, test=to_test_db)
        indeces = myscraper.imglib.tests.known_good_indeces
        myscraper.scrape_indeces(indeces, dl_images=dl_images, from_hd=from_hd)
def drop_all_tables():
    image_databases = config.image_databases
    for name, data in image_databases.items():
        myscraper = mkscraper(name)
        myscraper.db.truncate_all_tables()
        break

# make a scraper based on the config
def mkscraper(image_db_key, test=False):
    kwargs = {}
    if test:
        data_root_dir = config.data_root_dir
        kwargs['db_url'] = config.test_db_url
    else:
        data_root_dir = config.test_data_root_dir
        kwargs['db_url'] = config.db_url

    img_db_config = config.image_databases[image_db_key]
    data_base_dir = data_root_dir + img_db_config['data_subdir']

    img_libraries_metalib = config.img_libraries_metalib
    kwargs['imglib'] = getattr(img_libraries_metalib, img_db_config['python_lib'])
    # we keep this around so that we can construct a different data path for the web
    kwargs['data_library_subdir'] = img_db_config['data_subdir']
    kwargs['data_dir'] = data_base_dir
    kwargs['html_subdir'] = config.html_subdir
    kwargs['data_table_prefix'] = img_db_config['data_table_prefix']
    kwargs['max_daemons'] = config.max_daemons
    kwargs['max_filesize'] = config.max_filesize
    kwargs['web_data_base_dir'] = config.web_data_base_dir
    kwargs['long_name'] = img_db_config['long_name']
    kwargs['homepage'] = img_db_config['homepage']
    kwargs['code_url'] = img_db_config['code_url']
    kwargs['abbrev'] = image_db_key
    kwargs['test'] = test
    return Scraper(**kwargs)




class Scraper:
    # imglib is the string name of the 
    def __init__(self, imglib, db_url, data_dir, html_subdir, data_table_prefix, data_library_subdir, max_daemons=10, max_filesize=None, web_data_base_dir=None, long_name='', homepage='', code_url='', abbrev='', test=False):
        self.imglib = imglib 
        self.resolutions = imglib.data_schema.resolutions
        self.max_daemons = max_daemons
        self.max_filesize = max_filesize
        self.long_name = long_name
        self.homepage = homepage
        self.code_url = code_url
        self.abbrev = abbrev
        self.data_dir = data_dir
        self.html_dir = data_dir + html_subdir 
        self.testing = test
        # we keep this around so that we can construct a different data path for the web
        self.data_library_subdir = data_library_subdir
        if web_data_base_dir:
            self.web_data_base_dir = web_data_base_dir + self.data_library_subdir

        metadata_table_name = data_table_prefix + "metadata"

        db_kwargs = {
            'data_schema' : self.imglib.data_schema,
            'db_url' : db_url,
            'metadata_table_name' : metadata_table_name,
            'scraper' : self,
        }
        self.db = db.DB(**db_kwargs)


    ### HIGH-LEVEL
    def scrape_all(self, dl_images=True, from_hd=False):
        floor = self.db.get_highest_id_in_our_db()
        ceiling = self.imglib.scraper.get_highest_id()
        indeces = range(floor, ceiling+1)
        self.scrape_indeces(indeces, dl_images=dl_images, from_hd=from_hd)

    # download all images that haven't already been downloaded
    # (accoding to our db, not according to the filesystem)
    def download_all_images(self):
        for resolution, resolution_data in self.resolutions.items():
            self.download_resolution_images(resolution)
    # (helper for above)
    def download_resolution_images(self, resolution):
        queue = Queue.Queue()
        # MAKE OUR THREADZZZ
        # note: they wont do anything until we put stuff in the queue
        for i in range(self.max_daemons):
            t = self.ImgDownloader(queue, resolution, self)
            t.setDaemon(True)
            t.start()

        #list of (id, url) tuples for images to download
        dl_these_tuples = self.db.get_set_images_to_dl(resolution)
        print dl_these_tuples
        ids = map(lambda tuple: tuple[0], dl_these_tuples)

        # bootstrap our file structure for our download
        root_dir = self.get_resolution_download_dir(resolution) 
        self.make_directories_if_necessary(ids, root_dir)
        map(queue.put, dl_these_tuples)
        # wait on the queue until everything has been processed
        queue.join()

    ### FILESYSTEM STUFF
    # if this gets heavy, we could move it to it's own file, like db.py
    ## READING
    def get_resolution_download_dir(self, resolution):
        return self.data_dir + self.resolutions[resolution]['subdir']
    def get_resolution_local_image_location(self, resolution, id, remote_url=None):
        extension = self.get_resolution_extension(resolution, id)
        return self.get_resolution_download_dir(resolution) + get_subdir_for_id(id) + get_filename_base_for_id(id) + extension
    def get_local_html_file_location(self, id):
        filename_base = get_filename_base_for_id(id)
        subdir = get_subdir_for_id(id)
        #TODO: let's not do this any more
        mkdir(self.html_dir + subdir)
        return self.html_dir + subdir + filename_base + '.html'
    def get_local_raw_html(self, id):
        local_html_file_location = self.get_local_html_file_location(id)
        fp = open(local_html_file_location, 'r')
        html = fp.read()
        return html

    ## WRITING
    def store_raw_html(self, id, html):
        local_html_file_location = self.get_local_html_file_location(id)
        fp = open(local_html_file_location, 'w')
        fp.write(html)
        fp.close()
    # bootstrapping: make the right data subdirs
    def make_directories_if_necessary(self, ids, root_dir):
        ## directories for image downloads
        subdirs = map(get_subdir_for_id, ids)
        # this removes duplicates
        subdirs = set(subdirs)
        # convert the floors into strings of format like 015XX
        # also, make the effing directories
        map((lambda dirname: mkdir(root_dir + dirname)), subdirs)

    ### MISC
    def get_resolution_extension(self, resolution, id):
        try:
            remote_url = self.db.get_resolution_url(resolution, id)
            extension = get_extension_from_path(remote_url)
        except:
            extension = self.resolutions[resolution]['extension']
        return extension


    # huge thanks to http://www.ibm.com/developerworks/aix/library/au-threadingpython/
    # this threading code is mostly from there
    class ImgDownloader(threading.Thread):
        def __init__(self, queue, resolution, scraper):
            threading.Thread.__init__(self)
            self.queue = queue
            self.resolution = resolution
            self.scraper = scraper
        def run(self):
            while True:
                ## grab url/id tuple from queue
                id_url_tuple = self.queue.get()
                try:
                    print id_url_tuple #TODO: make this output more useful
                    id = id_url_tuple[0]
                    url = id_url_tuple[1]
                    local_filename = self.scraper.get_resolution_local_image_location(self.resolution, id, url)
                    remote = urllib2.urlopen(url)
                    filesize = int(remote.info().getheaders("Content-Length")[0])
                    # if the file is too big
                    if (self.scraper.db.get_is_marked_as_too_big(id, self.resolution)) or (self.scraper.max_filesize and filesize > self.scraper.max_filesize):
                        print "this file is too big so i won't download it: " + local_filename


                        # signal to db that we're done downloading
                        self.scraper.db.mark_img_as_too_big(id, self.resolution)
                        print "finished marking as too big " + url
                    # if the file isn't too big
                    else:
                        #download it!
                        local = open(local_filename, 'w')
                        local.write(remote.read())
                        local.close()
                        print "finished downloading " + url
                            
                        # signal to db that we're done downloading
                        self.scraper.db.mark_img_as_downloaded(id, self.resolution)
                        print "finished marking as downloaded " + url

                    # signals to queue job is done
                    self.queue.task_done()
                except KeyboardInterrupt:
                    sys.exit(0)
                    self.queue.task_done()
                except:
                    print "ERROR: trouble dling image apparently... " + str(id)
                    traceback.print_exc()
                    self.queue.task_done()
                    continue

        
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
                    print "downloading html for " + str(current_id) + " ..."
                    html = self.imglib.scraper.scrape_out_img_page(current_id, cookiejar)
                    print "downloaded"
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
                try:
                    html = self.get_local_raw_html(current_id)
                except:
                    traceback.print_exc()
                    continue
            try:
                # 3: parse the metadata out of their html
                metadata = self.imglib.parser.parse_img_html_page(html)
                metadata = self.imglib.parser.post_processing(metadata)
            except KeyboardInterrupt:
                sys.exit(0)
            except:
                print "ERROR: couldn't parse raw html for id " + str(current_id)
                metadata = {
                        'id': current_id,
                        'we_couldnt_parse_it': True,
                        }
                self.db.store_metadata_row(metadata)
                print "we just recorded in the DB the fact that we couldn't parse this one"
                failed_indices.append(current_id)
                traceback.print_exc()
                continue
            if not metadata or metadata == {}:
                print "ERROR: we thought we parsed raw html for id " + str(current_id) + ", but we got a blank dict back"
                metadata = {
                        'id': current_id,
                        'we_couldnt_parse_it': True,
                        }
                self.db.store_metadata_row(metadata)
                print "we just recorded in the DB the fact that we couldn't parse this one"
                failed_indices.append(current_id)
                traceback.print_exc()
                continue
            try:
                self.db.store_metadata_row(metadata)
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
            self.download_all_images()



    ### CROSS-POSTING STUFF
    def upload_to_wikicommons_if_unique(self, id):
        import wikiuploader
        myuploader = wikiuploader.WikiUploader(self, testing=self.testing)
        metadata = self.db.get_image_metadata_dict(id)
        myuploader.upload_to_wikicommons_if_unique(metadata)

    #### WEB STUFF
    def set_web_vars(self, web_data_base_dir):
        self.web_data_base_dir = web_data_base_dir + self.data_library_subdir
    def get_web_resolution_local_image_location(self, resolution, id, remote_url=None):
        extension = self.get_resolution_extension(resolution, id)
        return self.web_data_base_dir + self.resolutions[resolution]['subdir'] + get_subdir_for_id(id) + get_filename_base_for_id(id) + extension
    def get_image_html_repr(self, id):
        kwargs = {
            'image_as_dict' : self.db.get_image_metadata_dict(id),
            'image_resolution_to_local_file_location_fxn' : 
                lambda resolution: self.get_web_resolution_local_image_location(resolution, id),
            }
        html = self.db.repr_as_html(**kwargs)
        return html


    ### TESTING/SETUP/ETC UTILS
    # update the download statuses in our DB based on the FS
    # useful if you accidentally kill your database
    # NOTE: this will add rows even for ids that we don't have rows for yet
    def update_download_statuses_based_on_fs(self, ceiling_id=50000):
        for resolution, res_data in self.resolutions.items():
            self.update_resolution_download_status_based_on_fs(resolution, ceiling_id)
    # helper for above
    def update_resolution_download_status_based_on_fs(self, resolution, ceiling_id=50000):
        ## go through ids and check if we have them
        # TODO: this doesn't work currently because we don't know the extension of 
        root_dir = self.get_resolution_download_dir(resolution)
        ids = range(1, ceiling_id+1)
        for id in ids:
            local_file_location = self.get_resolution_local_image_location(resolution, id)
            we_have_it = os.access(local_file_location,os.F_OK)
            if we_have_it:
                self.db.mark_img_as_downloaded(id, resolution)
            else:
                self.db.mark_img_as_not_downloaded(id, resolution)

    # download to disk the html files for these indeces
    # useful for grabbing html files to toss in to a sites's /samples
    def dl_html_for_indeces(self, indeces):
        map(self.dl_html, indeces)
    # helper for above
    def dl_html(self, id):
        html = self.imglib.scraper.scrape_out_img_page(id)
        filename = str(id) + '.html'
        fp = open(filename, 'w')
        fp.write(html)
        print  "wrote " + filename
        return True

    def clear_all_data(self):
        # clear out the mysql data
        self.db.truncate_all_tables()
        # create path to move the old data to (good to have a backup)
        if self.data_dir[-1] == '/':
            backup_data_dir = self.data_dir[0:-1] + '_old'
        else:
            backup_data_dir = self.data_dir + '_old'
        # move the data dir to a backup one
        # first, nuke the destination
        if os.path.isdir(backup_data_dir):
            shutil.rmtree(backup_data_dir)
        if os.path.isdir(self.data_dir):
            shutil.move(self.data_dir, backup_data_dir)



if __name__ == '__main__':
    do_this = 'testing'
    if do_this == 'nightly':
        dl_images = True
        from_hd = True
        nightly(dl_images, from_hd)
    elif do_this == 'testing':
        generate_test_dataset(dl_images=True, from_hd=False)
        #generate_test_dataset(dl_images=False, from_hd=True)
    elif do_this == 'update_download_statuses':
        for name, data in config.image_databases.items():
            myscraper = mkscraper(name)
            ceiling_id = myscraper.db.get_highest_id_in_our_db()
            myscraper.update_download_statuses_based_on_fs(ceiling_id)
    elif do_this == 'dl_indeces':
        name = 'fws'
        indeces = [2,1234]
        myscraper = mkscraper(name)
        myscraper.dl_html_for_indeces(indeces)
    else:
        pass

