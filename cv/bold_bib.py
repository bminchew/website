#!/usr/bin/env python3

import sys,os
import shutil
import numpy as np

def main(master='../pubs/minchew_journals.bib',new='../pubs/noedit_minchew_journals.bib'):
    bold_minchew(master,new)

def bold_minchew(master,new):
    replacement = r'\textbf{B. M. Minchew}'

    with open(master,'r') as fid:
        reads = fid.readlines()
    with open(new,'w') as fid:
        for r in reads:
            if 'Minchew' in r:
                replacer = 'Minchew, B. M.'
                if replacer in r:
                    rnew = r.replace(replacer,replacement)
                else:
                    replacer = 'Minchew, B.'
                    rnew = r.replace(replacer,replacement)
            else:
                rnew = r
            fid.write(rnew)
    return

if __name__=='__main__':
    main()
