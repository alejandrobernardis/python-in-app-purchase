#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-
# Copyright (c) 2014 Asumi Kamikaze Inc.
# Licensed under the MIT License.
# Author: Alejandro M. Bernardis
# Email: alejandro (dot) bernardis (at) asumikamikaze (dot) com
# Created: 23/Sep/2014 6:08 AM

import copy
import uuid
from backend.common.errors import ConfigurationError, SessionError
from backend.common.storage import KeyValueClientFactory
from functools import wraps

__all__ = (
    'validate_session',
    'verify_session',
    'verify_not_session',
    'Session',
    'SessionMixin',
    'SESSION_NAME',
    'SESSION_EXPIRE'
)


SESSION_NAME = 'sid'
SESSION_EXPIRE = 60 * 20


def validate_has_key(method):
    @wraps(method)
    def wrapper(self, *args, **kwargs):
        if not self.has(args[0]):
            raise KeyError('Key "%s" not found' % args[0])
        return method(self, *args, **kwargs)
    return wrapper


def validate_key_type(method):
    @wraps(method)
    def wrapper(self, *args, **kwargs):
        if not isinstance(args[0], (basestring, int,)):
            raise TypeError('Invalid key, must be a basestring or integer')
        return method(self, *args, **kwargs)
    return wrapper


def validate_value_type(method):
    @wraps(method)
    def wrapper(self, *args, **kwargs):
        if not isinstance(args[0], dict):
            raise TypeError('Invalid values, must be a dictionary')
        keys = args[0].keys()
        if not keys or not all(isinstance(i, (basestring, int)) for i in keys):
            raise TypeError('Invalid key, must be a basestring or integer')
        return method(self, *args, **kwargs)
    return wrapper


def validate_session(method):
    @wraps(method)
    def wrapper(self, *args, **kwargs):
        self.session_validate()
        return method(self, *args, **kwargs)
    return wrapper


def verify_session(method):
    @wraps(method)
    def wrapper(self, *args, **kwargs):
        if not self.session_verify():
            return \
                self.get_json_error_response_and_finish('EXPIRED SESSION', -1)
        return method(self, *args, **kwargs)
    return wrapper


def verify_not_session(method):
    @wraps(method)
    def wrapper(self, *args, **kwargs):
        if self.session_verify():
            return \
                self.get_json_error_response_and_finish('ACTIVE SESSION', -2)
        return method(self, *args, **kwargs)
    return wrapper


class Session(object):
    def __init__(self, handler):
        if not handler:
            raise ConfigurationError('Handler is undefined')
        elif not hasattr(handler, 'session_id'):
            raise AttributeError(
                'Handler does not define a "session_id" attribute')
        self._handler = handler
        if 'session' not in self._handler.settings:
            raise ConfigurationError('Session is undefined')
        self._settings = copy.deepcopy(self._handler.settings.get('session'))
        if not self._settings:
            raise ConfigurationError('Settings is empty')
        self._client = KeyValueClientFactory.make(self._settings)

    @property
    def data(self):
        return self._client.get(self.sid)

    @property
    def is_empty(self):
        return not self.data

    @property
    def keys(self):
        return self.data.keys()

    @property
    def sid(self):
        return self._handler.session_id

    @property
    def time_expires(self):
        return self._settings.get('expires', SESSION_EXPIRE)

    @validate_has_key
    def get(self, key, default=None):
        return self.data.get(key, default)

    def set(self, key, value, expires=None):
        self.save({key: value}, expires)

    def update(self, values, expires=None):
        self.save(values, expires)

    @validate_has_key
    def delete(self, key, expires=None):
        data = self.data
        del data[key]
        self.save(data, expires, True)

    def expires(self, expires):
        self.save(self.data, expires, True)

    def clear(self, expires=None):
        self.save({}, expires, True)

    def revoke(self):
        self._client.delete(self.sid)

    @validate_key_type
    def has(self, key):
        return key in self.data
    __contains__ = has

    def save(self, value, expires=None, ignore_value=False):
        self.force_save(value, self.sid, expires, ignore_value)

    @validate_value_type
    def force_save(self, value, sid, expires=None, ignore_value=False):
        if not ignore_value:
            data = self.data
            data.update(copy.deepcopy(value))
            value = data
        self._client.save(sid, value, expires or self.time_expires)


class SessionMixin(object):
    def _session_maker(self):
        key = '_session'
        session = getattr(self, key, False)
        if not isinstance(session, Session):
            session = Session(self)
            setattr(self, key, session)
        return session

    @property
    def session(self):
        return self._session_maker()

    @property
    def session_id(self):
        for func in ('get_argument', 'get_secure_cookie',):
            if not hasattr(self, func):
                continue
            sid = getattr(self, func)(self.session_cookie_name)
            if not sid:
                continue
            return str(sid)
        raise SessionError('Session ID not found')

    @property
    def session_cookie_name(self):
        return getattr(self, 'settings', {}).get('cookie_session', SESSION_NAME)

    @verify_not_session
    def session_start(self, data, expires=None):
        if not isinstance(data, dict):
            for func in ('to_dict', 'to_python', 'to_object', 'to_json',):
                if not hasattr(data, func):
                    continue
                data = getattr(data, func)()
                if isinstance(data, dict):
                    break
            if not isinstance(data, dict):
                raise SessionError('Invalid session data, must be a dict.')
        sid = str(uuid.uuid4()).replace('-', '')
        self.session.force_save(data, sid, expires, True)
        if hasattr(self, 'request'):
            getattr(self, 'request').arguments['sid'] = [sid]
        return sid

    @verify_session
    def session_destroy(self):
        sid = self.session_id
        self.session.revoke()
        return sid

    def session_validate(self):
        sid = self.session_id
        if self.session.is_empty:
            raise SessionError('Session ID "%s" has expired.' % sid)
        elif self.session.get('sid') != sid:
            raise SessionError('Session ID "%s" does not match.' % sid)
        return True

    def session_verify(self):
        try:
            return self.session_validate()
        except:
            return False
