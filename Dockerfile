FROM public.ecr.aws/docker/library/python:3.12
COPY --from=public.ecr.aws/awsguru/aws-lambda-adapter:0.8.3 /lambda-adapter /opt/extensions/lambda-adapter
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

ARG MATURITY="local"
ENV MATURITY=${MATURITY}
ARG HOST=0.0.0.0
ENV HOST=${HOST}
ARG PORT=8080
ENV PORT=${PORT}

RUN apt update
RUN apt clean
RUN rm -rf /var/lib/apt/lists/*

# Install the function's dependencies using file requirements.txt
COPY requirements.txt .
RUN uv pip install --system --no-cache-dir --upgrade -r ./requirements.txt

COPY ./src/SearchAPI ./SearchAPI

LABEL maintainer="Alaska Satellite Facility Discovery Team <uaf-asf-discovery@alaska.edu>"

# Set the CMD to your handler (could also be done as a parameter override outside of the Dockerfile)
CMD exec uvicorn --host $HOST --port=$PORT SearchAPI.application:app