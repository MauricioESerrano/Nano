#!/bin/bash

# change the perl command with perl libraries
cp /home/exnadmin/pdf/perl/bin/perl_db /usr/bin/perl5.26.1
rm -f /usr/bin/perl
ln -s /usr/bin/perl5.26.1 /usr/bin/perl
