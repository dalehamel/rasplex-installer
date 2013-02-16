
class _DynamicModule(object):
    def load(self, code):
        execdict = {'__builtins__': None}
        exec code in execdict
        for key in execdict:
            if not key.startswith('_'):
                setattr(self, key, execdict[key])

import sys as _sys
_ref, _sys.modules[__name__] = _sys.modules[__name__], _DynamicModule()

import os,urllib2,platform,re,datetime,imp

INSTALL_URL="https://raw.github.com/dalehamel/rasplex-installer/master/getrasplex-bootstrapped.py"

def bootstrap():
    print "Getting latest installer..."
    dl = urllib2.urlopen(INSTALL_URL)
    code = dl.read()
   
    import getrasplex

    getrasplex.load(code)


if __name__=="__main__":
    bootstrap()
