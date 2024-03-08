FROM public.ecr.aws/lambda/python:3.10

# Work from this location:
WORKDIR ${LAMBDA_TASK_ROOT}

### GENERIC INSTALLS:
# System installs first so they're cached:
RUN yum install -y git
RUN  python3 -m pip install -U --no-cache-dir wheel
# Now add/install our files:
COPY SearchAPI/requirements.txt .
RUN  python3 -m pip install -U --no-cache-dir -r requirements.txt
COPY Discovery-asf_search ./Discovery-asf_search
RUN  python3 -m pip install -U --no-cache-dir ./Discovery-asf_search
COPY Discovery-WKTUtils ./Discovery-WKTUtils
RUN  python3 -m pip install -U --no-cache-dir ./Discovery-WKTUtils

### OUR FILES:
# Install our SearchAPI
COPY README.md ./README.md
COPY setup.py ./setup.py
COPY SearchAPI ./SearchAPI
RUN python3 -m pip install -U --no-cache-dir .

### NETORKING:
# What to open host too.
#    - localhost [default] = 127.0.0.1
#    - outside_world = 0.0.0.0
ENV OPEN_TO_IP="127.0.0.1"
ENV OPEN_TO_PORT=9000
EXPOSE ${OPEN_TO_PORT}

ENTRYPOINT [ "python3", "SearchAPI/main.py" ]
