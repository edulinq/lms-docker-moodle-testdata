FROM ghcr.io/edulinq/lms-docker-moodle-base:0.0.2

ENV DEBIAN_FRONTEND=noninteractive

WORKDIR /work

# Install Python Dependencies
COPY ./requirements.txt /work/
RUN pip3 install --break-system-packages -r /work/requirements.txt

# Copy Data
COPY ./lms-testdata /work/lms-testdata
COPY ./scripts/load-data.py /work/scripts/

# Populate with test data.
RUN \
    # Start the DB in the background. \
    mysqld_safe --nowatch \
    # Wait for the DB to be ready. \
    && (until mysqladmin ping --silent; do echo "Waiting for database server to start..." ; sleep 2 ; done) \
    # Load the data. \
    && python3 /work/scripts/load-data.py \
    # Stop the DB. \
    && mysqladmin shutdown
