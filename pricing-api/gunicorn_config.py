"""
Gunicorn configuration for production deployment
"""
import os

# Server socket
bind = f"0.0.0.0:{os.getenv('PORT', '5001')}"
backlog = 2048

# Worker processes
workers = 4
worker_class = 'sync'
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 50

# Timeouts - ochrona przed Slowloris
timeout = 30
graceful_timeout = 30
keepalive = 2

# Process naming
proc_name = 'pricing-api'

# Logging
accesslog = '-'
errorlog = '-'
loglevel = 'info'
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Server mechanics
daemon = False
pidfile = None
umask = 0
user = None
group = None
tmp_upload_dir = None

# SSL (jeśli używasz certyfikatów)
# keyfile = '/path/to/keyfile'
# certfile = '/path/to/certfile'
