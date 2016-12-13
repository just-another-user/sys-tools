#!/bin/bash
# ############################################# #
#
# first_install.sh (v0.1)
# by just-another-user
#
# Description:
# Install all of my requirements in
# one simple command.
#
# ############################################# #

sudo apt update
sudo apt dist-upgrade -y
sudo apt install python python-dev python3 python3-dev python-pip python3-pip python-setuptools python3-setuptools python-tk python3-tk build-essential git libffi-dev openssl libssl-dev ffmpeg libsdl2-dev libsdl2-image-dev libsdl2-mixer-dev libsdl2-ttf-dev libportmidi-dev libswscale-dev libavformat-dev libavcodec-dev zlib1g-dev libxml2-dev libxslt1-dev libtiff5-dev libjpeg8-dev zlib1g-dev libfreetype6-dev liblcms2-dev libwebp-dev tcl8.6-dev tk8.6-dev libcurl4-openssl-dev libsmbclient-dev libcups2-dev openjdk-8-jdk openjdk-8-jre unixodbc unixodbc-dev libsqlite3-dev libmysqlclient-dev

# Dropbox
sudo apt-key adv --keyserver pgp.mit.edu --recv-keys 5044912E
sudo sh -c 'echo "deb http://linux.dropbox.com/ubuntu/ xenial main" >> /etc/apt/sources.list.d/dropbox.list'

# Pycharm
sudo add-apt-repository ppa:mystic-mirage/pycharm
sudo sh -c 'echo "deb http://ppa.launchpad.net/mystic-mirage/pycharm/ubuntu xenial main" >> /etc/apt/sources.list.d/pycharm.list'

# Kivy
sudo add-apt-repository ppa:kivy-team/kivy
sudo sh -c 'echo "deb http://ppa.launchpad.net/kivy-team/kivy/ubuntu xenial main" >> /etc/apt/sources.list.d/kivy.list'
