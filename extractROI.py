from __future__ import print_function
import collections
import glob, os, os.path
import warnings

import numpy as np
from skimage import (transform, io, exposure, util)

import click
import yaml

import tifffile as TIFF



class Settings(collections.MutableMapping):
    def __init__(self, **entries):
        self.__dict__.update(entries)

    def __repr__(self):
        return str(self.__dict__)

    def __iter__(self):
        return self.__dict__.__iter__()

    def __len__(self):
        return len(self.__dict__)

    def __getitem__(self, key):
        return self.__dict__[key]

    def __setitem__(self, key, value):
        self.__dict__[key] = value

    def __delitem__(self, key):
        del self.__dict__[key]


def load_config(fname):
    """YAML file name, section string -> Settings object.
    """
    with open(fname, "r") as f:
        config = yaml.safe_load(f)
        return {key: Settings(**value) for (key,value) in config.iteritems()}

def equalize_from_ROI(img, region):
    mask = np.zeros(img.shape)
    mask[region.ymin:region.ymax, region.xmin:region.xmax] = 1
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
        eqlzd = util.img_as_uint(exposure.equalize_hist(img, mask = mask))
    return eqlzd


def extract_region(img, xmin, xmax, ymin, ymax):
    return img[ymin:ymax, xmin:xmax]


@click.command()
@click.argument("infile", 
    type = click.Path(exists=True))
@click.argument("indir",  
    type = click.Path(exists=True,
            file_okay = False,
            dir_okay = True))
@click.argument("outdir",  
    type = click.Path(exists=True,
            file_okay = False,
            dir_okay = True))
@click.option("-e", "--extension",
    help = "File extension type.",
    default = "*.tif")
@click.option("--equalize",
    type = click.Path(exists=True))
def main(infile, indir, outdir, equalize, extension):
    """Extract regions of interest from every image file in specified input directory,
    writing sub-images to output directory.
    """
    # get ROIs from YAML file
    regions = load_config(infile)
    infiles = glob.glob(os.path.join(indir,extension))

    # if equalization invoked
    if equalize:
        eqlz_region = load_config(equalize).values()[0]

    # Create output subdirectories
    region_names = regions.keys()
    for name in region_names:
        os.makedirs(os.path.join(outdir, name))

    # iterate over input files and subregions
    # putting out sub-image for each file
    for fname in infiles:
        basename = os.path.basename(fname)
        with open(fname, "r") as f:
            img = np.squeeze(io.imread(f))
            if equalize:
                img = equalize_from_ROI(img, eqlz_region)
            for (name, region) in regions.iteritems():
                subimg = extract_region(img,
                            region.xmin, region.xmax,
                            region.ymin, region.ymax)
                outfile = "{}-{}".format(name, basename)
                outname = os.path.join(os.path.join(outdir, name, outfile))
                TIFF.imsave(outname, subimg)




if __name__ == "__main__":
    main()



