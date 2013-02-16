

MIRROR_FOLDER="/release/"
MIRROR_URL="https://s3.amazonaws.com/plex-rpi"+MIRROR_FOLDER+"mirrors"
MIRROR_PROTOCOL="https://"
MIRRORCHECK="mirrorcheck"


import os,sys,urllib2,platform,re,datetime,imp

# check if running on Mac
mac = (platform.system() == 'Darwin')


# yes/no prompt adapted from http://code.activestate.com/recipes/577058-query-yesno/
def query_yes_no(question, default="yes"):
    valid = {"yes":"yes", "y":"yes", "ye":"yes", "no":"no", "n":"no"}
    if default == None:
        prompt = " [y/n] "
    elif default == "yes":
        prompt = " [Y/n] "
    elif default == "no":
        prompt = " [y/N] "
    else:
        raise ValueError("invalid default answer: '%s'" % default)
    while 1:
        print question + prompt
        choice = raw_input().lower()
        if default is not None and choice == '':
            return default
        elif choice in valid.keys():
            return valid[choice]
        else:
            print "Please respond with 'yes' or 'no' (or 'y' or 'n').\n"

def chunk_report(bytes_so_far, chunk_size, total_size):
    percent = float(bytes_so_far) / total_size
    percent = round(percent*100, 2)
    sys.stdout.write("Downloaded %0.2f of %0.2f MiB (%0.2f%%)\r" % 
        (float(bytes_so_far)/1048576, float(total_size)/1048576, percent))
    if bytes_so_far >= total_size:
        sys.stdout.write('\n')

def chunk_read(response, file, chunk_size, report_hook):
    total_size = response.info().getheader('Content-Length').strip()
    total_size = int(total_size)
    bytes_so_far = 0
    while 1:
        chunk = response.read(chunk_size)
        file.write(chunk)
        bytes_so_far += len(chunk)
        if not chunk:
            break
        if report_hook:
            report_hook(bytes_so_far, chunk_size, total_size)
    return bytes_so_far

def download(url):
    print "Downloading, please be patient..."
    dl = urllib2.urlopen(url)
    dlFile = open('installer.img.gz', 'w')
    chunk_read(dl, dlFile, 8192, chunk_report)
    #dlFile.write(dl.read())
    dlFile.close()

def deviceinput():
    # they must know the risks!
    verified = "no"
    raw_input("Please ensure you've inserted your SD card, and press Enter to continue.")
    while verified is not "yes":
        print ""
        if mac:
            print "Enter the 'IDENTIFIER' of the device you would like imaged:"
        else:
            print "Enter the 'Disk' you would like imaged, from the following list:"
        listdevices()
        print ""
        if mac:
            device = raw_input("Enter your choice here (e.g. 'disk1', 'disk2'): ")
        else:
            device = raw_input("Enter your choice here (e.g. 'mmcblk0' or 'sdd'): ")
        # Add /dev/ to device if not entered
        if not device.startswith("/dev/"):
            device = "/dev/" + device
        if os.path.exists(device) == True:
            print "It is your own responsibility to ensure there is no data loss! Please backup your system before imaging"
            cont = query_yes_no("Are you sure you want to install rasplex to '\033[31m" + device + "\033[0m' ", "no")
            if cont == "no":
                sys.exit()
            else:
                verified = "yes"
        else:
            print "Device doesn't exist"
            # and thus we are not 'verified'
            verified = "no"
    return device

def listdevices():
    if mac:
        print "   #:                       TYPE NAME                    SIZE       IDENTIFIER"
        os.system('diskutil list | grep "0:"')
    else:
        os.system('fdisk -l | grep -E "Disk /dev/"')

def unmount(drive): # unmounts drive
    print "Unmounting all partitions..."
    if mac:
        exitcode = os.system("diskutil unmountDisk " + drive)
    else:
        # check if partitions are mounted; if so, unmount
        if os.system("mount | grep " + drive + " > /dev/null") == 0:
            exitcode = os.system("umount `mount | grep " + drive + " | cut -f1 -d ' '`")
        else:
            # partitions were not mounted; must pass error check
            exitcode = 0
    if exitcode != 0:
        print 'Error: the drive couldn\'t be unmounted, exiting...'
        sys.exit()

def mount(drive): # mounts drive to mount_rasplex/
    print "Mounting the drive for post-installation settings"
    if mac:
        os.system("diskutil mount -mountPoint mount_rasplex/ " + drive + "s1")
    else:
        if os.path.exists(drive + "p1"):
            drive = drive + "p"
        os.system("mount " + drive + "1  mount_rasplex/")

def imagedevice(drive, imagefile):
    print ""
    unmount(drive)
    # use the system's built in imaging and extraction facilities
    print "Please wait while rasplex is installed to your SD card..."
    print "This may take some time and no progress will be reported until it has finished."
    if mac:
        os.system("gunzip -c " + imagefile + " | dd of=" + drive + " bs=1m")
    else:
        os.system("gunzip -c " + imagefile + " | dd of=" + drive + " bs=1M")
        # Linux kernel must reload the partition table
        os.system("blockdev --rereadpt " + drive)
    print "Installation complete."

