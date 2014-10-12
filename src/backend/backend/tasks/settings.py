#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-
# Copyright (c) 2014 Asumi Kamikaze Inc.
# Licensed under the MIT License.
# Author: Alejandro M. Bernardis
# Email: alejandro (dot) bernardis (at) asumikamikaze (dot) com
# Created: 23/Sep/2014 6:03 AM


def log_failure(self, exc, task_id, args, kwargs, einfo):
    import logging
    logging.error("[%s] failed: %r" % (task_id, exc, ))


BROKER_URL = "amqp://celery:celery@localhost//"
CELERY_RESULT_BACKEND = "amqp"
CELERY_IMPORTS = ("backend.tasks.tasks",)
CELERY_ENABLE_UTC = True
CELERY_TASK_RESULT_EXPIRES = 60 * 60 * 24
CELERY_ANNOTATIONS = {'*': {'on_failure': log_failure, 'rate_limit': '1000/m'},}