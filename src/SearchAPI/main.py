"""
Actually runs the API.
Make changes to the API itself in SearchAPI/application.py
"""

import os
import uvicorn
from mangum import Mangum

from application import application

handler = Mangum(application.app)


# Beanstalk handle:
def run_server() -> None:
    """
    To run this API from EC2, or another 'server'-like environment
    """
    if not os.environ.get("OPEN_TO_IP") or not os.environ.get("OPEN_TO_PORT"):
        open_to_ip = '0.0.0.0'
        open_to_port = 8080
    else:
        open_to_ip = os.environ["OPEN_TO_IP"]
        open_to_port = int(os.environ["OPEN_TO_PORT"])

    uvicorn.run(application.app, host=open_to_ip, port=open_to_port)


if __name__ == "__main__":
    run_server()
