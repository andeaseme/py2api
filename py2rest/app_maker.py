from __future__ import division

from flask import Flask, jsonify, request
from flask_cors import CORS
from werkzeug.exceptions import InternalServerError
from platform import system as this_system

from oto.ws.ws_errors import ClientError
from oto.pj.stag.util.logging_utils import logger


def route_wrapper(route_ow, route_name=None):
    def route_func():
        try:
            return route_ow(request)
        except Exception as e:
            raise  # if _handle_error didn't raise anything specific

    if route_name is None:
        route_name = route_ow.__name__
    route_func.__name__ =  route_name
    return route_func


def mk_app(app_name, routes=None, app_config=None, cors=True):
    app = Flask(app_name)
    if app_config is None:
        app_config = {'JSON_AS_ASCII': False}
    for k, v in app_config.items():
        app.config[k] = v
    if cors:
        if cors is True:
            cors = {}
        CORS(app, **cors)

    this_logger = logger.init_logger(name=app_name, tags=[app_name, 'api'])

    @app.errorhandler(InternalServerError)
    def handle_internal_server_error(e):
        print("General error: {}".format(e))
        response = jsonify(success=False, error="InternalServerError",
                           message="Failed to perform action: {}".format(str(e)))
        response.status_code = 500
        this_logger.exception('{} InternalServerError default catch: Exception with stack trace!'.format(app_name))
        return response

    @app.errorhandler(ClientError)
    def handle_invalid_usage(error):
        response = jsonify(error.to_dict())
        response.status_code = error.status_code
        this_logger.exception('{} ClientError default catch: Exception with stack trace!'.format(app_name))
        return response

    if routes:
        app = add_routes_to_app(app, routes)

    return app


def add_routes_to_app(app, routes):
    _routes = list()
    if isinstance(routes, dict):
        for route_name, route_ow in routes.items():
            _routes.append(route_wrapper(route_ow, route_name=route_name))
        routes = _routes
    else:
        for route_ow in routes:
            _routes.append(route_wrapper(route_ow))
        routes = _routes

    for route_func in routes:
        print route_func.__name__
        app.route(route_func.__name__, methods=['GET', 'POST'])(route_func)

    return app


def dflt_run_app_kwargs():
    dflt_kwargs = dict()

    dflt_kwargs['host'] = '0.0.0.0'
    dflt_kwargs['port'] = 5003

    if this_system() == 'Linux':
        dflt_kwargs['debug'] = 0
    else:
        dflt_kwargs['debug'] = 1

    return dflt_kwargs
