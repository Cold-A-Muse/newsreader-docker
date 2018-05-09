FROM ubuntu:16.04
ENV LANG en_US.UTF-8
MAINTAINER Paul Huygen (paul.huygen@huygen.nl)
EXPOSE 5002
ADD ./repo ./repo

RUN ./repo/installbackground
RUN ./repo/installmodules < ./repo/modulelist

CMD python /usr/local/nlpp/server/server.py --host 0.0.0.0 --port 5002 
