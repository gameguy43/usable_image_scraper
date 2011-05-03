import unittest2 as unittest
import scraper
import config
import os

class TestScraperFunctions(unittest.TestCase):
    def setUp(self):
        self.maxDiff = None
        # instantiate a scraper 
        self.imglib_name = 'fema'
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
        known_good_indeces.sort()
        max_known_good_index = known_good_indeces.pop()
        # woops--now we're missing the last one. better put that back.
        known_good_indeces.append(max_known_good_index)

        #TODO: this is kind of just a patch for now. but maybe it's cool to leave
        # really we shouldhave separate test coverage for this
        #self.myscraper.update_download_statuses_based_on_fs(ceiling_id=max_known_good_index)

        # do a scrape on them
        self.myscraper.scrape_indeces(known_good_indeces, from_hd=True) #DEBUG TODO
        #self.myscraper.scrape_indeces(known_good_indeces, dl_images=True, from_hd=False)

        # check that we have the right number of rows in the database
        rows = self.myscraper.metadata_table.all()
        self.assertEqual(len(known_good_indeces), len(rows))

        # check that the ids in the rows are right
        all_rows = self.myscraper.metadata_table.all()
        ids = map(lambda row: row.id, all_rows)
        self.assertEqual(ids, known_good_indeces)

        # check that at least one of the rows actually has the right data
        known_metadata_mappings = self.imglib.tests.known_metadata_mappings
        for id, known_metadata_mapping in known_metadata_mappings.items():
            # this is kind of hackey, but makes sense--
            # if we didn't put the known good data through the same encoding and decoding process, we might get problems where we have a list of tuples instead of a dict, etc
            known_metadata_mapping = self.imglib.data_schema.re_objectify_data(
                self.imglib.data_schema.prep_data_for_insertion(known_metadata_mapping))
            in_db_data = self.myscraper.get_image_metadata_dict(id)
            for key, known_data in known_metadata_mapping.items():
                print key
                self.assertEqual(known_data, in_db_data[key])

        # check that all the images are marked as downloaded
        # first, do it by hand
        check_this_id = known_good_indeces[0]
        check_this_id = str(check_this_id)
        self.assertTrue(self.myscraper.get_image_metadata_dict(check_this_id)['hires_status'])

        # then do it the modular way
        for id in known_good_indeces:
            metadata = self.myscraper.get_image_metadata_dict(check_this_id)
            for resolution, resolution_info in self.myscraper.resolutions.items():
                self.assertTrue(metadata[resolution_info['status_column_name']])

        # make sure that we have the HTML and image files for each of the known good indeces
        for id in known_good_indeces:
            html_file = self.myscraper.get_local_html_file_location(id)

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

        # TODO: check that the function update_resolution_download_status_based_on_fs(self, resolution, ceiling_id=50000) works
        


#TODO: case: * grab the highest index in the database
# maybe. or just make this a test that lives in the individual image libraries

if __name__ == '__main__':
    unittest.main()
