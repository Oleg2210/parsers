From ubuntu:18.04

WORKDIR /app

COPY docker/requirements.txt /app
COPY docker/sysdeps.sh /app
RUN /app/sysdeps.sh

COPY app/ /app
COPY docker/start.sh /app

CMD ["/bin/bash", "start.sh"]