# Atlantr Imap Checker. 
##### Fastes Email:Pass Checker on the planet.

![Screencast](https://raw.githubusercontent.com/SUP3RIA/Atlantr/master/screen.png)

Atlantr is a tool to validate login credentials of email accounts via the IMAP protocol. 
Green threads (Gevent) are used to implement concurrent and asynchronous networking.
### system requirements:
- Python 2.7.x
- Gevent (pip install gevent)
- tqdm (pip install tqdm)
- 512MB RAM
- Linux preferred
#### Example usage:
python atr3.py -i input.txt -o output.txt -t 1000 -g true 
#### Optional Arguments:
When no optional arguments are provided default values are used.


| Short| Long | Description | Default value |
 ----------------- | :----------------------------: | :------------------: | ------:|
|-i |--input|name of input text file|mail_pass.txt |
|-o|--output|name of output text file| mail_pass_valid.txt|
|-t|--threads|number of "threads" used|100 |
|-iu|--invunma|log invalid and unmatched accounts|true |
|-g|--grabber|get emails according to the provided queries|false |
|-mf|--matchfile|define textfile with imap queries for grabber| matchers.dat|
|-to|--timeout|define timeout for all sockets in sec.| 5|
|-r|--resume|resume from line defined in "last_line.log"|false |
|-b|--big|don't initialize progressbar with linecount| false|
|-uh|--unknownhosts|Check hardcoded list for hosts without settings|true |
|-s|--snap|Compress "grabbed" folder at the end as .zip| true|
### Functions explained in detail
###### IMAP Login
The validation of the credentials is implemented using the IMAP standard library of Python via a SSL connection. The protocoll is not explicitly specified to work concurrently but it seems to work reliable with Gevent. Settings for domains are obtained from hosts.dat.
###### Email Grabber
When the login was successful and the -g switch is true, IMAP queries obtained from matchers.dat are executed and returned emails are saved in the folder "grabbed".
Each credentials gets its own textfile which will be appended to even after restarting. When -s switch is true, the "grabbed" folder will be compressed to a .zip file (but not deleted!) just before Atlantr terminates.

There is no parsing of emails for information supported.
Please use a external programm for that!
###### Hosts Without Settings
When no settings are found for a domain a hardcoded list of subdomains will be tried to connect to 
imap , mail, pop, pop3, imap-mail, inbound, mx, imaps, smtp, and m.
If there is a subdomain found it will be saved to hoster.dat.

#### Use with TOR or SOCKS5
###### Linux (Debian, Ubuntu):
sudo apt-get update

sudo apt-get install tor

sudo apt-get install proxychains

sudo nano /etc/tor/torrc

Add this line: MaxCircuitDirtiness 10

tor

proxychains curl https://api.ipify.org/tformat=text

sudo proxychains python atr3.py 


##### Formats:
###### Mail:Pass:
user@domain.com:password
###### hoster.dat:
domain.com:imap.domain.com:port
###### matchers.dat:
search|(FROM "domain.com")|discriptor
