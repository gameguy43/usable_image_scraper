import unittest2 as unittest
import scraper
import config
import os


class TestScraperFunctions(unittest.TestCase):
    def setUp(self):
        self.maxDiff = None
        # instantiate a scraper 
        self.imglib_name = 'cdc_phil'
        print "SETTING UP"
        self.myscraper = scraper.mkscraper(self.imglib_name, test=True)
        self.imglib = self.myscraper.imglib
        # DELETE EVERYTHING THATS ALREADY IN THE TEST DB.
        # LIKE, OMFG
        self.myscraper.clear_all_data()

        # clear out all of the data for this site (like, omfg)

    '''
    def test_db_creation(self):
        db = myscraper.get_or_create_db()
        # TODO: assert things about the database
        # has the right tables
        # insert something and then grab it out
    '''

    def scrape_known_good_indeces(self):
        # grab known good indeces
        known_good_indeces = self.imglib.tests.known_good_indeces
        known_good_indeces.sort()
        max_known_good_index = known_good_indeces.pop()
        # woops--now we're missing the last one. better put that back.
        known_good_indeces.append(max_known_good_index)

        # do a scrape on them
        #self.myscraper.scrape_indeces(known_good_indeces, dl_images=False, from_hd=True) #DEBUG TODO
        self.myscraper.scrape_indeces(known_good_indeces, dl_images=True, from_hd=False)
        

    #TODO: test the scraping from hd functionality

    def test_scrape(self):
        # grab known good indeces
        known_good_indeces = self.imglib.tests.known_good_indeces
        known_good_indeces.sort()
        max_known_good_index = known_good_indeces.pop()
        # woops--now we're missing the last one. better put that back.
        known_good_indeces.append(max_known_good_index)

        # do a scrape on them
        #self.myscraper.scrape_indeces(known_good_indeces, dl_images=False, from_hd=True) #DEBUG TODO
        self.myscraper.scrape_indeces(known_good_indeces, dl_images=True, from_hd=False)

        # check that we have the right number of rows in the database
        rows = self.myscraper.db.metadata_table.all()
        import pprint; pprint.pprint(rows)
        import pprint; pprint.pprint(known_good_indeces)
        self.assertEqual(len(known_good_indeces), len(rows))

        # check that the ids in the rows are right
        all_rows = self.myscraper.db.metadata_table.all()
        ids = map(lambda row: int(row.id), all_rows)
        self.assertEqual(set(ids), set(known_good_indeces))

        # check that at least one of the rows actually has the right data
        known_metadata_mappings = self.imglib.tests.known_metadata_mappings
        for id, known_metadata_mapping in known_metadata_mappings.items():
            # this is kind of hackey, but makes sense--
            # if we didn't put the known good data through the same encoding and decoding process, we might get problems where we have a list of tuples instead of a dict, etc
            known_metadata_mapping = self.myscraper.db.re_objectify_data(
                self.myscraper.db.prep_data_for_insertion(known_metadata_mapping))
            in_db_data = self.myscraper.db.get_image_metadata_dict(id)
            for key, known_data in known_metadata_mapping.items():
                print key
                self.assertEqual(known_data, in_db_data[key])

        # check that all the images are marked as downloaded
        # first, do it by hand
        check_this_id = known_good_indeces[0]
        check_this_id = str(check_this_id)
        self.assertTrue(self.myscraper.db.get_image_metadata_dict(check_this_id)['thumb_status'])

        # then do it the modular way
        num_statuses_checked = 0
        for id in known_good_indeces:
            metadata = self.myscraper.db.get_image_metadata_dict(check_this_id)
            for resolution, resolution_info in self.myscraper.resolutions.items():
                if not self.myscraper.db.get_is_marked_as_too_big(id, resolution):
                    num_statuses_checked+=1
                    self.assertTrue(metadata[resolution_info['status_column_name']])

        # make sure that we're at least checking a reasonable number of statuses
        self.assertGreater(num_statuses_checked, 3)

        # make sure that we have the HTML and image files for each of the known good indeces
        for id in known_good_indeces:
            html_file = self.myscraper.get_local_html_file_location(id)

            print "making sure we have " + html_file
            self.assertTrue(os.access(html_file,os.F_OK))

            for resolution in self.myscraper.resolutions:
                if not self.myscraper.db.get_is_marked_as_too_big(id, resolution):
                    extension = scraper.get_extension_from_path(self.myscraper.db.get_resolution_image_url(id, resolution))
                    remote_url = self.myscraper.db.get_resolution_image_url(id, resolution)
                    file = self.myscraper.get_resolution_local_image_location(resolution, id, remote_url)
                    print "making sure we have " + file
                    self.assertTrue(os.access(file,os.F_OK))

            #TODO: test that all the images are there too
            # (not sure how to handle)

        
        # manually check that a specific one of the rows has all the right content? maybe
        #TODO

        # TODO: check that the function update_resolution_download_status_based_on_fs(self, resolution, ceiling_id=50000) works
        
    #TODO: this test should be uncommented. However, right now it generates:
    #ArgumentError: this Column already has a table!
    def test_next_id(self):
        known_good_indeces = self.imglib.tests.known_good_indeces
        for id in known_good_indeces:
            print id
            self.assertTrue(isinstance(self.myscraper.db.get_next_successful_image_id(id), int))
            self.assertTrue(isinstance(self.myscraper.db.get_prev_successful_image_id(id), int))

        # order good indeces 
        known_good_indeces.sort()
        # we'll download good1 and good3, but not good2
        good1 = known_good_indeces[0]
        good2 = known_good_indeces[1]
        good3 = known_good_indeces[2]
        self.myscraper.scrape_indeces([good1], dl_images=True, from_hd=False)
        self.myscraper.scrape_indeces([good3], dl_images=True, from_hd=False)
        local_file_we_dont_dl = self.myscraper.get_resolution_local_image_location(self.myscraper.resolutions.keys()[0], good2)
        # touch the file we won't dl, to trick our scraper in to thinking we've downloaded it
        #open(local_file_we_dont_dl, 'a')
        self.myscraper.update_download_statuses_based_on_fs(ceiling_id=good3)
        self.assertEqual(self.myscraper.db.get_next_successful_image_id(good1), good3)
        self.assertEqual(self.myscraper.db.get_prev_successful_image_id(good3), good1)
        

    def test_update_download_statuses(self):
        #TODO
        pass

    def test_get_set_images_to_dl(self):
        self.scrape_known_good_indeces()
        resolution = self.myscraper.resolutions.keys()[0]
        known_good_indeces = self.imglib.tests.known_good_indeces
        a = known_good_indeces[0]
        b = known_good_indeces[1]
        c = known_good_indeces[2]
        self.assertNotEqual(a, b)
        self.assertNotEqual(b, c)

        a_url = self.myscraper.db.get_resolution_url(resolution, a)
        b_url = self.myscraper.db.get_resolution_url(resolution, b)
        c_url = self.myscraper.db.get_resolution_url(resolution, c)

        # mark a as downloaded, b as not downloaded, c as too big, 
        self.myscraper.db.mark_img_as_downloaded(a, resolution)
        self.myscraper.db.mark_img_as_not_downloaded(b, resolution)
        self.myscraper.db.mark_img_as_too_big(c, resolution)

        reported_images_to_dl = self.myscraper.db.get_set_images_to_dl(resolution)
        reported_images_to_dl.sort()
        # we should only want to download b
        expected_images_to_dl = [(b, b_url)]
        expected_images_to_dl.sort()
        self.assertEqual(reported_images_to_dl, expected_images_to_dl)

        not_expected_images_to_dl = [(a, a_url)]
        not_expected_images_to_dl.sort()
        self.assertNotEqual(reported_images_to_dl, not_expected_images_to_dl)

#TODO: case: * grab the highest index in the database
# maybe. or just make this a test that lives in the individual image libraries

if __name__ == '__main__':
    unittest.main(verbosity=2)
