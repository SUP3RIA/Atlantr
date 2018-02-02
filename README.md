# Atlantr Imap Checker. 
##### Fastes Email:Pass Checker on the planet.

![Screencast](https://raw.githubusercontent.com/SUP3RIA/Atlantr/master/screen.gif)

Atlantr is a tool to validate login credentials of email accounts via the IMAP protocol. 
Green threads (Gevent) are used to implement concurrent and asynchronous networking.
### system requirements:
- Python 2.7.x
- Gevent (pip install gevent)
- tqdm (pip install tqdm)
- 512MB RAM
- Linux preferred
#### Example usage:
```
python atr3.py -i input.txt -o output.txt -t 1000 -g true 
```
#### Optional Arguments:
If no optional arguments are provided the default values are used.

| Short| Long | Description | Default value |
| ----------------- | ---------------------------- | ------------------ | ------|
|-i |--input|name of input text file|mail_pass.txt |
|-o|--output|name of output text file| mail_pass_valid.txt|
|-t|--threads|number of "threads" used|100 |
|-iu|--invunma|log invalid and unmatched accounts|true |
|-g|--grabber|get emails according to the provided imap queries|false |
|-mf|--matchfile|define textfile with imap queries for grabber| matchers.dat|
|-to|--timeout|define timeout for all sockets in seconds| 5|
|-r|--resume|resume from line defined in "last_line.log"|false |
|-b|--big|initialize progressbar without starting linecount| false|
|-uh|--unknownhosts|check hardcoded list of subdomains for hosts without settings|true |
|-s|--snap|compress "grabbed" folder at the end as .zip| true|
|-gper|--grabperformance|Grabs but does not save emails| false|

##
### Functions explained in detail
###### IMAP Login
The validation of the credentials is implemented using the IMAP standard library of Python via a SSL connection. The protocoll is not explicitly specified to work concurrently but it seems to work reliable with Gevent. Settings for domains are obtained from hosts.dat.
###### Email Grabber
If the login is successful as is the -g switch is true, IMAP queries obtained from matchers.dat are executed and returned emails are saved in the folder "grabbed". Each credential gets its own textfile which will be appended, even after its restart.
Credentials of accounts which have >1 emails returned to the imap query are saved in a textfile and if the -gper wich is true no emails will be saved.
In case -s switch is true, the "grabbed" folder will be compressed to a .zip file (however, it will not be deleted) prior to Atlantr termination.

There is no parsing of emails for information supported.
Please use an external programm for that!
###### Pause/Resume Feature
It is possible to pause and resume at the next start of the script. Just press Ctrl+C and the program will shut down gracefully and write the last line processed into lastline.log. Resume at the next start with the -r true switch.

###### Hosts Without Settings
If no settings are found for a domain, a hardcoded list of subdomains will be used to find a valid imap server.

> mail, pop, pop3, imap-mail, inbound, mx, imaps, smtp, me

If there is a valid subdomain found of a domain to establish a connection to an imap server, it will be saved to hoster.dat.
##
### Usage with TOR or Proxies
There is no internal functionality for any kind of proxy implemented but it works well with external proxifier programs like "proxychains".

##### Tutorial for Linux (Debian, Ubuntu):
Update and and then install Tor and Proxychains:
```
sudo apt-get update
sudo apt-get install tor
sudo apt-get install proxychains
```
Edit the torrc file to get new ip after 10 seconds:
``` 
sudo nano /etc/tor/torrc 
```
Add this line and save to disk:
```
MaxCircuitDirtiness 10
```
Start Tor:
```
tor
```
Check if Proxychains is working:
```
proxychains curl https://api.ipify.org/tformat=text
```
The returned ip should be different when proxychains is used!
```
curl https://api.ipify.org/tformat=text
```
Start Atlantr like this:
```
sudo proxychains python atr3.py 
```
Note that Proxychains can be configured to work with Socks5 and other types of proxies. There are good Tutorials to find via Google.
##

#### Formats and conventions
Mail:Pass:
user@domain.com:password
hoster.dat:
domain.com:imap.domain.com:port
matchers.dat:
search|(FROM "domain.com")|discriptor
