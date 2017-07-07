from __future__ import print_function

import numpy as np

import matplotlib
matplotlib.use('qt5agg')
from matplotlib.widgets import RectangleSelector, Button
import matplotlib.pyplot as plt

from skimage import (transform, io)

import click
import yaml



def subdivide_region(shape_or_bbox, nrows=2, ncols=2):
    """Divide image of given height,width into subregions."""
    
    def bboxes_from_boundaries(rows, cols):
        nr, nc = len(rows), len(cols)
        bboxes = []
        for i in range(nr - 1):
            for j in range(nc - 1):
                b = list(zip(rows[i:i + 2], cols[j:j + 2]))
                bboxes.append((b[0][0], b[0][1], b[1][0], b[1][1]))
        return bboxes    

    if len(shape_or_bbox) == 2:
        minr, minc = 0, 0
        maxr, maxc = shape_or_bbox
    else:
        minr, minc, maxr, maxc = shape_or_bbox

    rstep = int((maxr-minr)/float(nrows))
    cstep = int((maxc-minc)/float(ncols))
    rows = minr + (np.arange(nrows + 1) * rstep)
    cols = minc + (np.arange(ncols + 1) * cstep)
    bboxes = bboxes_from_boundaries(rows, cols)
    return bboxes


class PersistentRectangleSelector(RectangleSelector):
    def release(self, event):
        super(PersistentRectangleSelector, self).release(event)
        self.to_draw.set_visible(True)
        self.canvas.draw()


class SelectorCollection(object):
    current = 0
    selectors = []
    rows = 2
    cols = 2
    normalized = True
    outfile = None
    colors = []

    def select_callback(self, eclick, erelease):
        'eclick and erelease are the press and release events'
        x1, y1 = eclick.xdata, eclick.ydata
        x2, y2 = erelease.xdata, erelease.ydata

    def choose_selector(self, event):
        nselectors = len(self.selectors)
        if event.key in [str(i) for i in range(1, nselectors+1)]:
            self.current = int(event.key) - 1
            self.activate_current()
        [i.update() for i in self.selectors]

    def _update_selector(self, i, interactive):
        xmin, xmax, ymin, ymax = self.selectors[i].extents
        newselector = PersistentRectangleSelector(
            self.selectors[i].ax, 
            self.select_callback,
            drawtype='box', 
            useblit=False,
            button=[1],
            minspanx=5, minspany=5,
            spancoords='data',
            rectprops = dict(facecolor=self.colors[i], 
                             alpha=0.5),
            interactive = interactive)
        newselector.extents = (xmin, xmax, ymin, ymax)
        return newselector        

    def activate_current(self):
        self.selectors[self.current].set_visible(False)  
        self.selectors[self.current] = self._update_selector(self.current, True) 
        self.selectors[self.current].set_visible(True)                
        self.selectors[self.current].set_active(True) 
        for i in range(len(self.selectors)):
            if i == self.current: 
                continue
            self.selectors[i].set_visible(False) 
            self.selectors[i] = self._update_selector(i, False)    
            self.selectors[i].set_visible(True)               
            self.selectors[i].set_active(False)           
        plt.title("Current Selection: {}".format(self.current + 1))

    def normalize_geometry(self):
        def width(selector):
            xmin, xmax, _, _ = selector.extents
            return xmax - xmin
        def height(selector):
            _, _, ymin, ymax = selector.extents
            return ymax - ymin
        maxW = max([width(i) for i in self.selectors])
        maxH = max([height(i) for i in self.selectors])
        for selector in self.selectors:
            xmin, _, ymin, _ = selector.extents
            selector.extents = (xmin, xmin + maxW, ymin, ymin + maxH)

    def normalize_and_update(self, event):
        self.normalize_geometry()
        [i.update() for i in self.selectors]

    def write_geometry(self, event):
        if self.normalized:
            self.normalize_geometry()
        d = {}
        for i, selector in enumerate(self.selectors):
            pstr = "Region{:03d}".format(i + 1)
            d[pstr] = {}
            xmin, xmax, ymin, ymax = selector.extents
            d[pstr] = dict(xmin = int(xmin), xmax=int(xmax), 
                           ymin = int(ymin), ymax=int(ymax))
        yaml.safe_dump(d, self.outfile,
            default_flow_style=False,
            encoding = "utf-8")
        plt.close("all")

    


@click.command()
@click.option("-r", "--rows",
              help = "Number of rows of ROIs",
              type = click.IntRange(1,4),
              default = 2)
@click.option("-c", "--cols",
              help = "Number of columns of ROIs",
              type = click.IntRange(1,4),
              default = 2)
@click.option("--normalized/--not-normalized", default=True,
              help = "Make ROIs uniform in size.")
@click.argument("image_file",  
                type = click.Path(exists=True))
@click.argument("outfile",  
                type = click.File("w"),
                default = "-")
def main(image_file, outfile, rows, cols, normalized):
    """Define regions of interest (ROIs) on an image,
    and return the bounding boxes of those ROIs. Assumes
    a grid of ROIs, but no constraints on ROI overlap.
    
    Returned bounding boxes are returned in YAML format for easy
    parsing. See extractROI for a program that operates on ROIs.
    
    """
    img = np.squeeze(io.imread(image_file))    
    fig, main_ax = plt.subplots()  
    plt.subplots_adjust(bottom = 0.2)      
    main_ax.imshow(img, cmap="gray") 

    nplates = rows * cols
    irows, icols = img.shape

    selections = SelectorCollection()
    selections.outfile = outfile
    selections.rows = rows
    selections.cols = cols 
    selections.normalized = normalized
    selections.colors = plt.cm.tab10(np.linspace(0, 1, nplates)) 
    selections.selectors = \
        [PersistentRectangleSelector(
            main_ax, 
            selections.select_callback,
            drawtype='box', 
            useblit=False,
            button=[1],
            minspanx=5, minspany=5,
            spancoords='data',
            rectprops = dict(facecolor=selections.colors[i],alpha=0.5),
            interactive=True) 
         for i in range(nplates)]

    bboxes = subdivide_region((irows,icols), rows, cols)

    for i, bbox in enumerate(bboxes):
        minr, minc, maxr, maxc = bbox
        selections.selectors[i].extents = (minc, maxc, minr, maxr)
        selections.selectors[i].set_visible(True)

    selections.current = 0
    selections.activate_current()

    ax_normalize = plt.axes([0.45, 0.05, 0.2, 0.075])
    btn_normalize = Button(ax_normalize, "Normalize")
    btn_normalize.on_clicked(selections.normalize_and_update)    

    ax_apply = plt.axes([0.7, 0.05, 0.2, 0.075])
    btn_apply = Button(ax_apply, "Apply and Close")
    btn_apply.on_clicked(selections.write_geometry)    


    plt.connect('key_press_event', selections.choose_selector)
    plt.sca(main_ax)
    plt.show()



if __name__ == "__main__":
    main()
