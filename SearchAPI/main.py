"""
Actually runs the API.
Make changes to the API itself in SearchAPI/application.py
"""

import os
from mangum import Mangum
import uvicorn

from .application.application import app

# Lambda handle:
lambda_handler = Mangum(app)

# Beanstalk handle:
def run_server() -> None:
    open_to_ip = os.getenv("OPEN_TO_IP")
    open_to_port = int(os.getenv("OPEN_TO_PORT"))
    uvicorn.run(app, host=open_to_ip, port=open_to_port)

if __name__ == "__main__":
    run_server()
