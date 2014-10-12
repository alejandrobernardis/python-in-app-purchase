#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-
# Copyright (c) 2014 Asumi Kamikaze Inc.
# Licensed under the MIT License.
# Author: Alejandro M. Bernardis
# Email: alejandro (dot) bernardis (at) asumikamikaze (dot) com
# Created: 12/Oct/2014 3:02

import re
import json
import base64
from backend.api.base import BaseHandler
from backend.models.requests import AndroidStore, AppleStore
from backend.security.sessions import verify_session
from backend.tasks.tasks import push_track_activity_store
from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5
from Crypto.Hash import SHA
from tornado import gen
from tornado.httpclient import AsyncHTTPClient, HTTPRequest


PACKAGE_IDS = (
    "default",
)

# Environment

ANDROID_PUBLIC_KEY = '>>> HASH <<<'
ANDROID_VERIFY_KEY = RSA.importKey(base64.decodestring(ANDROID_PUBLIC_KEY))
ANDROID_PACKAGE_NAME = 'tld.domain.android'


class AndroidStoreHandler(BaseHandler):
    _schema = AndroidStore

    @verify_session
    @gen.coroutine
    def post(self, *args, **kwargs):
        schema, isvalid = self.validate_form()
        try:
            if not isvalid:
                self.get_json_error_response_and_finish(schema.errors)
            else:
                receipt = json.loads(schema.receipt)
                package_name = receipt.get('packageName')
                if package_name != ANDROID_PACKAGE_NAME:
                    raise ValueError('Package Name (x)')
                product_id = receipt.get('productId')
                if schema.product_id != product_id \
                        or product_id not in PACKAGE_IDS:
                    raise ValueError('Product ID (x)')
                transaction_id = receipt.get('orderId')
                if not transaction_id:
                    raise ValueError('Transaction ID (?)')
                track = self.db['activity.store']
                track_find_one = \
                    yield track.find_one({'transaction_id': transaction_id})
                if track and track_find_one:
                    raise ValueError('Transaction ID (x)')
                h = SHA.new(receipt)
                verifier = PKCS1_v1_5.new(ANDROID_VERIFY_KEY)
                signature = schema.signature
                signature_decode = base64.decodestring(signature)
                if not verifier.verify(h, signature_decode):
                    raise ValueError('Transaction (x)')
                try:
                    if self.settings.get('track', False):
                        push_track_activity_store(
                            activity='android_store_succes',
                            uuid=schema.uuid,
                            receipt=schema.receipt,
                            signature=schema.signature,
                            product_id=schema.product_id,
                            transaction_id=transaction_id
                        )
                except Exception:
                    pass
                self.get_json_response_and_finish()
        except Exception as e:
            if self.settings.get('track', False):
                push_track_activity_store(
                    activity='android_store_error',
                    uuid=schema.uuid,
                    receipt=schema.receipt,
                    signature=schema.signature,
                    product_id=schema.product_id,
                    error=e.message.encode('utf-8')
                )
            self.get_json_exception_response_and_finish(e.message)


APPLE_URL_LIVE = 'https://buy.itunes.apple.com/verifyReceipt'
APPLE_URL_SANDBOX = 'https://sandbox.itunes.apple.com/verifyReceipt'
APPLE_PACKAGE_NAME = 'tld.domain.ios'
APPLE_ENVIRONMENT = re.compile(r'sandbox', re.I)
APPLE_SANITIZE = re.compile(r'("[^"]*")\s*=\s*("[^"]*");')
APPLE_SANITIZE_COMMA = re.compile(r',(\s*})')

APPLE_ERROR = {
    21000: 'The App Store could not read the JSON object you provided.',
    21002: 'The data in the receipt-data property was malformed.',
    21003: 'The receipt could not be authenticated.',
    21004: 'The shared secret you provided does not match the shared secret '
           'on file for your account.',
    21005: 'The receipt server is not currently available.',
    21006: 'This receipt is valid but the subscription has expired. When this '
           'status code is returned to your server, the receipt data is also '
           'decoded and returned as part of the response.',
    21007: 'This receipt is a sandbox receipt, but it was sent to the '
           'production service for verification.',
    21008: 'This receipt is a production receipt, but it was sent to the '
           'sandbox service for verification.',
}


def apple_json_sanitize(value):
    return json.loads(
        APPLE_SANITIZE_COMMA.sub(
            r'\1', APPLE_SANITIZE.sub(
                r'\1: \2,', value
            )
        )
    )


class AppleStoreHandler(BaseHandler):
    _schema = AppleStore
    _client = AsyncHTTPClient()

    @verify_session
    @gen.coroutine
    def post(self, *args, **kwargs):
        schema, isvalid = self.validate_form()
        try:
            if not isvalid:
                self.get_json_error_response_and_finish(schema.errors)
            else:
                receipt = apple_json_sanitize(schema.receipt)
                purchase_info = base64.b64decode(receipt.get('purchase-info'))
                package_name = purchase_info.get('bid')
                if package_name != APPLE_PACKAGE_NAME:
                    raise ValueError('Package Name (x)')
                product_id = purchase_info.get('product-id')
                if schema.product_id != product_id \
                        or product_id not in PACKAGE_IDS:
                    raise ValueError('Product ID (x)')
                transaction_id = purchase_info.get('transaction-id')
                track = self.db['activity.store']
                track_find_one = \
                    track.find_one({'transaction_id': transaction_id})
                if track and track_find_one:
                    raise ValueError('Transaction ID (x)')
                sandbox = APPLE_ENVIRONMENT.search(receipt.get('environment'))
                if sandbox:
                    url = APPLE_URL_SANDBOX
                else:
                    url = APPLE_URL_LIVE
                _req = HTTPRequest(url)
                _req.method = 'POST'
                _req.headers = {'Content-Type': 'text/json; charset=utf-8'}
                _req.body = \
                    json.dumps({'receipt-data': base64.b64encode(receipt)})
                _task = yield gen.Task(self._client.fetch, _req)
                _response = json.loads(_task.body)
                status = _response.get('status')
                if status and status in APPLE_ERROR:
                    raise Exception(
                        '(%s) %s' % (status, APPLE_ERROR.get(status)))
                verify = _response.get('receipt')
                if verify.get('error'):
                    raise ValueError(verify['error'].get('message'))
                elif verify.get('bid') != APPLE_PACKAGE_NAME:
                    raise ValueError('Package Name (x)')
                elif verify.get('product_id') != product_id:
                    raise ValueError('Product ID (x)')
                elif verify.get('transaction_id') != transaction_id:
                    raise ValueError('Transaction ID (x)')
                try:
                    if self.settings.get('track', False):
                        push_track_activity_store(
                            activity='apple_store_success',
                            uuid=schema.uuid,
                            receipt=schema.receipt,
                            product_id=schema.product_id,
                            transaction_id=transaction_id,
                            sandbox=sandbox,
                            **verify
                        )
                except Exception:
                    pass
                self.get_json_response_and_finish(response={
                    'sandbox': sandbox
                })
        except Exception as e:
            if self.settings.get('track', False):
                push_track_activity_store(
                    activity='apple_store_error',
                    uuid=schema.uuid,
                    receipt=schema.receipt,
                    product_id=schema.product_id,
                    error=e.message.encode('utf-8')
                )
            self.get_json_exception_response_and_finish(e.message)


handlers_list = [
    (r'/s/store/android/(?P<sid>[a-z0-9]+)/?', AndroidStoreHandler),
    (r'/s/store/ios/(?P<sid>[a-z0-9]+)/?', AppleStoreHandler),
]