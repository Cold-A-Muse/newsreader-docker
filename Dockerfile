FROM ubuntu:16.04 as nlpp-base-layer
ENV LANG en_US.UTF-8
MAINTAINER Paul Huygen (paul.huygen@huygen.nl)
EXPOSE 5002
COPY ./repo ./repo
WORKDIR ./repo
RUN ./doit

FROM nlpp-base-layer as nlpp-dependency-layer
WORKDIR /root/nlpp_ubuntu_16.04/
COPY ./custom/installDependencies ./installDependencies
RUN ./installDependencies

FROM nlpp-dependency-layer as nlpp-modules-layer
COPY ./custom/modulelist-en ./modulelist-en
RUN cat ./modulelist-en | ./installmodules

COPY ./custom/createProduction /usr/local/share/pipelines/nlpp/nlppmodules/createProduction
WORKDIR /usr/local/share/pipelines/nlpp/nlppmodules
RUN bash ./createProduction

FROM nlpp-base-layer as nlpp-production-layer
WORKDIR /root/nlpp_ubuntu_16.04/
COPY ./custom/ubuntu_runtime_packages ./ubuntu_packages
COPY ./custom/installProductionDependencies ./installProductionDependencies
RUN ./installProductionDependencies

COPY --from=nlpp-modules-layer /usr/local/share/pipelines/nlpp/nlppmodules/production/ixa-pipe-tok /usr/local/share/pipelines/nlpp/nlppmodules/ixa-pipe-tok

COPY --from=nlpp-modules-layer /usr/local/share/pipelines/nlpp/nlppmodules/production/ixa-pipe-pos /usr/local/share/pipelines/nlpp/nlppmodules/ixa-pipe-pos

#COPY --from=nlpp-modules-layer /usr/local/share/pipelines/nlpp/nlppmodules/production/ixa-pipe-topic /usr/local/share/pipelines/nlpp/nlppmodules/ixa-pipe-topic

COPY --from=nlpp-modules-layer /usr/local/share/pipelines/nlpp/nlppmodules/production/ixa-pipe-parse /usr/local/share/pipelines/nlpp/nlppmodules/ixa-pipe-parse

COPY --from=nlpp-modules-layer /usr/local/share/pipelines/nlpp/nlppmodules/production/ixa-pipe-nerc/ /usr/local/share/pipelines/nlpp/nlppmodules/ixa-pipe-nerc/

COPY --from=nlpp-modules-layer /usr/local/share/pipelines/nlpp/nlppmodules/production/ixa-pipe-ned /usr/local/share/pipelines/nlpp/nlppmodules/ixa-pipe-ned

COPY --from=nlpp-modules-layer /usr/local/share/pipelines/nlpp/nlppmodules/production/entity-relink-pipeline /usr/local/share/pipelines/nlpp/nlppmodules/entity-relink-pipeline

COPY --from=nlpp-modules-layer /usr/local/share/pipelines/nlpp/nlppmodules/production/NWRDomainModel /usr/local/share/pipelines/nlpp/nlppmodules/NWRDomainModel

COPY --from=nlpp-modules-layer /usr/local/share/pipelines/nlpp/nlppmodules/production/ixa-pipe-wikify /usr/local/share/pipelines/nlpp/nlppmodules/ixa-pipe-wikify

COPY --from=nlpp-modules-layer /usr/local/share/pipelines/nlpp/nlppmodules/production/EHU-ukb.v30 /usr/local/share/pipelines/nlpp/nlppmodules/EHU-ukb.v30

COPY --from=nlpp-modules-layer /usr/local/share/pipelines/nlpp/nlppmodules/production/it_makes_sense_WSD /usr/local/share/pipelines/nlpp/nlppmodules/it_makes_sense_WSD

COPY --from=nlpp-modules-layer /usr/local/share/pipelines/nlpp/nlppmodules/production/EHU-corefgraph.v30 /usr/local/share/pipelines/nlpp/nlppmodules/EHU-corefgraph.v30

COPY --from=nlpp-modules-layer /usr/local/share/pipelines/nlpp/nlppmodules/production/ixa-pipe-srl /usr/local/share/pipelines/nlpp/nlppmodules/ixa-pipe-srl

COPY --from=nlpp-modules-layer /usr/local/share/pipelines/nlpp/nlppmodules/production/FBK-time.v30 /usr/local/share/pipelines/nlpp/nlppmodules/FBK-time.v30

COPY --from=nlpp-modules-layer /usr/local/share/pipelines/nlpp/nlppmodules/production/FBK-temprel.v30 /usr/local/share/pipelines/nlpp/nlppmodules/FBK-temprel.v30

COPY --from=nlpp-modules-layer /usr/local/share/pipelines/nlpp/nlppmodules/production/FBK-causalrel.v30 /usr/local/share/pipelines/nlpp/nlppmodules/FBK-causalrel.v30

COPY --from=nlpp-modules-layer /usr/local/share/pipelines/nlpp/nlppmodules/production/EventCoreference /usr/local/share/pipelines/nlpp/nlppmodules/EventCoreference

COPY --from=nlpp-modules-layer /usr/local/share/pipelines/nlpp/nlppmodules/production/vua_factuality /usr/local/share/pipelines/nlpp/nlppmodules/vua_factuality

COPY --from=nlpp-modules-layer /usr/local/share/pipelines/nlpp/nlppmodules/production/opinion_miner_deluxePP /usr/local/share/pipelines/nlpp/nlppmodules/opinion_miner_deluxePP

COPY --from=nlpp-modules-layer /usr/local/share/pipelines/nlpp/nlppmodules/production/vua-resources /usr/local/share/pipelines/nlpp/nlppmodules/vua-resources

COPY ./custom/modules.en /usr/local/etc/nlpp
COPY ./custom/nlpp.sh /root/nlpp_ubuntu_16.04/run/nlpp2 
COPY ./custom/iexec_nlpp.sh /root/nlpp_ubuntu_16.04/run/iexec_nlpp
COPY ./custom/runTokenizerWithRawText /usr/local/share/pipelines/nlpp/nlppmodules/ixa-pipe-tok/run
WORKDIR /root/nlpp_ubuntu_16.04/run/
CMD /bin/bash