def autodetectMirrors( dl=None):

    if (dl == None):
        dl = urllib2.urlopen(MIRROR_URL)

    mirrors = list()

    for mirror in dl:
        mirrors.append( MIRROR_PROTOCOL+ mirror.strip() + MIRROR_FOLDER + MIRRORCHECK)
 
    return mirrors

def getCurrentFromMirrors( mirrors ):
 
    bestspeed = None
    bestmirror = None

    print "Determining fastest mirror..."
    for mirror in mirrors:
        sys.stdout.write("Checking "+mirror+"... ")
        tick =  datetime.datetime.now()
        dl = urllib2.urlopen(mirror)
        tock =  datetime.datetime.now()
        delta = tock - tick
        speed = float( 1 / ( float(delta.microseconds) / float(1000000) ))
        sys.stdout.write( "%s MB/s\n" % str(speed))
        


        if bestspeed == None or speed > bestspeed:
            bestspeed=speed
            bestmirror = mirror
    
    print "Fastest mirror is "+bestmirror
    bestmirror = bestmirror.replace(MIRRORCHECK,"current")
    current = urllib2.urlopen(bestmirror).read().strip()
    return current

def rasplexinstaller(current):
    # configure the device to image
    disk = deviceinput()
    # should downloading and extraction be done?
    redl = "" # so that redl == "yes" doesn't throw an error
    if os.path.exists("installer.img.gz"):
        redl = query_yes_no("It appears that the rasplex installation image has already been downloaded. Would you like to re-download it?", "yes")
    if redl == "yes" or not os.path.exists("installer.img.gz"):
        # call the dl    
        print "Downloading from mirror: "+current
        download(current)
    # now we can image
    if mac:
        regex = re.compile('/dev/r?(disk[0-9]+?)')
        try:
            disk = re.sub('r?disk', 'rdisk', regex.search(disk).group(0))
        except:
            print "Malformed disk specification -> ", disk
            sys.exit()
    imagedevice(disk, "installer.img.gz")
    # post-install options, if supported by os
    print "rasplex is now ready to finish setup on your Pi, please insert the SD card with an active internet connection"



def doInstall():
    
    if "-m" not in sys.argv:
        mirrors = autodetectMirrors()
        current = getCurrentFromMirrors(mirrors)
    else:
        mirrors = list()
        mirror = sys.argv[ sys.argv.index("-m")+1]
        print "Forcing mirror "+mirror
        mirrors.append( mirror )
        mirrors = autodetectMirrors(mirrors)
        current = getCurrentFromMirrors(mirrors)

# check if root with geteuid
    if os.geteuid() != 0:
        print "Please re-run this script with root privileges, i.e. 'sudo ./getrasplex.py'\n"
        sys.exit()


# check if all necessary system utilities are present
    if mac:
        exitcode = os.system("which clear diskutil grep gunzip dd")
    else:
        exitcode = os.system("which clear fdisk grep umount mount cut gunzip dd blockdev")
    if exitcode != 0:
        print "Error: your operating system does not include all the necessary utilities to continue."
        if mac:
            print "Utilities necessery: clear diskutil grep gunzip dd"
        else:
            print "Utilities necessery: clear fdisk grep umount mount cut gunzip dd blockdev"
        print "Please install them."
        sys.exit()

    os.system("clear")

    print ""
    print """
This is the Rasplex installer for Linux and OS X"
It is based on Sam Nazarko's raspbmc installer. 
All credit goes to Sam, all blame goes to Dale : )

Read more about Rasplex at 
    http://blog.srvthe.net"

If you like the project and want to support future development, please donate at 
    http://srvthe.net

Donations are re-invested in the project, and cover various expenses, as well as act
as an incentive for community members to participate and contribute. 

This is a community driven project, and receives no funding from plex directly.

Feed your developers! Donate at 
    http://srvthe.net

If you would like support, kindly email:

    dale.hamel@srvthe.net

If you would like to report a bug, please:

    First check for duplicates at:
        https://trello.com/board/plex-on-raspberry-pi/510c4d34e1d17df66c00092a
   
    Then make a trello account, and remember your name (should be under profile,
    @yourname)

    Next go to http://chat.srvthe.net and join channel "plex" in a web browser,
    or connect to irc.srvthe.net with your favorite irc client and join #plex

    Tell Dale your name so he can add you to the trello board with:

        /msg void_ptr @yourname

Thank you very much! I hope you enjoy rasplex as much as I do!

-Dale Hamel

"""

    rasplexinstaller(current)

    print """

Rasplex hackers:

    Dale Hamel - Lead developer, builder, hoster, creator of rasplex (stubborn Canadian)
    Robert Buhren - weelkin (lead of OpenELEC port)
    Anil Daoud - Anil (Lead of Raspbian port)
    Lionel CHAZALLON - LongChair (Lead tester, first user to join the channel)
    Marc Massey - ElMassman (god of the GUI)
    Jay Smith - jsmith79 (stellar tester, helpful hacker, front line soldier)


Special thanks to:

    Sam Nazarko (as well as the whole raspbmc team) - creator of Raspbmc, on which much of this work was based
    Elan Feingold - creator of Plex - the best media center ever created
    Tobias Hieta - maintainer of PlexHT, which made this port possible
    GEWalker - creator of plex-linux, which got the ball rolling on this

Please donate at 

    http://srvthe.net
"""
