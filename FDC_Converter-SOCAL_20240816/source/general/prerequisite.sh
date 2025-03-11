#!/bin/bash

# install requirement plugin 
yum -y install python3 pip3 git

# set library path 
### ImportError: /usr/lib64/python3.6/lib-dynload/pyexpat.cpython-36m-x86_64-linux-gnu.so: undefined symbol: XML_SetHashSalt
export LD_LIBRARY_PATH=/lib64/:${LD_LIBRARY_PATH}

# install required pip lib
pip3 install pandas jinja2
