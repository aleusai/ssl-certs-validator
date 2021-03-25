FROM ubuntu:20.04
RUN apt-get update -y && \
    apt-get -y upgrade && \
    apt-get install -y python3-pip python-dev

# Switch to non-root user:
RUN useradd -ms /bin/bash app
WORKDIR /app
USER app
COPY ../requirements.txt /app/requirements.txt
RUN /usr/bin/pip3 install -r /app/requirements.txt
COPY ../ .
CMD [ "python3", "-u" , "-m", "flask", "run", "--host=0.0.0.0"]

