Analysis
=========
This directory is home to analysis scripts to be run on data generated on the Boxerino testbench

rootify
========
A script to convert all the files in a directory with a given file extension to root histograms.

usage: Reads all spectrum files in a directory and creates histos
       [-h] [-e EXTENSION] in_dir out_dir

positional arguments:
  in_dir                directory containing .spe files to be processed
  out_dir               directory where root file will be created [./]

optional arguments:
  -h, --help            show this help message and exit
  -e EXTENSION, --extension EXTENSION
                        extension of files to be processed [.Spe]

