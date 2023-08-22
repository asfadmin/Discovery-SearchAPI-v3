
from typing import Callable
import time
import logging

from fastapi import Response, Request
from fastapi.routing import APIRoute

from . import api_logger


class LoggingRoute(APIRoute):
    """
    APRRoute's are used to preform tasks before/after every API endpoint is hit.

    This one is for logging request info for every endpoint.
    """

    old_factory = logging.getLogRecordFactory()
    aws_request_id = ""

    def record_factory(self, *args, **kwargs):
        """
        Add extra info to the logger when each request hits the API.

        From: https://stackoverflow.com/a/57820456
        """
        record = self.old_factory(*args, **kwargs)
        record.aws_request_id = self.aws_request_id
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
            self.aws_request_id = request.scope["aws.context"].aws_request_id
            logging.setLogRecordFactory(self.record_factory)
            # Time the request itself:
            before = time.time()
            try:
                response: Response = await original_route_handler(request)
            finally:
                # What to ALWAYS log:
                duration = time.time() - before
                api_logger.info(
                    "Query finished running.",
                    extra={
                        "QueryTime": duration,
                        "QueryParams": dict(request.query_params),
                        "Endpoint": request.scope['path'],
                    }
                )
            # What to log if the query was successful:
            api_logger.info(
                "Query was successful!",
                extra={
                    "media_type": response.media_type,
                }
            )
            # An example on adding headers. IDK if we actually need this one:
            response.headers["X-Response-Time"] = str(duration)
            return response

        return custom_route_handler
