FROM phusion/baseimage as nlpp-base-layer
ENV LANG en_US.UTF-8
MAINTAINER Paul Huygen (paul.huygen@huygen.nl)
EXPOSE 5002
COPY ./repo ./repo
WORKDIR ./repo
RUN ./doit
WORKDIR /root/nlpp_ubuntu_16.04/
COPY ./custom/installDependencies ./installDependencies
RUN ./installDependencies

#CMD /repo/startservers

# Use baseimage-docker's init system.
CMD ["/sbin/my_init"]	

# Clean up APT when done.
RUN apt-get clean && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*


