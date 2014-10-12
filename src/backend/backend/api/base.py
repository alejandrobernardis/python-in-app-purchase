#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-
# Copyright (c) 2014 Asumi Kamikaze Inc.
# Licensed under the MIT License.
# Author: Alejandro M. Bernardis
# Email: alejandro (dot) bernardis (at) asumikamikaze (dot) com
# Created: 24/Sep/2014 4:40 AM

import re
import sys
import json
import math
import datetime
from backend.common.utils import trace_error, camel_case_split, complex_types, \
    str_to_bool, domain
from backend.models.requests import RequestModel
from backend.security.sessions import SessionMixin
from backend.tasks.tasks import push__track_activity
from bson import json_util as json_mongo
from functools import wraps
from tornado.httputil import responses
from tornado.escape import json_decode
from tornado.web import RequestHandler
from wtforms_tornado.form import Form


def is_tracking_enabled(method):
    @wraps(method)
    def wrapper(self, *args, **kwargs):
        if not self.track:
            return None
        return method(self, *args, **kwargs)
    return wrapper


def verify_method(action_name, action_method):
    def decorator(method):
        @wraps(method)
        def wrapper(self, *args, **kwargs):
            if args[0] != action_name or self.request.method != action_method:
                return self._not_implemented()
            return method(self, *args, **kwargs)
        return wrapper
    return decorator


class Paginator(object):
    def __init__(self, page_number=0, page_size=50, total=0, query=None):
        self._page_number = page_number
        self._page_size = page_size
        self._total = total
        self._page_query = query

    @property
    def total(self):
        return int(self._total)

    @property
    def page_total(self):
        return int(math.ceil(self.total/float(self.page_size)))

    @property
    def page_number(self):
        return int(self._page_number)

    @property
    def page_size(self):
        return int(self._page_size)

    @property
    def page_next(self):
        if self.page_number < self.page_total:
            return self.page_number + 1
        else:
            return self.page_total

    @property
    def page_prev(self):
        if self.page_number > 1:
            return self.page_number - 1
        else:
            return 1

    @property
    def page_query(self):
        return self._page_query

    def to_object(self):
        return {
            'total': self.total,
            'pages': self.page_total,
            'query': self.page_query,
            'page': {
                'size': self.page_size,
                'number': self.page_number,
                'next': self.page_next,
                'prev': self.page_prev,
            },

        }

    def to_json(self):
        return json.dumps(self.to_object())


