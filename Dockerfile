FROM ubuntu:16.04
ENV LANG en_US.UTF-8
MAINTAINER Paul Huygen (paul.huygen@huygen.nl)
EXPOSE 5002
ADD ./repo ./repo
WORKDIR ./repo
RUN ./doit
CMD startservers


