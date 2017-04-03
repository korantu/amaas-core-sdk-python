# coding=utf-8
from __future__ import absolute_import, division, print_function, unicode_literals

from amaasutils.random_utils import random_string
import datetime
from decimal import Decimal
import logging.config
import random
import requests_mock
import unittest

from amaascore.config import DEFAULT_LOGGING
from amaascore.transactions.children import Comment
from amaascore.transactions.transaction import Transaction
from amaascore.transactions.interface import TransactionsInterface
from amaascore.tools.generate_asset import generate_asset
from amaascore.tools.generate_book import generate_book
from amaascore.tools.generate_transaction import generate_transaction, generate_transactions, generate_positions

logging.config.dictConfig(DEFAULT_LOGGING)


class TransactionsInterfaceTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        pass
        cls.transactions_interface = TransactionsInterface()

    def setUp(self):
        self.longMessage = True  # Print complete error message on failure
        self.maxDiff = None  # View the complete diff when there is a mismatch in a test
        self.asset_manager_id = random.randint(1, 2**31-1)
        self.asset = generate_asset(asset_manager_id=self.asset_manager_id)
        self.asset_book = generate_book(asset_manager_id=self.asset_manager_id)
        self.counterparty_book = generate_book(asset_manager_id=self.asset_manager_id)
        self.transaction = generate_transaction(asset_manager_id=self.asset_manager_id, asset_id=self.asset.asset_id,
                                                asset_book_id=self.asset_book.book_id,
                                                counterparty_book_id=self.counterparty_book.book_id)
        self.transaction_id = self.transaction.transaction_id
        self.setup_cache()

    def tearDown(self):
        pass

    def create_transaction_asset(self):
        transaction_asset_fields = ['asset_manager_id', 'asset_id', 'asset_status', 'asset_class', 'asset_type',
                                    'fungible']
        asset_json = self.asset.to_json()
        transaction_asset_json = {attr: asset_json.get(attr) for attr in transaction_asset_fields}
        self.transactions_interface.upsert_transaction_asset(transaction_asset_json=transaction_asset_json)

    def setup_cache(self):
        self.create_transaction_asset()
        self.create_transaction_book(self.asset_book)
        self.create_transaction_book(self.counterparty_book)

    def create_transaction_book(self, book):
        transaction_book_fields = ['asset_manager_id', 'book_id', 'party_id', 'book_status']
        book_json = book.to_json()
        transaction_book_json = {attr: book_json.get(attr) for attr in transaction_book_fields}
        self.transactions_interface.upsert_transaction_book(transaction_book_json=transaction_book_json)

    def test_New(self):
        self.assertIsNone(self.transaction.created_time)
        transaction = self.transactions_interface.new(self.transaction)
        # TODO - this should be populated by the New call.
        #self.assertIsNotNone(transaction.created_time)
        self.assertEqual(transaction.transaction_id, self.transaction_id)

    def test_Amend(self):
        transaction = self.transactions_interface.new(self.transaction)
        self.assertEqual(transaction.version, 1)
        new_settlement_date = transaction.settlement_date + datetime.timedelta(days=1)
        transaction.settlement_date = new_settlement_date
        transaction = self.transactions_interface.amend(transaction)
        self.assertEqual(transaction.settlement_date, new_settlement_date)
        self.assertEqual(transaction.version, 2)

    def test_Partial(self):
        self.transactions_interface.new(self.transaction)
        price = Decimal('3.14')
        updates = {'price': price}
        transaction = self.transactions_interface.partial(asset_manager_id=self.asset_manager_id,
                                                          transaction_id=self.transaction_id,
                                                          updates=updates)
        self.assertEqual(transaction.version, 2)
        self.assertEqual(transaction.price, price)

    def test_Retrieve(self):
        self.transactions_interface.new(self.transaction)
        transaction = self.transactions_interface.retrieve(self.transaction.asset_manager_id,
                                                           self.transaction.transaction_id)
        self.assertEqual(type(transaction), Transaction)

    def test_Cancel(self):
        self.transactions_interface.new(self.transaction)
        self.transactions_interface.cancel(self.transaction.asset_manager_id, self.transaction.transaction_id)
        transaction = self.transactions_interface.retrieve(self.transaction.asset_manager_id,
                                                           self.transaction.transaction_id)
        self.assertEqual(transaction.transaction_id, self.transaction_id)
        self.assertEqual(transaction.transaction_status, 'Cancelled')

    @requests_mock.Mocker()
    def test_Search(self, mocker):
        # This test is somewhat fake - but the integration tests are for the bigger picture
        endpoint = self.transactions_interface.endpoint + '/transactions'
        asset_manager_ids = [self.asset_manager_id, self.asset_manager_id+1]
        transactions = generate_transactions(asset_manager_ids=asset_manager_ids)
        mocker.get(endpoint, json=[transaction.to_json() for transaction in transactions])
        all_transactions = self.transactions_interface.search()
        self.assertEqual(all_transactions, transactions)

    @requests_mock.Mocker()
    def test_TransactionsByAssetManager(self, mocker):
        # This test is somewhat fake - but the integration tests are for the bigger picture
        endpoint = '%s/transactions/%s' % (self.transactions_interface.endpoint, self.asset_manager_id)
        asset_manager_ids = [self.asset_manager_id]
        transactions = generate_transactions(asset_manager_ids=asset_manager_ids)
        mocker.get(endpoint, json=[transaction.to_json() for transaction in transactions])
        results = self.transactions_interface.transactions_by_asset_manager(asset_manager_id=self.asset_manager_id)
        self.assertEqual(results, transactions)

    @requests_mock.Mocker()
    def test_PositionSearch(self, mocker):
        # This test is somewhat fake - but the integration tests are for the bigger picture
        endpoint = '%s/positions' % self.transactions_interface.endpoint
        asset_manager_ids = [self.asset_manager_id, self.asset_manager_id+1]
        positions = generate_positions(asset_manager_ids=asset_manager_ids)
        mocker.get(endpoint, json=[position.to_json() for position in positions])
        all_positions = self.transactions_interface.position_search()
        self.assertEqual(all_positions, positions)

    @requests_mock.Mocker()
    def test_PositionsByBook(self, mocker):
        # This test is somewhat fake - but the integration tests are for the bigger picture
        book_id = self.asset_book.book_id
        endpoint = '%s/positions/%s/%s' % (self.transactions_interface.endpoint, self.asset_manager_id, book_id)
        positions = generate_positions(asset_manager_ids=[self.asset_manager_id], book_ids=[book_id])
        mocker.get(endpoint, json=[position.to_json() for position in positions])
        results = self.transactions_interface.positions_by_asset_manager_book(asset_manager_id=self.asset_manager_id,
                                                                              book_id=book_id)
        self.assertEqual(positions, results)

    @requests_mock.Mocker()
    def test_PositionsByAssetManager(self, mocker):
        # This test is somewhat fake - but the integration tests are for the bigger picture
        endpoint = '%s/positions/%s' % (self.transactions_interface.endpoint, self.asset_manager_id)
        positions = generate_positions(asset_manager_ids=[self.asset_manager_id])
        mocker.get(endpoint, json=[position.to_json() for position in positions])
        results = self.transactions_interface.positions_by_asset_manager(asset_manager_id=self.asset_manager_id)
        self.assertEqual(positions, results)

    def test_MultipleLink(self):
        transaction = self.transactions_interface.new(self.transaction)
        links = transaction.links.get('Multiple')
        self.assertEqual(len(links), 3)  # The test script inserts 3 links
        # Add a link
        random_id = random_string(8)
        transaction.add_link('Multiple', linked_transaction_id=random_id)
        transaction = self.transactions_interface.amend(transaction)
        self.assertEqual(len(transaction.links.get('Multiple')), 4)
        transaction.remove_link('Multiple', linked_transaction_id=random_id)
        transaction = self.transactions_interface.amend(transaction)
        self.assertEqual(len(transaction.links.get('Multiple')), 3)

    def test_ChildrenPopulated(self):
        transaction = self.transactions_interface.new(self.transaction)
        retrieved_transaction = self.transactions_interface.retrieve(asset_manager_id=self.asset_manager_id,
                                                                     transaction_id=self.transaction_id)
        self.assertGreater(len(transaction.charges), 0)
        self.assertGreater(len(transaction.codes), 0)
        self.assertGreater(len(transaction.comments), 0)
        self.assertGreater(len(transaction.links), 0)
        self.assertGreater(len(transaction.parties), 0)
        self.assertGreater(len(transaction.references), 0)
        self.assertEqual(transaction.charges, retrieved_transaction.charges)
        self.assertEqual(transaction.codes, retrieved_transaction.codes)
        self.assertEqual(transaction.comments, retrieved_transaction.comments)
        self.assertEqual(transaction.links, retrieved_transaction.links)
        self.assertEqual(transaction.parties, retrieved_transaction.parties)
        self.assertEqual(transaction.references, retrieved_transaction.references)

    def test_Unicode(self):
        unicode_comment = '日本語入力'
        self.transaction.comments['Unicode'] = Comment(comment_value=unicode_comment)
        transaction = self.transactions_interface.new(self.transaction)
        self.assertEqual(transaction.comments.get('Unicode').comment_value, unicode_comment)

if __name__ == '__main__':
    unittest.main()
