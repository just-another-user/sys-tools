#!/usr/bin/env bash

echo "Installing Python 2 + 3 + essentials..."
sudo apt install --upgrade -y python python3 python-dev python3-dev python-pip python3-pip
sudo -i pip2 install -U pip setuptools requests beautifulsoup4 pytest mock six selenium
sudo -i pip3 install -U pip setuptools requests beautifulsoup4 pytest mock six selenium

echo "Installing additional software..."
sudo apt install --upgrade -y chromium-browser wget curl lynx virtualbox 

echo "Installing Kivy..."
sudo add-apt-repository ppa:kivy-team/kivy
sudo apt install python-kivy --upgrade -y
sudo apt install python3-kivy --upgrade -y
sudo apt install python-kivy-examples --upgrade -y

echo "Done! :)"
