from __future__ import absolute_import, division, print_function, unicode_literals

import logging
import requests

from amaascore.config import ENDPOINTS
from amaascore.core.interface import Interface
from amaascore.monitor.utils import json_to_item


class MonitorInterface(Interface):

    def __init__(self, logger=None):
        endpoint = ENDPOINTS.get('monitor')
        self.logger = logger or logging.getLogger(__name__)
        super(MonitorInterface, self).__init__(endpoint=endpoint)

    def new_item(self, item):
        url = self.endpoint + '/items'
        response = requests.post(url, json=item.to_interface())
        if response.ok:
            item = json_to_item(response.json())
            return item
        else:
            self.logger.error(response.text)
            response.raise_for_status()

    def resubmit_item(self, asset_manager_id, item_id):
        url = '%s/items/%s/%s' % (self.endpoint, asset_manager_id, item_id)
        response = requests.patch(url)
        if response.ok:
            item = json_to_item(response.json())
            return item
        else:
            self.logger.error(response.text)
            response.raise_for_status()

    def retrieve_item(self, asset_manager_id, item_id):
        url = '%s/items/%s/%s' % (self.endpoint, asset_manager_id, item_id)
        response = requests.get(url)
        if response.ok:
            return json_to_item(response.json())
        else:
            self.logger.error(response.text)
            response.raise_for_status()

    def close_item(self, asset_manager_id, item_id):
        url = '%s/items/%s/%s' % (self.endpoint, asset_manager_id, item_id)
        response = requests.delete(url)
        if response.ok:
            print("DO SOMETHING?")
        else:
            self.logger.error(response.text)
            response.raise_for_status()

    def search_items(self, asset_manager_ids=None, item_ids=None):
        search_params = {}
        # Potentially roll this into a loop through args rather than explicitly named - depends on additional validation
        if asset_manager_ids:
            search_params['asset_manager_ids'] = asset_manager_ids
        if item_ids:
            search_params['item_ids'] = item_ids
        url = self.endpoint + '/items'
        response = requests.get(url, params=search_params)
        if response.ok:
            items = [json_to_item(json_item) for json_item in response.json()]
            return items
        else:
            self.logger.error(response.text)
            response.raise_for_status()

    def items_by_asset_manager(self, asset_manager_id):
        url = '%s/items/%s' % (self.endpoint, asset_manager_id)
        response = requests.get(url)
        if response.ok:
            items = [json_to_item(json_item) for json_item in response.json()]
            return items
        else:
            self.logger.error(response.text)
            response.raise_for_status()
