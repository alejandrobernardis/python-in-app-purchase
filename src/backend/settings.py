#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-
# Copyright (c) 2014 Asumi Kamikaze Inc.
# Licensed under the MIT License.
# Author: Alejandro M. Bernardis
# Email: alejandro (dot) bernardis (at) asumikamikaze (dot) com
# Created: 23/Sep/2014 6:02 AM

from __future__ import unicode_literals
import os
from backend.common.utils import abspath


# Bootstrap

ROOT_PATH = os.path.abspath(os.path.dirname(__file__))


# Version

VERSION_TUPLE = (1, 0, 0, 'dev', 0)
VERSION = '.'.join([str(item) for item in VERSION_TUPLE])


# Environment

ENV_DEVELOPMENT = 0
ENV_TESTING = 1
ENV_STAGING = 2
ENV_PRODUCTION = 3
ENV_LIST = ('development', 'testing', 'staging', 'production',)
ENV_STATUS = ENV_DEVELOPMENT


# Application

APP_NAME = 'backend'
DOMAIN = 'localhost'
PORT = 8000
DEBUG = ENV_STATUS < ENV_STAGING
TRACK = ENV_STATUS > ENV_DEVELOPMENT
SSL = False
CDN_PREFIX = None
PREFORK_PROCESS = -1
XSRF_COOKIE = False
COOKIE_SECRET = None
COOKIE_SESSION = 'sid'
LOGIN_URL = '/auth/signin'
LOGOUT_URL = '/auth/signout'


# Api

API = ('natalia', 1.0,)
API_CURRENT = 1.0
API_AVAILABLE = (API,)
API_DOMAIN = 'localhost'
API_PORT = 9000


# Paths

APP_PATH = abspath(APP_NAME, ROOT_PATH)
CA_PATH = abspath('CA', APP_PATH)
STATIC_PATH = abspath('static', APP_PATH)
TEMPLATES_PATH = abspath('templates', APP_PATH)
TEMP_PATH = abspath('/tmp')


# Locale

LOCALE_PATH = abspath('locale', APP_PATH)

LOCALE_SUPPORTED = (
    ('es', 'Español'),
    ('en', 'English'),
    ('pt', 'Português')
)

LOCALE_DEFAULT = 'en'


# Autoreload

AUTORELOAD_ENABLED = True
AUTORELOAD_FILES = ()


# Static Files

STATIC_FILES = ()


# Handlers

PUBLIC_HANDLERS_LIST = (
    'backend.api.public.main',
    'backend.api.public.services',
)

PRIVATE_HANDLERS_LIST = (
    'backend.api.private.stores',
)

HELPER_HANDLERS_LIST = ()


# Modules (('ModuleName', 'ModulePath.ModuleClass'))

UI_MODULES = ()


# Storage

SESSION = {
    'engine': 'memcached',
    'servers': ('localhost:11211',),
    'expires': 60 * 10 * 100,
    'serializer': 'marshal'
}

SESSION_DATA = ()

DATABASE = {
    'default': {
        'name': 'application',
        'username': None,
        'password': None,
        'settings': {
            'host': 'localhost',
            'port': 27017,
            'max_pool_size': 250,
            'auto_start_request': True,
            'use_greenlets': ENV_STATUS > ENV_TESTING
        }
    },
    'social': {
        'name': 'social',
        'username': None,
        'password': None,
        'settings': {
            'host': 'localhost',
            'port': 27017,
            'max_pool_size': 250,
            'auto_start_request': True,
            'use_greenlets': ENV_STATUS > ENV_TESTING
        }
    },
    'tracker': {
        'name': 'tracker',
        'username': None,
        'password': None,
        'settings': {
            'host': 'localhost',
            'port': 27017,
            'max_pool_size': 250,
            'auto_start_request': True,
            'use_greenlets': ENV_STATUS > ENV_TESTING
        }
    }
}


# Email

EMAIL = {
    'from': 'In-App Purchase',
    'email': 'no-reply@domain.tld',
    'settings': {
        'host': 'smtp.gmail.com',
        'port': 587,
        'username': 'no-reply@domain.tld',
        'password': 'secret-word',
        'use_tls': True
    }
}
