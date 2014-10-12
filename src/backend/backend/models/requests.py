#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-
# Copyright (c) 2014 Asumi Kamikaze Inc.
# Licensed under the MIT License.
# Author: Alejandro M. Bernardis
# Email: alejandro (dot) bernardis (at) asumikamikaze (dot) com
# Created: 09/Oct/2014 6:48 PM

from schematics.models import Model
from schematics.types import StringType
from tornado.web import RequestHandler


class RequestModel(Model):
    _errors = None

    def __init__(self, raw_data=None, deserialize_mapping=None, strict=True):
        data = {}
        if isinstance(raw_data, RequestHandler):
            for key in raw_data.request.arguments.keys():
                data[key] = raw_data.get_argument(key)
        super(RequestModel, self)\
            .__init__(data or None, deserialize_mapping, strict)

    def validate(self, partial=False, strict=False):
        try:
            super(RequestModel, self).validate(partial, strict)
            return True
        except Exception, e:
            self._errors = getattr(e, 'messages')
            return False

    @property
    def errors(self):
        return self._errors


class AppleStore(RequestModel):
    uuid = StringType(required=True, min_length=32, max_length=32)
    receipt = StringType(required=True)
    product_id = StringType(required=True)


class AndroidStore(RequestModel):
    signature = StringType(required=True)