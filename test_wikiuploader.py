import unittest2 as unittest
import wikiuploader
import scraper
import urllib


class TestWikiUploader(unittest.TestCase):
    # TODO: write a test to assert that we've found all of the metadata fields
    def setUp(self):
        site = "fema"
        self.maxDiff = None
        # instantiate a scraper 
        self.myscraper = scraper.mkscraper(site, test=True)
        self.mywikiuploader = wikiuploader.WikiUploader(self.myscraper)
    
    def test_wiki_title_builder(self):
        for id in self.myscraper.imglib.tests.known_good_indeces:
            title = self.mywikiuploader.build_title(self.myscraper.db.get_image_metadata_dict(id))
            self.assertTrue(isinstance(title, unicode))

    def test_wiki_upload(self):
        # for each known good image in our site
        for id in self.myscraper.imglib.tests.known_good_indeces:
            # upload it to wikimedia commons
            self.myscraper.upload_to_wikicommons_if_unique(id)
            # grap the url that it should have been uploaded to
            metadata = self.myscraper.db.get_image_metadata_dict(id)
            title = self.mywikiuploader.build_title(metadata)
            url = 'http://commons.wikimedia.org/wiki/File:' + title
            print url
            # grab that page
            fp = urllib.urlopen(url)
            html = fp.read()
            # make sure our tags and stuff are there
            for field, data in metadata.items():
                if field in self.myscraper.imglib.data_schema.their_fields:
                    self.assertTrue(metadata[field] in html)
            # TODO

if __name__ == '__main__':
    unittest.main(verbosity=2)
