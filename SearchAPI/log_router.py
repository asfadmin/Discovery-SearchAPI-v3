
from typing import Callable
import time
import logging

from fastapi import Response, Request
from fastapi.routing import APIRoute

from . import api_logger


class LoggingRoute(APIRoute):
    """
    Modify the default route to expand logging to every endpoint
    """

    old_factory = logging.getLogRecordFactory()
    request_uuid = ""

    def record_factory(self, *args, **kwargs):
        """
        Add extra info to the logger when each request hits the API.

        From: https://stackoverflow.com/a/57820456
        """
        record = self.old_factory(*args, **kwargs)
        record.uuid = self.request_uuid
        return record

    def get_route_handler(self) -> Callable:
        """
        This is called before/after every request. Mostly used
        to add logging around every endpoint.

        From: https://fastapi.tiangolo.com/advanced/custom-request-and-route/#custom-apiroute-class-in-a-router
        """
        original_route_handler = super().get_route_handler()

        async def custom_route_handler(request: Request) -> Response:
            # Grab the AWS UUID and set it for every log:
            self.request_uuid = request.scope["aws.context"].aws_request_id
            logging.setLogRecordFactory(self.record_factory)
            # Time the request itself:
            before = time.time()
            try:
                response: Response = await original_route_handler(request)
            finally:
                duration = time.time() - before
                api_logger.info(
                    "Query finished running!",
                    extra={
                        "QueryTime": duration,
                        "QueryParams": dict(request.query_params),
                        "Endpoint": request.scope['path']
                    }
                )
            response.headers["X-Response-Time"] = str(duration)
            return response

        return custom_route_handler
