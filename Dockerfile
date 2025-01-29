FROM ubuntu:24.04

COPY ./ /app

WORKDIR /app

# These files are just needed so the simulation stage can run
COPY ./.docker/pflotran-dummy /usr/bin/pflotran
COPY ./.docker/mpirun-dummy /usr/bin/mpirun

# On Ubuntu 24.04, python3 is python3.12
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y python3-poetry
RUN poetry install

CMD poetry shell
