#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-
# Copyright (c) 2014 Asumi Kamikaze Inc.
# Licensed under the MIT License.
# Author: Alejandro M. Bernardis
# Email: alejandro (dot) bernardis (at) asumikamikaze (dot) com
# Created: 23/Sep/2014 7:26 AM


class FormError(Exception):
    pass


class ConfigurationError(Exception):
    pass


class SchemaError(Exception):
    pass


class SessionError(Exception):
    pass
