#! /bin/bash

# Download the source code of Freya.
git clone https://github.com/szeged/Freya.git

# Build and install.
cd Freya
./autogen.sh
./configure --prefix=`pwd`/inst
make
make install

cd freya
make
make install
