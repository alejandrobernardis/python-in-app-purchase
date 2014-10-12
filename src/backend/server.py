#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-
# Copyright (c) 2014 Asumi Kamikaze Inc.
# Licensed under the MIT License.
# Author: Alejandro M. Bernardis
# Email: alejandro (dot) bernardis (at) asumikamikaze (dot) com
# Created: 23/Sep/2014 6:02 AM

import sys
import settings
from backend.common.errors import ConfigurationError
from backend.common.storage import nosql_database_connector
from backend.common.utils import import_by_path, import_module, verify_file, \
    verify_folder
from tornado.autoreload import watch as autoreload_watch, \
    start as autoreload_start
from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop
from tornado.options import define, options, parse_command_line
from tornado.web import Application, StaticFileHandler

__project_name__ = 'SME'
__project_full_name__ = 'Slot Machines, Experimental'
__project_owner__ = ('Asumi Kamikaze, inc',)
__project_author__ = 'Alejandro M. Bernardis'
__project_version__ = settings.VERSION_TUPLE
__project_created__ = (2014, 9)

define('debug', default=settings.DEBUG, type=bool)
define('track', default=settings.TRACK, type=bool)
define('port', default=settings.PORT, type=int)
define('domain', default=settings.DOMAIN, type=basestring)
define('ssl', default=settings.SSL, type=bool)
define('cdn_prefix', default=settings.CDN_PREFIX, type=basestring)
define('prefork_process', default=settings.PREFORK_PROCESS, type=int)
define('xsrf_cookie', default=settings.XSRF_COOKIE, type=bool)
define('cookie_secret', default=settings.COOKIE_SECRET, type=basestring)
define('cookie_session', default=settings.COOKIE_SESSION, type=basestring)
define('autoreload', default=settings.AUTORELOAD_ENABLED, type=bool)


class MainApplication(Application):
    def __init__(self):
        for item in settings.AUTORELOAD_FILES:
            autoreload_watch(verify_file(item, settings.ROOT_PATH))

        _handlers = []

        for item in settings.STATIC_FILES:
            verify_file(item, settings.STATIC_PATH)
            _handlers.append((item, StaticFileHandler, {
                'path': settings.STATIC_PATH
            }))

        _handler_list = list(settings.PUBLIC_HANDLERS_LIST)

        if options.port > 8999:
            _handler_list.extend(settings.PRIVATE_HANDLERS_LIST)

        if options.debug:
            _handler_list.extend(settings.HELPER_HANDLERS_LIST)

        for item in _handler_list:
            try:
                module = import_module(item)
            except ImportError as e:
                raise ConfigurationError(
                    'ImportError %s: %s' % (item, e.args[0]))
            if not hasattr(module, 'handlers_list'):
                raise ConfigurationError(
                    'Module "%s" does not define a "%s" attribute' %
                    (item, 'handlers_list'))
            _handlers.extend(getattr(module, 'handlers_list'))

        _ui_modules = {}

        for key, value in settings.UI_MODULES:
            try:
                _ui_modules[key] = import_by_path(value)
            except ImportError as e:
                raise ConfigurationError(
                    'ImportError %s, %s: %s' % (key, value, e.args[0]))

        super(MainApplication, self).__init__(_handlers, **{
            'app_name': settings.APP_NAME,
            'app_version': settings.VERSION,
            'debug': options.debug,
            'track': options.track,
            'ssl': options.ssl,
            'cdn_prefix': options.cdn_prefix,
            'xsrf_cookies': options.xsrf_cookie,
            'cookie_secret': options.cookie_secret,
            'cookie_session': options.cookie_session,
            'login_url': settings.LOGIN_URL,
            'logout_url': settings.LOGOUT_URL,
            'domain': options.domain,
            'port': options.port,
            'path': verify_folder(settings.APP_PATH),
            'root_path': settings.ROOT_PATH,
            'static_path': settings.STATIC_PATH,
            'template_path': verify_folder(settings.TEMPLATES_PATH),
            'temp_path': verify_folder(settings.TEMP_PATH),
            'ca_path': verify_folder(settings.CA_PATH),
            'locale_path': verify_folder(settings.LOCALE_PATH),
            'locale_default': settings.LOCALE_DEFAULT,
            'locale_supported': settings.LOCALE_SUPPORTED,
            'ui_modules': _ui_modules,
            'session': settings.SESSION,
            'database': settings.DATABASE,
            'email': settings.EMAIL,
            'env': settings.ENV_STATUS,
            'env_list': settings.ENV_LIST,
            'api': settings.API,
            'api_current': settings.API_CURRENT,
            'api_available': settings.API_AVAILABLE,
            'api_domain': settings.API_DOMAIN,
            'api_port': settings.API_PORT,
        })

        self._db_cache = {}

        for item in settings.DATABASE.keys():
            self.db_connector(item)

    @property
    def env_list(self):
        return settings.ENV_LIST

    @property
    def env_name(self):
        return self.env_list[self.env_value]

    @property
    def env_value(self):
        return settings.ENV_STATUS

    @property
    def db_config(self):
        value = self.settings.get('database', {})
        if not value:
            raise ConfigurationError('Database config is undefined')
        return value

    def db_connector(self, name='default'):
        if name not in self._db_cache:
            self._db_cache[name] = \
                nosql_database_connector(name, self.db_config)
        return self._db_cache[name]

    @property
    def ssl_support(self):
        return self.settings.get('ssl', False)

    @property
    def ssl_config(self):
        if not self.ssl_support:
            return None
        import ssl
        ca_path = self.settings.get('ca_path')
        return {
            'cert_reqs': ssl.CERT_REQUIRED,
            'ca_certs': verify_file('cacert.crt', ca_path),
            'certfile': verify_file('server.crt', ca_path),
            'keyfile': verify_file('server.key', ca_path)
        }


if __name__ == '__main__':
    parse_command_line()
    print 'Listening on http://%s:%s' % (options.domain, options.port)
    app = MainApplication()
    http_server = HTTPServer(app, xheaders=True, ssl_options=app.ssl_config)
    if options.prefork_process > -1:
        http_server.bind(options.port)
        http_server.start(options.prefork_process)
    else:
        http_server.listen(options.port)
    io_loop = IOLoop.instance()
    if options.autoreload:
        autoreload_start(io_loop)
    try:
        io_loop.start()
    except:
        print 'Bye, bye...'
        io_loop.stop()
        sys.exit(0)
