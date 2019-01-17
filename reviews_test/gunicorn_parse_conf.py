import os
from multiprocessing import cpu_count

user = 'root'
group= 'root'
bind = ['0.0.0.0:8511']
chdir = os.path.abspath(os.path.dirname(__file__))
daemon = True
workers = cpu_count()
threads = cpu_count() * 2
worker_connections = 5000
worker_class = 'gevent'
forwarded_allow_ips = '*'
keepalive = 6
timeout = 30
graceful_timeout = 35
limit_request_line = 8190
limit_request_fields = 50
limit_request_field_size = 8190 
reload = True
pidfile = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'parse_pid.pid')
accesslog = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'parse_access.log')
access_log_format = '%(p)s %(h)s %(l)s %(u)s %(t)s %(r)s %(a)s %(D)s'
errorlog = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'parse_error.log')
loglevel = 'warning'
capture_output = True
