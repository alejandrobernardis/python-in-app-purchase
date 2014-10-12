#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-
# Copyright (c) 2014 Asumi Kamikaze Inc.
# Licensed under the MIT License.
# Author: Alejandro M. Bernardis
# Email: alejandro (dot) bernardis (at) asumikamikaze (dot) com
# Created: 08/Oct/2014 10:22 AM

import os

BACKEND_PORT = 8000
BACKEND_API_PORT = 9000
ROOT_PATH = os.path.abspath(os.path.dirname(__file__))
LIBRARY_PATH = os.path.join(ROOT_PATH, '/Volumes/Projects/library/python/2.7')
DATA_LIB_PATH = os.path.join(ROOT_PATH, 'lib')
DATA_SRC_PATH = os.path.join(ROOT_PATH, 'src/backend')
PYTHON_PATH = '$PYTHONPATH:%s:%s:%s' \
              % (LIBRARY_PATH, DATA_LIB_PATH, DATA_SRC_PATH)

from fabric.api import *


def _start(background=False, port=BACKEND_PORT):
    with lcd(DATA_SRC_PATH):
        with shell_env(PYTHONPATH=PYTHON_PATH):
            command = 'python2.7 -m server --port=%s' % port
            if background:
                command = "nohup {0} > /tmp/backend.{1}.log 2>&1 " \
                          "& echo $! > /tmp/backend.{1}.pid" \
                          .format(command, port)
            local(command)


def _stop(port=BACKEND_PORT):
    pid = open('/tmp/backend.%s.pid' % port).read().replace('\n', '')
    local('kill -9 %s %s' % (pid, int(pid)+1))


def _tail(port=BACKEND_PORT):
    local('tail -f /tmp/backend.%s.log' % port)


@task
def start_db(port=27017, domain='127.0.0.1',
             dbpath='/Volumes/Projects/data/db/default'):
    command = '/Volumes/Projects/software/mongodb/2.6.3/bin/mongod ' \
              '--port {0} --bind_ip {1} --dbpath {2} ' \
              '--pidfilepath {2}/default.pid --logpath {2}/default.log ' \
              '--oplogSize 128 --logappend --fork --journal --smallfiles'
    local(command.format(port, domain, dbpath))


@task
def stop_db():
    local('killall mongod')


@task
def start_backend(background=False):
    _start(background)


@task
def start_backend_api(background=False):
    _start(background, BACKEND_API_PORT)


@task
def start_all():
    start_db()
    start_backend(True)
    start_backend_api(True)


@task
def stop_backend():
    _stop()


@task
def stop_backend_api():
    _stop(BACKEND_API_PORT)


@task
def stop_all():
    stop_db()
    stop_backend()
    stop_backend_api()


@task
def tail_backend():
    _tail()


@task
def tail_backend_api():
    _tail(BACKEND_API_PORT)


@task
def tail_all():
    tail_backend()
    tail_backend_api()
