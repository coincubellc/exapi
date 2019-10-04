FROM continuumio/miniconda3
RUN apt-get update && apt-get install -y build-essential

RUN conda install -c conda-forge requests
ADD requirements.txt /exapi/requirements.txt
RUN pip install -r /exapi/requirements.txt
RUN conda install -c conda-forge uwsgi libiconv

ADD exapi /exapi
WORKDIR /exapi/web

COPY docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

ENTRYPOINT ["docker-entrypoint.sh"]
