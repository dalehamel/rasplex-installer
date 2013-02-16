
INSTALL_URL="https://raw.github.com/dalehamel/rasplex-installer/master/getrasplex-bootstrapped.py"

class _DynamicModule(object):
    def load(self, code):
        execdict = {'__builtins__': None}
        exec code in execdict
        for key in execdict:
            if not key.startswith('_'):
                setattr(self, key, execdict[key])

import sys 
import os,urllib2,platform,re,datetime,imp
_ref, sys.modules[__name__] = sys.modules[__name__], _DynamicModule()



def bootstrap():
    print "Getting latest installer..."
    dl = urllib2.urlopen(INSTALL_URL)
    code = dl.read()
   
    import getrasplex

    getrasplex.load(code)
    import sys
    getrasplex.doInstall()


if __name__=="__main__":
    bootstrap()
