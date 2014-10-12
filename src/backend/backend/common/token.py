#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-
# Copyright (c) 2014 Asumi Kamikaze Inc.
# Licensed under the MIT License.
# Author: Alejandro M. Bernardis
# Email: alejandro (dot) bernardis (at) asumikamikaze (dot) com
# Created: 24/Sep/2014 8:30 PM

import base64
import datetime
import hashlib
import string
from random import choice

__all__ = (
    'secret_key',
    'secret_key_b64',
    'activation_key',
    'activation_key_b64',
    'token',
    'token_b64',
    'user_token',
    'user_token_b64'
)


def _string_random_choice(length=64):
    h = '%s%s%s%s' % (
        string.ascii_letters, string.digits, string.punctuation,
        datetime.datetime.utcnow().strftime('%Y%m%d%H%M%S%f'))
    return ''.join([choice(h) for _ in xrange(length)])


def secret_key(length=64):
    return _string_random_choice(length)


def secret_key_b64(length=64):
    return base64.encodestring(_string_random_choice(length))


def activation_key(username, email, length=64):
    s = '%s%s%s' % (username, email, _string_random_choice(length))
    h = hashlib.sha256()
    h.update(s.encode())
    return h.hexdigest()


def activation_key_b64(username, email, length=64):
    return base64.encodestring(activation_key(username, email, length))


def token(length=32):
    h = '%s%s' % (string.ascii_letters, string.digits)
    return ''.join([choice(h) for _ in xrange(length)])


def token_b64(length=32):
    return base64.encodestring(token(length))


def user_token(username):
    h = hashlib.sha256()
    h.update(username)
    return h.hexdigest()


def user_token_complex(username):
    h = '%s+%s' % (user_token(username), _string_random_choice())
    h = ''.join([choice(h) for _ in xrange(256)])
    return user_token(h)[:8]
