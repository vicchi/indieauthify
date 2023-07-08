# pylint: disable=invalid-name
"""
Reference Data API gunicorn configuration settings
"""

import multiprocessing
import setproctitle    # pylint: disable=unused-import # noqa: F401

# Server Mechanics: https://docs.gunicorn.org/en/latest/settings.html#server-mechanics
daemon = False
pidfile = 'run/api.pid'
umask = 0o644
worker_tmp_dir = '/dev/shm'

# Server Socket: https://docs.gunicorn.org/en/latest/settings.html#server-socket
bind = ['unix:run/api.sock']

# Worker Processes: https://docs.gunicorn.org/en/latest/settings.html#worker-processes
workers = multiprocessing.cpu_count() * 2 + 1
max_requests = 10000
worker_class = 'uvicorn.workers.UvicornWorker'

# Logging: https://docs.gunicorn.org/en/stable/settings.html#logging
accesslog = '-'
errorlog = '-'
loglevel = 'info'

# Process naming: https://docs.gunicorn.org/en/stable/settings.html#process-naming
proc_name = 'indieauthify-server'
