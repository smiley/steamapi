__author__ = 'andrew'

import uuid
from .core import APIConnection


class SteamStore(object):
    def __init__(self, appid, debug=False):
        self.appid = appid
        self.interface = 'ISteamMicroTxnSandbox' if debug else 'ISteamMicroTxn'

    def get_user_microtxh_info(self, steamid):
        params = {
            'steamid': steamid,
            'appid': self.appid
        }
        return APIConnection().call(self.interface, 'GetUserInfo', 'v1', **params)

    def init_purchase(self, steamid, itemid, amount, **kwargs):
        params = {
            'steamid': steamid,
            'itemid[0]': itemid,
            'amount[0]': amount,
            'appid': self.appid,
            'orderid': uuid.uuid1().int >> 64,
            'itemcount': kwargs.get('itemcount', 1),
            'language': kwargs.get('language', 'en'),
            'currency': kwargs.get('currency', 'USD'),
            'qty[0]': kwargs.get('qty', 1),
            'description[0]': kwargs.get('description', 'Some description'),
        }
        return APIConnection().call(self.interface, 'InitTxn', 'v3', method='POST', **params)

    def query_txh(self, orderid, transid=None):
        params = {
            'appid': self.appid,
            'orderid': orderid,
        }
        return APIConnection().call(self.interface, 'QueryTxn', 'v1', **params)

    def refund_txh(self, orderid):
        params = {
            'appid': self.appid,
            'orderid': orderid
        }
        return APIConnection().call(self.interface, 'RefundTxn', 'v1', method='POST', **params)

    def finalize_txh(self, orderid):
        params = {
            'appid': self.appid,
            'orderid': orderid
        }
        return APIConnection().call(self.interface, 'FinalizeTxn', 'v1', method='POST', **params)
