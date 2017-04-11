FROM ubuntu:14.04
MAINTAINER Diego Rocha <diego@diegorocha.com.br>

# keep upstart quiet
RUN dpkg-divert --local --rename --add /sbin/initctl
RUN ln -sf /bin/true /sbin/initctl

# no tty
ENV DEBIAN_FRONTEND noninteractive

# get up to date
RUN apt-get update --fix-missing

RUN apt-get install -y build-essential git
RUN apt-get install -y python python-dev python-setuptools
RUN apt-get install -y python-pip python-virtualenv
RUN apt-get install -y nginx supervisor

RUN service supervisor stop

RUN virtualenv /opt/venv
ADD ./requirements.txt /opt/venv/requirements.txt
RUN /opt/venv/bin/pip install -r /opt/venv/requirements.txt
RUN /opt/venv/bin/pip install gunicorn

ADD ./supervisord.conf /etc/supervisord.conf
ADD ./nginx.conf /etc/nginx/nginx.conf

RUN pip install supervisor-stdout

RUN service nginx stop

COPY . /opt/app
RUN /opt/venv/bin/python /opt/app/manage.py collectstatic --noinput
CMD supervisord -c /etc/supervisord.conf -n

EXPOSE 80
