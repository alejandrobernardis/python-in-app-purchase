#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-
# Copyright (c) 2014 Asumi Kamikaze Inc.
# Licensed under the MIT License.
# Author: Alejandro M. Bernardis
# Email: alejandro (dot) bernardis (at) asumikamikaze (dot) com
# Created: 23/Sep/2014 10:46 AM

import re

rx_camel_case_split = re.compile(r'((?<=[a-z0-9])[A-Z]|(?!^)[A-Z](?=[a-z]))')

rx_mongo_object_id = re.compile(r'^/?[a-f0-9]{24}/?$', re.I)

rx_username = re.compile(r'^[a-z][a-z0-9@_\-\.]+$', re.I)

rx_username_c8_to_c32 = re.compile(r'^[a-z][a-z0-9@_\.]{8,32}$', re.I)

rx_password = re.compile(r'^[a-z0-9!@#$%^&*_+=\-\.]+$', re.I)

rx_password_c8_to_c32 = re.compile(r'^[a-z0-9!@#$%^&*_+=\-\.]{8,32}$', re.I)

rx_token = rx_activation_key = re.compile(r'^/?[a-f0-9]+/?$', re.I)

rx_token_c8 = re.compile(r'^/?[a-f0-9]{8}/?$', re.I)

rx_token_c32 = rx_activation_key_c32 = re.compile(r'^/?[a-f0-9]{32}/?$', re.I)

rx_token_c64 = re.compile(r'^/?[a-f0-9]{64}/?$', re.I)

rx_token_c128 = re.compile(r'^/?[a-f0-9]{128}/?$', re.I)

rx_secret_key = re.compile(
    r'^[a-z0-9!"#$%&\'\(\)*+,\-\.\/:;<=>\?@\[\\\]^_`\{\|\}~]+$', re.I)

rx_secret_key_c8 = re.compile(
    r'^[a-z0-9!"#$%&\'\(\)*+,\-\.\/:;<=>\?@\[\\\]^_`\{\|\}~]{8}$', re.I)

rx_secret_key_c32 = re.compile(
    r'^[a-z0-9!"#$%&\'\(\)*+,\-\.\/:;<=>\?@\[\\\]^_`\{\|\}~]{32}$', re.I)

rx_secret_key_c64 = re.compile(
    r'^[a-z0-9!"#$%&\'\(\)*+,\-\.\/:;<=>\?@\[\\\]^_`\{\|\}~]{64}$', re.I)

rx_secret_key_c128 = re.compile(
    r'^[a-z0-9!"#$%&\'\(\)*+,\-\.\/:;<=>\?@\[\\\]^_`\{\|\}~]{128}$', re.I)

rx_token_b64 = rx_activation_key_b64 = rx_secret_key_b64 = \
    re.compile(r'^/?[a-z0-9%=]+/?$', re.I)

rx_sid = re.compile(
    r'(?i)(?<![a-z0-9])[0-f]{8}(?:-[0-f]{4}){3}-[0-f]{12}(?![a-z0-9])', re.I)

rx_isoformat = re.compile(
    r'^(-?(?:[1-9][0-9]*)?[0-9]{4})-(1[0-2]|0[1-9])-(3[0-1]|0[1-9]|[1-2][0-9])?'
    r'T(2[0-3]|[0-1][0-9]):([0-5][0-9]):([0-5][0-9])(\.[0-9]+)??'
    r'(Z|[+-](?:2[0-3]|[0-1][0-9]):[0-5][0-9])?$', re.I)

rx_isoformat_date = re.compile(
    r'^([0-9]{4})(?:(1[0-2]|0[1-9])|-?(1[0-2]|0[1-9])-?)?'
    r'(3[0-1]|0[1-9]|[1-2][0-9])$', re.I)

rx_isoformat_time = re.compile(
    r'^(2[0-3]|[0-1][0-9]):([0-5][0-9]):([0-5][0-9])(\.[0-9]+)??'
    r'(Z|[+-](?:2[0-3]|[0-1][0-9]):[0-5][0-9])?$', re.I)

rx_sha1_password = re.compile(r'^sha1\$(.*)\$([a-z0-9]+)$', re.I)

rx_sha256_password = re.compile(r'^sha256\$(.*)\$([a-z0-9]+)$', re.I)

rx_sha512_password = re.compile(r'^sha512\$(.*)\$([a-z0-9]+)$', re.I)
