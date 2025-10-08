FROM ghcr.io/edulinq/lms-docker-moodle-base:0.0.1

ENV DEBIAN_FRONTEND=noninteractive

WORKDIR /work

# Install Python Dependencies
COPY ./requirements.txt /work/
RUN pip3 install -r /work/requirements.txt

# Copy Data
COPY ./testdata/raw /work/data
