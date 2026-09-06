# Note: Needs to be in this directory for the proper asgi import

# ==============================================================================
# Logging Setup
# ==============================================================================

import logging
import os
import sys

root = logging.getLogger()
root.setLevel(logging.DEBUG)
ch = logging.StreamHandler(sys.stdout)
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
root.addHandler(ch)

# ==============================================================================
# Daphne Setup
# ==============================================================================

import asgi  # noqa: E402
from daphne.endpoints import build_endpoint_description_strings  # noqa: E402
from daphne.server import Server  # noqa: E402

# Docker/Heroku environments use NGINX and must bind to a socket; others bind to address
if 'USING_NGINX' in os.environ and bool(int(os.environ['USING_NGINX'])):
    root.info('TC_DEPLOY: Initialising Daphne with NGINX')
    Server(
        application=asgi.application,
        endpoints=build_endpoint_description_strings(
            unix_socket="/tmp/asgi.socket",
        ),
        ping_interval=15,
        ping_timeout=30,
        websocket_timeout=10800,  # 3 hours maximum length
        websocket_connect_timeout=10,
        application_close_timeout=10,
        verbosity=2,
        proxy_forwarded_address_header="X-Forwarded-For",
        proxy_forwarded_port_header="X-Forwarded-Port",
        proxy_forwarded_proto_header="X-Forwarded-Proto",
    ).run()
else:
    # Render (and other hosts) inject PORT via env var. Fall back to 10000.
    port = os.environ.get('PORT', '10000')
    root.info('TC_DEPLOY: Initialising Daphne on 0.0.0.0:%s', port)
    Server(
        application=asgi.application,
        endpoints=build_endpoint_description_strings(
            host="0.0.0.0",
            port=port,
        ),
        ping_interval=15,
        ping_timeout=30,
        websocket_timeout=10800,  # 3 hours maximum length
        websocket_connect_timeout=10,
        application_close_timeout=10,
        verbosity=2,
        proxy_forwarded_address_header="X-Forwarded-For",
        proxy_forwarded_port_header="X-Forwarded-Port",
        proxy_forwarded_proto_header="X-Forwarded-Proto",
    ).run()

