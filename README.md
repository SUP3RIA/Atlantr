Atlantr Imap Checker. Fastes Email:Pass Checker on the planet.
--------------------------------------------------------------
![Screencast](https://github.com/SUP3RIA/Atlantr/blob/master/screen.gif)

    usage: atr.py [-i INPUT] [-o OUTPUT] [-t THREADS] [-uh UNKNOWNHOSTS] [-l LOGGING] [-lsize LOGFILESIZE] [-gm GHOSTMODE] [-iu INVUNMA]

 - `-i` *Inputfile, any textfile with the format
   user@domain.com:password in each line should work. DEFAULT:
   mail_pass.txt*
 - `-o` *Outputfile, where to write valid results to disk. DEFAULT:
   mail_pass_valid.txt*
 - `-t` *Threads, define how many working threads you want to spawn.
   Greenlets (Gevent) are used for async threading. DEFAULT: 512*
 - `-uh` *Unknown hosts, tries to guess unknown hosts for their imap
   subdomain. This is BETA! DEFAULT: False*
 - `-l` *Logging, every proccesed line gets logged so if the programm
   stopps or crashes it can be continued from there. DEFAULT: False*
 - `-lsize` *Logfilesize, define how big the logfile fore the linecount
   should be in MB. After X MB old values are deleted. DEFAULT: 5*
 - `-gm` *Ghostmode, no userinput is needed to continue from old logged
   linecount. Handy if you use nohup. DEFAULT: False*

 

 - `-iu` *Log invalid an unmatched accounts. Disable for better
   performance DEFAULT: True*
