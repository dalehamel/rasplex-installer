# Overview

This is the installer for rasplex. It should automatically detect the fastest mirror based on the current available mirrors, and then grab the latest installer from github. 

It works by using a bootstrap script (that should never change), to download the latest script. This way, end users should only ever need to download and run the bootstrap script, but always have the latest installer.


# Requirements

Mac OSX or Linux with python 2.7+

Require various utils to be installed, will tell you what it needs if it doesn't find it.



# Usage

 python getrasplex.py

or
 chmod +x getrasplex.py
 ./getrasplex.py

# Special thanks

Thanks to Sam Nazarko, as this script is based off of his Raspbmc installer.
