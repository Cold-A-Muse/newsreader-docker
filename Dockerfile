FROM ubuntu:16.04 as nlpp-base-layer
ENV LANG en_US.UTF-8
MAINTAINER Paul Huygen (paul.huygen@huygen.nl)
EXPOSE 5002
COPY ./repo ./repo
WORKDIR ./repo
RUN ./doit

FROM nlpp-base-layer as nlpp-dependency-layer
WORKDIR /root/nlpp_ubuntu_16.04/
COPY ./custom ./
RUN ./installDependencies

FROM nlpp-dependency-layer as nlpp-modules-layer
RUN cat ./modulelist-en | ./installmodules

WORKDIR /usr/local/share/pipelines/
#RUN ./cleanUp

FROM nlpp-dependency-layer as nlpp-production-layer
COPY --from=nlpp-modules-layer /usr/local/share/pipelines/nlpp/nlppmodules /usr/local/share/pipelines/nlpp/nlppmodules

WORKDIR /repo/

CMD ./startservers
