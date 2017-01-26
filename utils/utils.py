"""Some useful functions
"""
import os
import sys

def check_dir(dname):
    """Check if directory exists, create it if it doesn't"""
    if(dname[-1] != "/"):
        dname = dname + "/"
    direc = os.path.dirname(dname)
    try:
        os.stat(direc)
    except:
        check = raw_input("Would you like to generate requested directory [Y/n]: ")
        if(check == "Y" or check == "y" or check == ""):
            os.makedirs(direc)
            print "Created directory {0}....".format(dname)
    return dname
