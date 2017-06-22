#! /bin/bash

# Todo: eliminate unneccesary dependencies (e.g. genfs, libusb)
sudo apt-get install -y autoconf libtool gperf flex bison autoconf2.13
sudo apt-get install -y cmake libncurses-dev libusb-1.0-0-dev genromfs
sudo apt-get install -y libsgutils2-dev gcc-arm-none-eabi minicom
sudo apt-get install -y python-pip pkg-config libssl-dev
sudo apt-get install -y gcc-arm-linux-gnueabihf binutils-arm-linux-gnueabi

sudo pip install schedule paramiko
