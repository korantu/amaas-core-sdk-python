import unittest
import csv
import random

from amaasutils.random_utils import random_string
from amaascore.csv_upload.data import Uploader

class WarrantUploaderTest(unittest.TestCase):

    def setUp(self):
        self.longMessage = True  # Print complete error message on failure
        self.asset_manager_id = self.client_id = 1
        self.csvfile = 'WarrantsUploaderTest.csv'
        self.asset_ids = [random_string(8), random_string(8)]
        with open(self.csvfile, 'r+', newline='') as readfile:
            reader = csv.reader(readfile)
            for row in reader:
                header = row
                break
        with open(self.csvfile, 'w+', newline='') as writefile:
            writer = csv.writer(writefile)
            writer.writerow(header)
            writer.writerow(['Warrant', self.asset_ids[0], '123', 'Active', '123', 'USA', '123', 'USD', '01/05/09',
                            'Warrant', '123', '123', '123', '123', '1', 'E', '01/05/09', '01/05/09', '01/05/09', '123',
                            '123', '123', '123', 'C', 'C',
                            '12345', '54321', 'true', '1', 'true', '2'])
            writer.writerow(['Warrant', self.asset_ids[1], '123', 'Active', '123', 'USA', '123', 'USD', '01/05/09',
                            'Warrant', '123', '123', '123', '123', '1', 'E', '01/05/09', '01/05/09', '01/05/09', '123',
                            '123', '123', '123', 'C', 'C',
                            '12345', '54321', 'true', '1', 'true', '2'])

    def tearDown(self):
        pass

    def test_WarrantUploadDownload(self):
        Uploader().upload(asset_manager_id=self.asset_manager_id, client_id=self.client_id, csvpath=self.csvfile)
        Uploader().download(csvpath=self.csvfile, asset_manager_id=self.asset_manager_id, data_id_type='asset_id', data_id_list=self.asset_ids)

if __name__ == '__main__':
    unittest.main()