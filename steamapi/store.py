__author__ = 'andrew'

from .core import APIConnection

import uuid


class SteamIngameStore(object):
    def __init__(self, appid, debug=False):
        self.appid = appid
        self.interface = 'ISteamMicroTxnSandbox' if debug else 'ISteamMicroTxn'

    def get_user_microtxh_info(self, steamid):
        return APIConnection().call(self.interface, 'GetUserInfo',
                                    'v1', steamid=steamid, appid=self.appid)

    def init_purchase(self, steamid, itemid, amount, itemcount=1, language='en', currency='USD', qty=1,
                      description='Some description'):
        params = {
            'steamid': steamid,
            'itemid[0]': itemid,
            'amount[0]': amount,
            'appid': self.appid,
            'orderid': uuid.uuid1().int >> 64,
            'itemcount': itemcount,
            'language': language,
            'currency': currency,
            'qty[0]': qty,
            'description[0]': description,
        }
        return APIConnection().call(self.interface, 'InitTxn',
                                    'v3', method='POST', **params)

    def query_txh(self, orderid):
        return APIConnection().call(self.interface, 'QueryTxn',
                                    'v1', appid=self.appid, orderid=orderid)

    def refund_txh(self, orderid):
        return APIConnection().call(self.interface, 'RefundTxn', 'v1',
                                    method='POST', appid=self.appid, orderid=orderid)

    def finalize_txh(self, orderid):
        return APIConnection().call(self.interface, 'FinalizeTxn', 'v1', method='POST', appid=self.appid,
                                    orderid=orderid)
