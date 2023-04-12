FROM public.ecr.aws/lambda/python:3.10

# Work from this location:
WORKDIR ${LAMBDA_TASK_ROOT}

### GENERIC INSTALLS:
# Install the function's dependencies using file requirements.txt
# from your project folder.
COPY requirements.txt  .
RUN  python3 -m pip install -U --no-cache-dir -r requirements.txt

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

ENTRYPOINT [ "python3", "-m", "SearchAPI.main" ]
