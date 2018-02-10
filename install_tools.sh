#!/usr/bin/env bash
# ############################################# #
#
# install_tools.sh (v0.1)
# by just-another-user
#
# Description:
# Install tools to /usr/local/bin
# Update system and install base packages
#
# ############################################# #
echo Updating system...
./aptdate

echo Installing base packages...
sudo apt install -y python python3 python-dev python3-dev python-pip python3-pip python-setuptools python3-setuptools python-tk python3-tk build-essential libffi-dev openssl libssl-dev libsqlite3-dev libmysqlclient-dev git

sudo ln -snf `pwd`/aptdate /usr/local/bin/aptdate
sydi chmod +x /usr/local/bin/aptdate
sudo echo `which python3` `pwd`/pipdate.py \$\* > /usr/local/bin/pipdate
sydi chmod +x /usr/local/bin/pipdate
sudo ln -snf `pwd`/where /usr/local/bin/where
sydi chmod +x /usr/local/bin/where

echo Updating Python packages...
pipdate