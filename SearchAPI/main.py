"""
Actually runs the API.
Make changes to the API itself in SearchAPI/application.py
"""

import os
from mangum import Mangum
import uvicorn

# Running as a script (python3 main.py) requires one
# Running as a module (python3 -m SearchAPI.main) requires the other
# I give up. We can get rid of this once we know which method we're using:
try:
    from application.application import app
except (ModuleNotFoundError, ImportError):
    from .application.application import app

# Lambda handle:
lambda_handler = Mangum(app)

# Beanstalk handle:
def run_server() -> None:
    if not os.environ.get("OPEN_TO_IP") or not os.environ.get("OPEN_TO_PORT"):
        raise RuntimeError("ERROR: Both env vars 'OPEN_TO_IP' and 'OPEN_TO_PORT' need to be set!")
    open_to_ip = os.environ["OPEN_TO_IP"]
    open_to_port = int(os.environ["OPEN_TO_PORT"])
    uvicorn.run(app, host=open_to_ip, port=open_to_port)

if __name__ == "__main__":
    run_server()
