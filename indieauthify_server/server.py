"""
IndieAuthify: main server module
"""

import logging
import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.logger import logger as fastapi_logger
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware

from indieauthify_server.dependencies.settings import get_settings
from indieauthify_server.routes import router

STATIC_DIR = 'static'
APP_ROOT = Path(__file__).parents[1]
STATIC_ROOT = str(APP_ROOT / STATIC_DIR)

settings = get_settings()
debug = settings.app_env.lower() != 'production'

if 'gunicorn' in os.environ.get('SERVER_SOFTWARE', ''):
    # When running with gunicorn the log handlers get suppressed instead of
    # passed along to the container manager. This forces the gunicorn handlers
    # to be used throughout the project.
    # See: https://github.com/tiangolo/uvicorn-gunicorn-fastapi-docker/issues/19#issuecomment-720720048

    gunicorn_logger = logging.getLogger('gunicorn')
    log_level = gunicorn_logger.level

    root_logger = logging.getLogger()
    gunicorn_error_logger = logging.getLogger('gunicorn.error')
    uvicorn_access_logger = logging.getLogger('uvicorn.access')

    # Use gunicorn error handlers for root, uvicorn, and fastapi loggers
    root_logger.handlers = gunicorn_error_logger.handlers
    uvicorn_access_logger.handlers = gunicorn_error_logger.handlers
    fastapi_logger.handlers = gunicorn_error_logger.handlers

    # Pass on logging levels for root, uvicorn, and fastapi loggers
    root_logger.setLevel(log_level)
    uvicorn_access_logger.setLevel(log_level)
    fastapi_logger.setLevel(log_level)

app = FastAPI(debug=debug, title='IndieAuthify')
app.add_middleware(SessionMiddleware, secret_key=settings.session_key)
app.add_middleware(ProxyHeadersMiddleware, trusted_hosts='*')
app.include_router(router)
app.mount('/static', StaticFiles(directory=STATIC_ROOT), name='static')
