FROM python:3.11

ARG UUID
ARG API_PORT
ARG API_DIR
ARG API_GLOBAL_DIR

ENV PYTHONBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Non-privileged user to run the app
RUN adduser \
    --disabled-password \
    --gecos "" \
    # --no-create-home \
    --shell "/sbin/nologin" \
    --uid "${UUID}" \
    app_runner

# Necesary ports and volumes
EXPOSE ${API_PORT}
VOLUME ["${API_GLOBAL_DIR}"]

# Incorporate MSSQL packages
RUN mkdir /root/.gnupg/
RUN echo "keyserver hkps://keyserver.openpgp.org" >> /root/.gnupg/dirmngr.conf
RUN echo "no-use-tor" >> /root/.gnupg/dirmngr.conf
RUN curl -sSL https://packages.microsoft.com/keys/microsoft.asc \
    | gpg --dearmor \
    | tee /usr/share/keyrings/msprod-archive-keyring.gpg
RUN curl https://packages.microsoft.com/config/ubuntu/20.04/prod.list --output /etc/apt/sources.list.d/msprod.list
RUN sed --in-place 's|\[\(.*\)\]|[\1 signed-by=/usr/share/keyrings/msprod-archive-keyring.gpg]|' /etc/apt/sources.list.d/msprod.list

# Install basic dependencies
RUN apt update && apt upgrade -y

# TODO: Add here installation of required libraries
# -----------------------------------------------------------------------------
# ...
# -----------------------------------------------------------------------------

# Install MSSQL Database driver
RUN ACCEPT_EULA=Y apt install --yes mssql-tools unixodbc-dev

# Dependencies do not change really often, cache this step
RUN --mount=type=cache,target=/root/.cache/pip \
    --mount=type=bind,source=requirements.txt,target=requirements.txt \
    python -m pip install --requirement requirements.txt

# Copy necessary data from local
WORKDIR "${API_DIR}"
COPY . .

# Switch to non-privileged user
USER app_runner
