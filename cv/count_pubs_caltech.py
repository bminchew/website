#!/usr/bin/env python3

import sys,os
import shutil

tex = 'cv_caltech.tex'
wtex = tex+'.test'

encoding = 'utf-8'
with open(tex,'r',encoding=encoding) as fid:
    reads = fid.readlines()

docnt = False
pubs = 0

for read in reads:
    if 'begin pub count' in read:
        docnt = True
    elif 'end pub count' in read:
        docnt = False
    elif docnt:
        pubs += len(read.split(','))
print(pubs)

with open(wtex,'w',encoding=encoding) as fid:
    for read in reads:
        outline = read
        if '## write number pubs here ##' in read:
            outline = read.split('}')[0] + '} (%d in total; * indicates students and $^\\star$ postdocs and other group members) %% ## write number pubs here ##\n' % pubs
        fid.write(outline)

shutil.move(wtex,tex)
