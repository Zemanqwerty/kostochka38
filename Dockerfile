FROM --platform=linux/amd64 python:3 as build

RUN #!/bin/bash
# RUN #!/usr/bin/env python3



# COPY reqs.pip /code/reqs.pip
# RUN pip install --upgrade pip
# RUN pip install -r /code/reqs.pip

# WORKDIR /code/

# EXPOSE 8000



RUN apt-get update && apt-get install -y --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /code/

COPY . /code/

RUN pip install --upgrade pip
RUN pip install -r reqs.pip

EXPOSE 8000

# CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]