FROM ubuntu:xenial

MAINTAINER marx2k <marx2k@yahoo.com>

RUN mkdir /nzbhydra

WORKDIR /nzbhydra

COPY libs ./libs

COPY nzbhydra ./nzbhydra

COPY ui-src ./ui-src

COPY .bowerrc .bowerrc

COPY bower.json bower.json

COPY gulpfile.js gulpfile.js

COPY nzbhydra.crt nzbhydra.crt

COPY nzbhydra.key nzbhydra.key

COPY nzbhydra.py nzbhydra.py

COPY package.json package.json

COPY version.txt version.txt

RUN apt-get update && apt-get -y install python

ENTRYPOINT ["python", "nzbhydra.py", "--nobrowser"]