'''
A python class structure for reading in
data files. At the time of writing only
.spe files are supported, but the 
structure has been made flexible for
updates.

Author: Ed Leming
Date:   26/01/17
'''
import argparse
import csv
import datetime
import re
import numpy as np

class File(object):
    '''A generic file class'''
    def __init__(self, fname):
        """ Initialise a file data structure """
        self._fname = fname
        self._extension = fname.split("/")[-1].split(".")[-1]
        self._data = []
        self.read_file()
    
    def read_file(self):
        """ Place holder method - to be superceeded by methods in inherited classes """
        pass

    def get_file_name(self):
        """ Return path to this file """
        return self._fname

    def get_data(self):
        """ Get the data in this file """
        return self._data

    def get_extension(self):
        """ Get file extension """
        return self._extension

    def get_title(self):
        """ Return the name given to the file, minus the path and extension """
        return self._fname.split("/")[-1].replace(".{0}".format(self._extension), "")


class SpeFile(File):
    '''A class to read in all information from the .spe files
    kicked out by Boxerino
    '''
    def __init__(self, fname):
        """ Initialise a Spe_file """
        super(SpeFile, self).__init__(fname)

    def read_file(self):
        '''Read in a spe file
        '''
        with open(self._fname, 'rb') as f:
            reader = csv.reader(f, delimiter="\t")

            # Find `header` lines
            fields, field_index = [], []
            for i, row in enumerate(reader):
                if row[0][0] == "$":
                    fields.append(row[0][1:-1])
                    field_index.append(i)

            # Use index array to calculate the number of rows to be read for each `header` field
            field_length = []
            for i, x in enumerate(field_index):
                if(i==0):
                    continue
                field_length.append((x) - field_index[i-1])
            field_length.append(-1) # Last field length is undefined

            # Loop over all `headers` and save their data into a dict
            raw_fields = {}
            for i, x in enumerate(field_index):
                f.seek(0) # seek to start of file
                reader = csv.reader(f, delimiter="\t")
                data = []
                for j, row in enumerate(reader):
                    # Only take the lines we're interested in
                    if(j > field_index[i] and j < (field_index[i] + field_length[i])):
                        data = data + row
                    elif(j > field_index[i] and field_length[i] == -1):
                        data = data + row
                raw_fields[fields[i]] = data

        # Format Important fields
        self._raw_fields = raw_fields
        self._run_time = int(raw_fields["MEAS_TIM"][0].split(" ")[0])
        self._datetime = datetime.datetime.strptime(raw_fields["DATE_MEA"][0], "%m/%d/%Y %H:%M:%S")
        spec_data = []
        for val in raw_fields["DATA"]:
            spec_data = spec_data + [int(s) for s in re.findall(r'\b\d+\b', val)]
        self._data = spec_data[2:]

    def get_timestamp(self):
        return self._datetime
        
    def get_run_time(self):
        return self._run_time

    def get_raw_parameter(self, key):
        '''There are a number of 'header' fields in the .spe files
        this function will return the array containing each row (or line)
        under that header. Each row is a string type array element.
        '''
        try:
            return self._raw_fields[key]
        except KeyError as e:
            print "The requested header ({0}) does not appear in the datafile. Available options are:".format(key)
            for k in self._raw_fields:
                print k
            raise e

