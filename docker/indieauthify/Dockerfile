FROM ubuntu:22.04

ARG VERSION

LABEL org.opencontainers.image.source=https://github.com/vicchi/indieauthify
LABEL org.opencontainers.image.url=https://github.com/vicchi/indieauthify/tree/master#readme
LABEL org.opencontainers.image.authors="Gary Gale <gary@vicchi.org>"
LABEL org.opencontainers.image.version=${VERSION}
LABEL org.opencontainers.image.licenses=BSD-3-Clause
LABEL org.opencontainers.image.description="An IndieAuth server"

ENV DEBIAN_FRONTEND noninteractive
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV CRYPTOGRAPHY_DONT_BUILD_RUST=1

RUN ln -fs /usr/share/zoneinfo/Europe/London /etc/localtime && \
    apt-get update && \
    apt-get install -y --no-install-recommends curl git openssh-client python3 python3-pip sqlite3 && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /service

COPY ./requirements.txt /service/requirements.txt
COPY ./VERSION /service/VERSION

RUN --mount=type=ssh mkdir -p "${HOME}"/.ssh && \
    chmod 0600 "${HOME}"/.ssh && \
    ssh-keyscan github.com >> "${HOME}"/.ssh/known_hosts && \
    mkdir /service/run && \
    pip install --upgrade pip \
    pip install --no-cache-dir --upgrade -r /service/requirements.txt

COPY ./indieauthify_server /service/indieauthify_server
COPY ./static /service/static
COPY ./templates /service/templates
COPY --chmod=0755 ./docker/indieauthify/docker-entrypoint.sh /service/docker-entrypoint.sh
COPY ./docker/indieauthify/init-tokendb.sql /service/init-tokendb.sql

EXPOSE 80

HEALTHCHECK CMD curl --fail http://localhost:80 || exit 1
ENTRYPOINT ["/service/docker-entrypoint.sh"]
CMD ["gunicorn", "indieauthify_server.server:app", "--bind", "0.0.0.0:80"]
