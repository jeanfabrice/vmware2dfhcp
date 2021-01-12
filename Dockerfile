ARG PYTHON3_FLAVOUR=alpine

FROM python:3-${PYTHON3_FLAVOUR} AS python

FROM python as builder
WORKDIR /usr/src/app
COPY . .
RUN pip install --no-cache-dir setuptools wheel && \
    python setup.py sdist bdist_wheel

FROM python
ARG AUTHOR
ARG CREATED
ARG DESCRIPTION
ARG EMAIL
ARG LICENSES
ARG REVISION
ARG SOURCE
ARG TITLE
ARG VERSION
LABEL org.opencontainers.image.authors="${AUTHOR} <${EMAIL}>"
LABEL org.opencontainers.image.created=${CREATED}
LABEL org.opencontainers.image.description=${DESCRIPTION}
LABEL org.opencontainers.image.licenses=${LICENSES}
LABEL org.opencontainers.image.revision=${REVISION}
LABEL org.opencontainers.image.source=${SOURCE}
LABEL org.opencontainers.image.title=${TITLE}
LABEL org.opencontainers.image.version=${VERSION}
COPY --from=builder /usr/src/app/dist/*.whl .
RUN pip install *.whl && \
    rm -rf *.whl
ENTRYPOINT [ "vmware2dhcp-cli" ]