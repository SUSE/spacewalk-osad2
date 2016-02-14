FROM csabakollar/spacewalk

MAINTAINER Kirill Klenov <horneds@gmail.com>

# update
RUN yum -y groupinstall "Development Tools"

# Install the module requirements
RUN easy_install argparse && \
    easy_install pyzmq && \
    easy_install python-daemon==1.5.5 && \
    easy_install lockfile
