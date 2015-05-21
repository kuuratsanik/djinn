#!/usr/bin/env python

import math
import subprocess, re, os, sys, csv

featmaps = {}     #  c   h/w
featmaps['input'] = [128, 1]
featmaps['small'] = [512, 1]
featmaps['med']   = [256,  1]
featmaps['large'] = [1024, 1]
featmaps['alt']   = [2048, 1]
featmaps['alt1']  = [4096, 1]
featmaps['alt2']  = [64, 1]
featmaps['alt3']  = [32, 1]

batches    = [1, 16, 64, 256]
batches    = [1]

def shcmd(cmd):
    subprocess.call(cmd, shell=True)

def shcom(cmd):
    p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
    out = p.communicate()[0]
    return out

def main( args ):
    PLAT = args[1]
    THREADS=args[2]
    NETCONF='sig'
    NET=NETCONF + '.prototxt'
    OUTNAME=NETCONF + '-sweep.csv'
    OUTNAME1=NETCONF + '-fpops.csv'
    FINAL=NETCONF+'-'+PLAT+'-gflops.csv'
    
    shcom('rm -rf %s-%s*' % NETCONF, PLAT))
    f = open(OUTNAME1, "wb")
    w = csv.writer(f)
    w.writerow(['layer','batch','channel','height','width','fpops'])
    
    for batch in batches:
        cmd = './change-dim.sh %s %s %s' % (NET, 1, batch)
        shcom(cmd)
        for k in featmaps:
            channel = featmaps[k][0]
            height  = featmaps[k][1]
            cmd = './change-dim.sh %s %s %s' % (NET, 2, channel)
            shcom(cmd)
            cmd = './change-dim.sh %s %s %s' % (NET, 3, height)
            shcom(cmd)
            cmd = './change-dim.sh %s %s %s' % (NET, 4, height)
            shcom(cmd)
            fpops = batch*channel*height*height
        
            w.writerow([NETCONF,batch,channel,height,height,fpops])
            if PLAT is 'cpu':
                cmd = 'OPENBLAS_NUM_THREADS=%s ./dummy --gpu 1 --network %s --layer_csv %s' % (THREADS, NET, OUTNAME)
            else:
                cmd = './dummy --gpu 1 --network %s --layer_csv %s' % (NET, OUTNAME)
            shcom(cmd)
    
    f.close()
    cmd ='sed "1s/^/layer,lat\\n/" %s > temp.txt' % (OUTNAME)
    shcom(cmd)
    shcom('mv temp.txt %s' % OUTNAME)
    f1 = file(OUTNAME, 'r')
    f2 = file(OUTNAME1, 'r')
    f3 = open(FINAL, "wb")
    w1 = csv.writer(f3)
    w1.writerow(['layer','batch','channel','height','width','fpops','lat','gflops'])
    
    c1 = csv.reader(f1)
    c2 = csv.reader(f2)
    
    next(c1, None)
    next(c2, None)
    
    for r1,r in zip(c1,c2):
        lat = float(r1[1])/1000
        gflops = float(r[5]) / lat / pow(10,9)
        w1.writerow([r[0],r[1],r[2],r[3],r[4],r[5],r1[1],gflops])
    
    f3.close()

if __name__=='__main__':
    sys.exit(main(sys.argv))
