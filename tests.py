import unittest2 as unittest
import scraper
import config
import os

class TestScraperFunctions(unittest.TestCase):
    def setUp(self):
        # TODO: instantiate a database?
        # instantiate a scraper 
        self.imglib_name = 'cdc_phil'
        self.myscraper = scraper.mkscraper(self.imglib_name)
        self.imglib = self.myscraper.imglib

    '''
    def test_db_creation(self):
        db = myscraper.get_or_create_db()
        # TODO: assert things about the database
        # has the right tables
        # insert something and then grab it out
    '''

    #TODO: test the scraping from hd functionality

    def test_scrape(self):
        # grab known good indeces
        known_good_indeces = self.imglib.tests.known_good_indeces

        # do a scrape on them
        self.myscraper.scrape_indeces(known_good_indeces, from_hd=False)
        #self.myscraper.scrape_indeces(known_good_indeces, False)

        # check that we have the right number of rows in the database
        rows = self.myscraper.metadata_table.all()
        self.assertEqual(len(known_good_indeces), len(rows))

        # check that the ids in the rows are right
        all_rows = self.myscraper.metadata_table.all()
        ids = map(lambda row: row.id, all_rows)
        self.assertEqual(ids, known_good_indeces)

        # TODO: check that at least one of the rows actually has the right data

        # make sure that we have the HTML and image files for each of them
        for id in known_good_indeces:
            subdir_for_id = scraper.get_subdir_for_id(id)
            filename_base_for_id = scraper.get_filename_base_for_id(id) 

            html_file = self.myscraper.html_dir + subdir_for_id + filename_base_for_id + ".html"
            print "making sure we have " + html_file
            self.assertTrue(os.access(html_file,os.F_OK))

            for resolution in self.myscraper.resolutions:
                extension = scraper.get_extension_from_path(self.myscraper.get_resolution_image_url(id, resolution))
                remote_url = self.myscraper.get_resolution_image_url(id, resolution)
                file = self.myscraper.get_resolution_local_image_location(resolution, id, remote_url)
                print "making sure we have " + file
                self.assertTrue(os.access(file,os.F_OK))

            #TODO: test that all the images are there too
            # (not sure how to handle)

        
        
        # manually check that a specific one of the rows has all the right content? maybe
        #TODO
        


#TODO: case: * grab the highest index in the database
# maybe. or just make this a test that lives in the individual image libraries

if __name__ == '__main__':
    unittest.main()
