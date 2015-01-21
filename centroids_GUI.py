# -*- coding: utf-8 -*-
"""
Created on Wed JAN 14:22:32 2015

@author: o0

try to solve some pics, then show em up one by one after clicks/closes

"""
import os
import numpy as np

from skimage.io import imread as skimread
from skimage.io import imsave as skimsave
from skimage.color import label2rgb
from skimage.morphology import closing, square
from skimage.measure import regionprops, label
from skimage.transform import rotate
from skimage.segmentation import clear_border

from Tkinter import Label, Frame
from PIL import Image, ImageTk, ImageDraw

def autoOvalSolver(corte):
    '''
        Takes the figure, finds the continuous regions and tries to get some
        boxes arroud the elements, not always works, but latter you'll decide
        about that.
        Works with the whole ovals and also cuts of it.
        
        Returns:
            the processed image:
                0 as background and every continuos regions as int,
                    sorted deppending on y position, yet...
            the bounding boxes of the regions that contain detectes elements
                [[minX, maxX], [minY,maxY]]
            the centroids of the areas
                [X,Y]
            the borders in X axis of the region
                [minX, maxX]
            the properties of the detected regions
                [region1, ..., regionN]
    ''' 
    clBrd=corte < 1
    colab=label(-clBrd,background=0)
    colab+=1
    boxes, centroids, borders, props = [],[],[],[]
    lettPos=[np.shape(corte)[1]/6,np.shape(corte)[0]/2]
    A=[regionprops(colab)[x].major_axis_length
       for x in range(len(np.unique(colab))-1)]
    B=[regionprops(colab)[x].minor_axis_length
       for x in range(len(np.unique(colab))-1)]
    C=[regionprops(colab)[x].area
       for x in range(len(np.unique(colab))-1)]    
    limA,limB,limC=[int(np.mean(x)+(np.std(x)/np.sqrt(len(x)))*3)
       for x in [A,B,C]]
    for region in regionprops(colab):
        minr, minc, maxr, maxc = region.bbox        
        if (((region.centroid[1] < lettPos[0]) and
            (region.centroid[0] < lettPos[1])) or
            #if the region its too near the upper left, it's probably the letter
            #(region.extent > 0.9) or
            #if the colored area it's too big, it may be pepper
            ((region.major_axis_length < limA) and
             (region.minor_axis_length > limB) and
             (region.area < limC)) #and
             #(region.extent > 0.7))
            #if the region it's too small, probably doesn't matter
            ):
            continue
        rect=zip([minc,minr],[maxc,maxr])
        cent=[region.centroid[1],region.centroid[0]]
        boxes.append(rect)
        centroids.append(cent)
        borders.append([minc,maxc])
        props.append(region)
    boxes.sort(key=lambda x: x[0][1])
    centroids.sort(key=lambda x: x[0])
    borders.sort(key=lambda x: x[0])
    props.sort(key=lambda x: x.centroid[1])
    return colab, boxes, centroids, borders, props
    
def ovalize(fpath):
    '''
    Takes a image, png ideally, and crops the 10 ovals out.
    Also it makes a good-enough job in image manipulation, so the prmCortes
    given are good enough to directly make the labels and start solving them.
    gives out the segmented areas, the ones that where rotated are a little 
    bigger that spected, but who cares that much about it?
    The resulting images are ordered by y axis appearence, so it's necessary to 
    reorder them...
    
    SKP 2014
    '''
    colegial=skimread(fpath, as_grey=True )           
    cole=(colegial < .9)    
    col=closing(cole, square(3))
    clear_border(col)
    colab = label(col, background=0)
    colab+=1; prmCorte=[]; origen=[]
    A=[regionprops(colab)[x].area
       for x in range(len(np.unique(colab))-1)]
    limA=[int(np.mean(x)+(np.std(x)/np.sqrt(len(x)))*4)
       for x in [A]]    
    for reg in regionprops(colab):
        if reg.area < limA:
            continue
        angle=np.rad2deg(reg.orientation)
        y0,x0,y1,x1=reg.bbox
        rotedLab=rotate((col[y0:y1,x0:x1]*1.0), mode= 'constant',cval=0.0, angle=-angle)
        rotedOr=rotate((cole[y0:y1,x0:x1]*1.0), mode= 'constant',cval=0.0, angle=-angle)
        prmCorte.append(rotedLab)
        origen.append(rotedOr)
    tmp=prmCorte[-3].copy(); tmpB=origen[-3].copy() 
    prmCorte[-3]=prmCorte[-2]; origen[-3]=origen[-2]
    prmCorte[-2]=tmp; origen[-2]=tmpB
    [clear_border(prmCorte[x]) for x in range(len(prmCorte))]
    [clear_border(origen[x]) for x in range(len(origen))]
#    prmCorte=[-prmCorte[x] for x in range(len(prmCorte))]
    return prmCorte

class MyImage(Frame):
    def __init__ (self,ipath,master = None):
        Frame.__init__(self, master)
        self.pack()
        self.ipath=ipath
        img = Image.open(self.ipath)       
        pic = ImageTk.PhotoImage(img)
        label = Label(self, image = pic)
        # Keep a reference!
        # (or dont and see what happens)
        label.image = pic
        label.pack()

def makeImg(solved):
    '''
        Takes one solved object and draws boxes and centroids over the labeled 
        image

        Still have to work on it...a lot...
    '''
    colab, boxes, centroids, borders, props = solved
    rgbcolab=label2rgb(colab, bg_label=0, bg_color=[.7,.7,.7])
    skimsave('tmp.png', rgbcolab)
    im=Image.open('tmp.png')
    draw=ImageDraw.Draw(im)
    boxes=[(props[x].bbox[1],props[x].bbox[0],props[x].bbox[3],props[x].bbox[2])  for x in range(len(props))]
    [draw.rectangle(x, fill=None, outline=(255,0,0)) for x in boxes]
    [draw.ellipse((x[0]-2,x[1]-2,x[0]+2,x[1]+2), fill=(0,255,0),outline=(0,255,0)) for x in centroids]
    #im.save(str('tmpB.png'))
    return im

if __name__ == "__main__":
    ims=[]
    for d, s, f in os.walk('.'):
        for x in [u for u in f if '.png' in u.lower()]:
            ims.append(os.path.join(d,x))
    ims.sort()
    names=[ims[x].split('/') for x in range(len(ims))]
    prmCorte=[None]*len(ims)
    prmCorte=[ovalize(im) for im in ims]
    for y, cortes in enumerate(prmCorte):
        solution =[autoOvalSolver(z) for z in cortes]
        resIm=[makeImg(z) for z in solution]
        nIms=Image.new('RGB', (600,950))
        posy=range(0,950,190)
        [nIms.paste(img, (0,x)) for img,x in zip(resIm[0:10:2],posy)]
        [nIms.paste(img, (300,x)) for img,x in zip(resIm[1:10:2],posy)]
        nIms.save(ims[y]+'.png')
#    a=[[None]*len(prmCorte)]*10
#    
#    prmCorte,ims=ovalize(fpath)
#    aut=autoOvalSolver(prmCorte[6])
#    makeImg(aut)
#    MyImage('tmpB.png').mainloop()
#    
#
#new_im=Image.new('RGB',(600,1000))
#posy=range(0,802,200)
#[new_im.paste(im, (0,x)) for im,x in zip(ims[0:10:2],posy)]
#[new_im.paste(im, (300,x)) for im,x in zip(ims[1:10:2],posy)]
