# unscanny
A Python program for time series imaging using flatbed scanners


## Goals

Time series imaging of pinned colonies growing on solid agar plates, using readily available flatbed scanner, is becoming an increasingly popular (REFs) approach for high-throughput phenotyping in microbial genetics and genomics.

With `unscanny` we aim to provide a simple yet flexible program and associated library, for carrying out scanner based time series imaging on Linux and OS X, using SANE compatible scanners. The framework was written with the Epson V700/800 series of scanners in mind (which is what we use in our laboratory), but there is (hopefully) little code that is specific to this particular devices. 

## Philosophy

Laboratory experiments that involve computing should, as much as possible, be self documenting. 

Running an experiment in `unscanny` requires two input files that describe key parameters of your scanning experiment:

1. scanner settings such as mode, resolution, etc
2. run setting such as number of scans, time between scans, etc
    
`unscanny` has two subcommands -- `setrun` and `setscanner` to help create YAML files with the required parameters. In addition, `unscanny` creates a log file after the run is completed with information on messages and errors that occured during the run.


## Requirements

* Numpy/Scipy -- the standard Python numerical analysis stack

* SANE -- [Python SANE module](https://github.com/python-pillow/Sane) and the appropriate SANE backends (`libsane` and `libsane-dev` on Debian/Ubunut systems)

* Curses -- the standard Python curses library plus [pick](https://github.com/wong2/pick), a module for choosing items using a curses interface.

* [Click](http://click.pocoo.org/) - A Python library for building command-line interfaces

* TIFF -- the library [tifffile](https://github.com/blink1073/tifffile) provides support for 16 bit TIFF images, embedding tags, etc.


## Usage

`unscanny --help` will show you the available commands. Each sub-command has it's own help page as well, e.g. `unscanny runit --help` will show you the help page for the `runit` sub-command.   
