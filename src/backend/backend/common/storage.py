#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-
# Copyright (c) 2014 Asumi Kamikaze Inc.
# Licensed under the MIT License.
# Author: Alejandro M. Bernardis
# Email: alejandro (dot) bernardis (at) asumikamikaze (dot) com
# Created: 24/Sep/2014 3:21 AM

import copy
from backend.common.errors import ConfigurationError
from backend.common.utils import purge_settings, import_module, \
    import_by_path, complex_types, deserialize_complex_types, \
    serialize_complex_types
from functools import wraps
from pymongo.common import validate
from pymongo.mongo_client import MongoClient
from pymongo.mongo_replica_set_client import MongoReplicaSetClient

__all__ = (
    'KeyValueClient',
    'KeyValueClientFactory',
    'MemcachedReaderClient',
    'MemcachedClient',
    'nosql_database_connector'
)


def is_read_only(method):
    @wraps(method)
    def wrapper(self, *args, **kwargs):
        if getattr(self, '_read_only', False):
            raise NotImplementedError('This client is read only')
        return method(self, *args, **kwargs)
    return wrapper


class KeyValueClient(object):
    def __init__(self, settings, serializer='cPickle'):
        if not isinstance(settings, dict):
            raise ConfigurationError('Settings is undefined')
        self._settings = settings
        module = self._settings.get('serializer', serializer)
        try:
            self._serializer = import_module(module)
            self._serializer_name = module.lower()
        except ImportError as e:
            raise ConfigurationError(
                'ImportError %s: %s' % (module, e.args[0]))
        if not hasattr(self.serializer, 'dumps') \
                or not hasattr(self.serializer, 'loads'):
            raise AttributeError(
                'Serializer "%s" does not define a "dumps/loads" attribute'
                % module)
        engine = self._settings.get('engine')
        if not engine:
            raise ValueError('Engine is undefined')
        try:
            self._engine = self._make_engine()
        except:
            raise ValueError('Can\'t create the engine: %s' % engine)

    @property
    def serializer(self):
        return self._serializer

    def serialize(self, value):
        if self._serializer_name == 'json':
            return self._serializer.dumps(value, default=complex_types)
        elif self._serializer_name in ('marshal', 'umsgpack'):
            value = serialize_complex_types(value)
        return self._serializer.dumps(value)

    def deserialize(self, value):
        if self._serializer_name == 'json':
            return self._serializer.loads(
                value, object_hook=deserialize_complex_types)
        elif self._serializer_name in ('marshal', 'umsgpack'):
            return deserialize_complex_types(self._serializer.loads(value))
        return self._serializer.loads(value)

    def get(self, key):
        value = self._get(key)
        return self.deserialize(value) if value else {}

    def save(self, key, value, expires=None):
        self._save(
            key, self.serialize(value),
            expires or self._settings.get('expires')
        )

    def delete(self, key):
        raise NotImplementedError()

    def _make_engine(self, *args, **kwargs):
        raise NotImplementedError()

    def _get(self, key):
        raise NotImplementedError()

    def _save(self, key, value, expires):
        raise NotImplementedError()

    def __repr__(self):
        return '<%s>' % self.__class__.__name__


class KeyValueClientFactory(object):
    @staticmethod
    def make(settings, **kwargs):
        if 'engine' not in settings:
            raise ConfigurationError('Engine is undefined')
        engine = settings.get('engine')
        if not engine:
            raise ValueError('Engine is empty')
        try:
            return getattr(
                KeyValueClientFactory,
                '_%s_client' % engine
            )(settings, **kwargs)
        except (Exception, AttributeError):
            raise ValueError('Engine "%s" is not supported' % engine)

    @staticmethod
    def _memcached_client(settings, **kwargs):
        return MemcachedClient(settings, **kwargs)

    @staticmethod
    def _memcached_reader_client(settings, **kwargs):
        return MemcachedReaderClient(settings, **kwargs)


class MemcachedClient(KeyValueClient):
    _arguments = ('servers', 'behaviors', 'binary', 'username', 'password',)

    def __init__(self, settings, serializer='pickle', read_only=False):
        if settings and 'engine' not in settings:
            settings['engine'] = 'memcached'
        self._read_only = read_only
        super(MemcachedClient, self).__init__(settings, serializer)

    def _make_engine(self, *args, **kwargs):
        path = 'pylibmc.Client'
        try:
            engine = import_by_path(path)
            return engine(**purge_settings(self._settings, self._arguments))
        except ImportError as e:
            raise ConfigurationError('ImportError %s: %s' % (path, e.args[0]))

    def _get(self, key):
        return self._engine.get(key)

    @is_read_only
    def _save(self, key, value, expires):
        self._engine.set(key, value, expires)

    @is_read_only
    def delete(self, key):
        return self._engine.delete(key)


class MemcachedReaderClient(MemcachedClient):
    def __init__(self, settings, serializer='pickle'):
        super(MemcachedReaderClient, self).__init__(settings, serializer, True)


def nosql_database_connector(name, config, include=None):
    if name not in config:
        raise ConfigurationError('Database %s not supported' % name)
    db_config = copy.deepcopy(config[name])
    db_name = db_config.get('name', 'test')
    db_settings = db_config.get('settings', {})
    for key, value in db_settings.items():
        try:
            if not include or key not in include:
                validate(key, value)
        except:
            del db_settings[key]
    if 'replicaset' not in db_settings:
        client = MongoClient(**db_settings)
    else:
        client = MongoReplicaSetClient(**db_settings)
    database = client[db_name]
    db_username = db_config.get('username', False)
    db_password = db_config.get('password', False)
    if db_username and db_password:
        database.authenticate(db_username, db_password)
    return database
