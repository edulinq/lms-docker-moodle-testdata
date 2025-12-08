# LMS Docker Image - Moodle With Test Data

A [Docker](https://en.wikipedia.org/wiki/Docker_(software)) image running an instance of the
[Moodle Learning Management System (LMS)](https://en.wikipedia.org/wiki/Moodle).
This image is based off of [ghcr.io/edulinq/lms-docker-moodle-base](https://github.com/edulinq/lms-docker-moodle-base),
and includes test data (users, courses, assignments, etc).

## Cloning

This repository includes submodules.
To fetch these submodules on clone, add the `--recurse-submodules` flag.
For example:
```sh
git clone --recurse-submodules git@github.com:edulinq/lms-docker-moodle-testdata.git
```

To fetch the submodules after cloning, you can use:
```sh
git submodule update --init --recursive
```

## Usage

The docker image is fairly standard, and does not require any special care when building or running.

Running the scripts in this project requires Python >= 3.8 and the dependencies listed in [requirements.txt](requirements.txt).
You can install these requirements in pip with:
```sh
pip install -r requirements.txt -r requirements-dev.txt
```

### Building

You can build an image with the tag `lms-docker-moodle-testdata` using:
```sh
docker build -t lms-docker-moodle-testdata .
```

### Running

Once built, the container can be run using standard options.
Moodle uses port 80 by default, so that port should be passed through
(or translated to an unpriveleged port):
```sh
# Using the previously built image.
docker run --rm -it -p 80:8080 --name moodle lms-docker-moodle-base

# Using the pre-built image.
docker run --rm -it -p 80:8080 --name moodle ghcr.io/edulinq/lms-docker-moodle-base
```

### Generating Test HTTP Data

To generate test HTTP data (for use in a [mock HTTP server](https://github.com/edulinq/python-utils/blob/main/edq/testing/httpserver.py)),
you can use the [scripts/generate-test-data.py](scripts/generate-test-data.py) script:
```sh
# Using the pre-built image.
./scripts/generate-test-data.py

# Using the previously built image.
./scripts/generate-test-data.py --image-name lms-docker-moodle-testdata
```

This will generate test HTTP exchanges in the [testdata/http](testdata/http) directory.

Use `--help` to see other available options (such as output directory).

### Verifying Test HTTP Data

To verify that test data matches the output of a Moodle image,
you can use the [scripts/verify-test-data.py](scripts/verify-test-data.py) script:
```sh
# Using the pre-built image.
./scripts/verify-test-data.py

# Using the previously built image.
./scripts/verify-test-data.py --image-name lms-docker-moodle-testdata
```

This will verify that the test HTTP exchanges in the [testdata/http](testdata/http) directory
get the same response from you Moodle image.

This verification step is also done as part of CI.

Use `--help` to see other available options (such as the test data directory).

## Licensing

This repository is provided under the MIT licence (see [LICENSE](./LICENSE)).
Moodle LMS is covered under the [GPL-3.0 license](https://github.com/moodle/moodle/blob/main/COPYING.txt).