class BaseHandler(RequestHandler, SessionMixin):
    _form = None
    _schema = None
    _template = None
    _db_name = 'default'

    # methods

    def head(self, *args, **kwargs):
        self._not_implemented()

    def get(self, *args, **kwargs):
        self._not_implemented()

    def post(self, *args, **kwargs):
        self._not_implemented()

    def delete(self, *args, **kwargs):
        self._not_implemented()

    def patch(self, *args, **kwargs):
        self._not_implemented()

    def put(self, *args, **kwargs):
        self._not_implemented()

    def options(self, *args, **kwargs):
        self._not_implemented()

    def _not_implemented(self):
        self.get_json_error_response_and_finish(responses[404], 404)

    # time

    def now(self, time_zone=None):
        return datetime.datetime.now(time_zone)

    def now_delta(self, time_zone=None, **kwargs):
        return self.now(time_zone) + datetime.timedelta(**kwargs)

    def utc_now(self):
        return datetime.datetime.utcnow()

    def utc_now_delta(self, **kwargs):
        return self.utc_now() + datetime.timedelta(**kwargs)

    # ops

    @property
    def track(self):
        return self.settings.get('track', False)

    @property
    def debug(self):
        return self.settings.get('debug', False)

    # template & models

    @property
    def template(self):
        if not self._template:
            name = re.sub(
                r'(handler|action|controller)', '',
                self.__class__.__name__,
                flags=re.I
            )
            self._template = '%s.html' % camel_case_split(name, '/', True)
        return self._template

    @property
    def form(self):
        if not self._form or not issubclass(self._form, Form):
            raise TypeError('Invalid form, must be a WTForms')
        return self._form

    def get_form(self, form=None, without_arguments=False):
        if not form:
            form = self.form
        return form() if without_arguments else form(self.request.arguments)

    def validate_form(self, form=None):
        form = self.get_form(form, False)
        return form, form.validate()

    def render_form(self, template_name=None, **kwargs):
        if 'form' not in kwargs:
            kwargs['form'] = self.form()
        self.render(template_name, **kwargs)

    def render(self, template_name=None, **kwargs):
        if not template_name:
            template_name = self.template
        super(BaseHandler, self).render(template_name, **kwargs)

    @property
    def schema(self):
        if not self._schema or not issubclass(self._schema, RequestModel):
            raise TypeError('Invalid schema, must be a RequestModel')
        return self._schema

    def get_schema(self, schema=None, without_arguments=False, **kwargs):
        if not schema:
            schema = self.schema
        return schema() if without_arguments else schema(self, **kwargs)

    def validate_schema(self, schema=None, **kwargs):
        schema = self.get_schema(schema, False, **kwargs)
        return schema, schema.validate()

    # server

    @property
    def remote_ip(self):
        try:
            ip = self.request.headers.get('X-Real-Ip', self.request.remote_ip)
        except:
            ip = self.request.remote_ip
        return self.request.headers.get('X-Forwarded-For', ip)

    def domain(self, protocol=None):
        return domain(
            self.settings.get('domain'),
            self.settings.get('port') if self.debug else None,
            protocol
        )

    def api_domain(self, protocol=None):
        return domain(
            self.settings.get('api_domain'),
            self.settings.get('api_port') if self.debug else None,
            protocol
        )

    def validate_arguments(self, *args):
        if not args:
            args = self.request.arguments.values()
        if not args or not all(args):
            raise ValueError('Arguments (!)')

    def get_query_fields(self, fields=None):
        if fields is None:
            fields = self.get_argument(
                'fields', self.get_argument('field', None))
        if isinstance(fields, (basestring, str)) and fields:
            if fields.endswith(','):
                fields = fields[:-1]
            return fields.split(',')
        if isinstance(fields, (tuple, list)):
            return [field for field in fields
                    if isinstance(field, basestring) and field]
        return None

    def get_query_logic_low(self, available=None, enabled=None):
        def _helper(name, default):
            return str_to_bool(self.get_argument(name, default))
        return {
            'available': _helper('available', available),
            'enabled': _helper('enabled', enabled)
        }

    @property
    def root_url(self):
        return self.settings.get('site_root', '/')

    @property
    def next_url(self):
        return self.get_argument(
            'next', self.get_argument(
                'next_url', self.root_url
            )
        )

    def goto_root(self):
        self.redirect(self.root_url)

    def goto_next(self):
        self.redirect(self.next_url)

    # paginator

    def paginate(self, page_number=0, page_size=50, total=0):
        return Paginator(page_number, self.paginate_size(page_size), total)

    def paginate_size(self, size=50):
        size = int(size)
        return size if size < 200 else 200

    # database

    @property
    def db(self):
        return self.db_connector(self.db_name)

    def db_connector(self, name):
        return self.application.db_connector(name)

    @property
    def db_name(self):
        return self._db_name

    # json

    def get_json_body(self):
        try:
            return json_decode(self.request.body)
        except:
            return {}

    def json_dump(self, value, default=complex_types):
        return self.sanitize_json_dump(json.dumps(value, default=default))

    def sanitize_json_dump(self, value):
        if isinstance(value, unicode):
            value = value.encode()
        if not isinstance(value, (basestring, type(None))):
            raise TypeError('Invalid type, must be a basestring.')
        return value.replace("</", "<\\/")

    def set_header_for_json(self):
        self.set_header('Content-Type', 'application/json; charset=utf-8')

    def get_object_response(self, eid=None, message=None, response=None):
        data = {
            'error': {
                'id': eid or 0,
                'message': message or 'success'
            }
        }
        if response:
            data['response'] = response
        return data

    def get_json_response(self, response=None, **kwargs):
        self.set_header_for_json()
        kwargs['response'] = response
        return self.json_dump(self.get_object_response(**kwargs))

    def get_json_response_and_finish(self, response=None, **kwargs):
        return self.finish(self.get_json_response(response, **kwargs))

    def get_json_obj_response_and_finish(self, value):
        self.set_header_for_json()
        return self.finish(self.json_dump(value))

    def get_json_mongo_response(self, cursor, **kwargs):
        self.set_header_for_json()
        kwargs['response'] = [document for document in cursor]
        return self.sanitize_json_dump(
            json_mongo.dumps(
                self.get_object_response(**kwargs)
            )
        )

    def get_json_mongo_response_and_finish(self, cursor, **kwargs):
        return self.finish(self.get_json_mongo_response(cursor, **kwargs))

    def get_json_mongo_obj_response_and_finish(self, cursor, **kwargs):
        self.set_header_for_json()
        kwargs['response'] = [document for document in cursor]
        return self.finish(self.sanitize_json_dump(json_mongo.dumps(**kwargs)))

    def get_json_complex_response_and_finish(self, data, **kwargs):
        if hasattr(data, 'to_json'):
            self.set_header_for_json()
            response = self.get_json_response('-{data}-', **kwargs)
            data = self.sanitize_json_dump(data.to_json())
            return self.finish(response.replace('"-{data}-"', data))
        elif hasattr(data, 'to_python'):
            data = data.to_python()
        elif hasattr(data, 'to_mongo'):
            data = data.to_mongo()
        return self.get_json_response_and_finish(data, **kwargs)

    def get_json_error_response_and_finish(self, message, eid=1000):
        if not isinstance(message, basestring):
            message = getattr(message, 'message') or str(message) or 'critical'
            eid = getattr(message, 'code', eid)
        self.push_error_audit(
            message, level='error' if eid < 2000 else 'critical')
        if isinstance(message, unicode):
            message = message.encode('utf-8')
        return self.get_json_response_and_finish(
            eid=eid, message=message
        )

    def get_json_exception_response_and_finish(self, message, eid=2000):
        trace_error(self.request.arguments)
        return self.get_json_error_response_and_finish(message, eid)

    # locale

    @property
    def locale_default(self):
        return self.settings.get('locale_default')

    def get_browser_locale(self, default=None):
        return super(BaseHandler, self).get_browser_locale(
            default or self.locale_default
        )

    def get_user_locale(self):
        try:
            return self.current_user.get('lang', self.locale_default)
        except:
            return self.locale_default

    # user

    def get_current_user(self):
        try:
            return self.session.data
        except:
            return {}

    # audit

    @property
    def _session_audit_object(self):
        current_user = self.current_user
        return {
            'sid': current_user.get('sid'),
            'username': current_user.get('username'),
            'remote_ip': current_user.get('remote_ip'),
            'last_login': current_user.get('last_login'),
        } if current_user else {}

    @is_tracking_enabled
    def push_audit(self, collection, activity, message, **kwargs):
        if not activity:
            activity = self.request.path
        kwargs.setdefault('host', self.request.host)
        kwargs.setdefault('remote_ip', self.remote_ip)
        current_user = self._session_audit_object
        if current_user:
            kwargs.setdefault('sid', current_user.get('sid'))
            kwargs.setdefault('username', current_user.get('username'))
        push__track_activity.delay(collection, activity, message, **kwargs)

    @is_tracking_enabled
    def push_service_audit(self, message, activity=None, level='info',
                           **kwargs):
        self.push_audit('service.%s' % level, activity, message, **kwargs)

    @is_tracking_enabled
    def push_activity_audit(self, message, activity=None, level='info',
                            **kwargs):
        self.push_audit('activity.%s' % level, activity, message, **kwargs)

    @is_tracking_enabled
    def push_error_audit(self, message, activity=None, level='warning',
                         **kwargs):
        exc_type, exc_value, exc_traceback = sys.exc_info()
        if exc_type and exc_value:
            kwargs['exception'] = exc_type.__name__
            kwargs['file_name'] = exc_traceback.tb_frame.f_code.co_filename
            kwargs['file_line'] = exc_traceback.tb_lineno
            message = exc_value.message
        kwargs['arguments'] = self.request.arguments
        self.push_audit('exception.%s' % level, activity, message, **kwargs)
