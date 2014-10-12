#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-
# Copyright (c) 2014 Asumi Kamikaze Inc.
# Licensed under the MIT License.
# Author: Alejandro M. Bernardis
# Email: alejandro (dot) bernardis (at) asumikamikaze (dot) com
# Created: 23/Sep/2014 6:02 AM

from __future__ import absolute_import

# Celery Configuration

from celery import Celery
from celery.utils.log import get_task_logger

celery = Celery()
celery.config_from_object('backend.tasks.settings')
logger = get_task_logger(__name__)


# DataBase Configuration

import datetime
import settings
from backend.common.storage import nosql_database_connector

_database_cache = {}


def get_database(name='default', **kwargs):
    if name not in _database_cache:
        _database_cache[name] = \
            nosql_database_connector(name, settings.DATABASE, **kwargs)
    return _database_cache[name]


def set_logiclow(value):
    if not isinstance(value, dict):
        raise TypeError('Invalid type, must be a dictionary.')
    query = dict(
        enabled=True,
        available=True,
        created=datetime.datetime.utcnow(),
        modified=datetime.datetime.utcnow(),
    )
    query.update(value)
    return query


# Tasks Configuration

@celery.task(ignore_result=True)
def push_track_activity_store(**query):
    try:
        get_database().activity.store.insert(set_logiclow(query))
    except Exception as e:
        logger.info(
            '(e): push_track_activity_store -> %s : %s'
            % (e.message.encode('utf-8'), query)
        )


@celery.task(ignore_result=True)
def push__track_activity(*args, **kwargs):
    pass  # TODO...


# Initialize

if __name__ == '__main__':
    celery.start()

