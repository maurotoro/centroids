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
from skimage.transform import rotate, resize
from skimage.segmentation import clear_border

from Tkinter import Label, Frame, Canvas, BOTH, NW, Button, RIGHT, BOTTOM, LEFT, RAISED
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
    clBrd=corte < .7
    colab=label(-clBrd,background=0)
    colab+=1
    centroids, borders, props = [],[],[]
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
        cent=[region.centroid[1],region.centroid[0]]
        centroids.append(cent)
        borders.append([minc,maxc])
        props.append(region)
    centroids.sort(key=lambda x: x[0])
    borders.sort(key=lambda x: x[0])
    props.sort(key=lambda x: x.centroid[1])
    return colab, centroids, borders, props
    
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
    if np.shape(colegial)[0] > 2400:
        colegial=colegial[:2214,:]
        colegial=resize(colegial, [1076,826], order=2)
        colegial=colegial<.9
        colegial=colegial-1
        colegial=colegial*-255
    cole=(colegial < .9)    
    col=closing(cole, square(3))
    clear_border(col)
    colab = label(col, background=0)
    colab+=1; prmCorte=[]
    A=[regionprops(colab)[x].area
       for x in range(len(np.unique(colab))-1)]
    limA=[int(np.mean(x)+(np.std(x)/np.sqrt(len(x)))*4)
       for x in [A]]    
    for reg in regionprops(colab):
        if reg.area < limA:
            continue
        if len(np.unique(reg)) < 1:
            continue
        angle=np.rad2deg(reg.orientation)
        y0,x0,y1,x1=reg.bbox
        rotedLab=rotate((col[y0:y1,x0:x1]*1.0), mode= 'constant',cval=0.0, angle=-angle)
        prmCorte.append(rotedLab)
    tmp=prmCorte[-3].copy()
    prmCorte[-3]=prmCorte[-2]
    prmCorte[-2]=tmp
    if np.shape(skimread(fpath, as_grey=True ))[0] >2400:
        tmp=prmCorte.pop(9)
        prmCorte.insert(7,tmp)
    [clear_border(prmCorte[x]) for x in range(len(prmCorte))]
    prmCorte=[cut for cut in prmCorte if len(np.unique(cut)) > 1]  
  
#    prmCorte=[-prmCorte[x] for x in range(len(prmCorte))]
    return prmCorte
class MyImage(Frame):
    def __init__ (self,solved,master = None):
        Frame.__init__(self, master)
        self.colab, self.centroids, self.borders, self.props = solved
        self.rgbcolab=label2rgb(self.colab, bg_label=0, bg_color=[.7,.7,.7])
        skimsave('tmp.png', self.rgbcolab)
        self.im=Image.open('tmp.png')        
        self.pic = ImageTk.PhotoImage(self.im)
        self.initUI()
        
    def initUI(self):
        '''
            given the Frame, creates a canvas, puts the solved image, and
            adds the rectangles and circles to mark the elements and centroids

            Still needs to take mouse events, select the closest rectangle,
            and put a new one depending on mouse press and release
            ...easybreazy...
        '''
        self.pack(fill=BOTH, expand=1)
        frame = Frame(self, relief=RAISED, borderwidth=1)
        frame.pack(fill=BOTH, expand=1)

        self.canvas = Canvas(self, width=self.im.size[0], height=self.im.size[1])
        canvas=self.canvas
        boxes=[(canvas.canvasx(x.bbox[1]), canvas.canvasx(x.bbox[2]),
                canvas.canvasx(x.bbox[3]), canvas.canvasx(x.bbox[0])) for x in self.props]

        canvas.create_image(0,0,anchor=NW, image=self.pic)
        #imbox=canvas.bbox(imID)
        self.rects = [canvas.create_rectangle(x[0], x[1], x[2],x[3] , 
                        fill=None, outline='red') for x in boxes]
        self.ellis = [canvas.create_oval((x[0]-2,x[1]-2,x[0]+2,x[1]+2),
                        fill='green',outline='green') for x in self.centroids]
        if len(self.rects) > 5:
            [canvas.delete(x) for x in self.rects[5:]]
        if len(self.ellis) > 5:
            [canvas.delete(x) for x in self.ellis[5:]]
        canvas.pack(fill=BOTH, expand=1)
        
        denButton = Button(self, text="Denny", command=self.diy)
        denButton.pack(side=RIGHT)
        accButton = Button(self, text="Accept")
        accButton.pack(side=LEFT)
        quiButton = Button(frame, text="quit")
        quiButton.pack(side=RIGHT)
        
    def diy(self):
        [self.canvas.delete(x) for x in self.ellis]
        [self.canvas.delete(x) for x in self.rects]
        butP=self.canvas.bind("<Button-1>", self.press)
        butR=self.canvas.bind("<ButtonRelease-1>", self.release)
    def press(self,event):
        print (event.x,event.y)
        self.x0=event.x
        self.y0=event.y
        pass
    def release(self,event):
        print (event.x,event.y)
        self.x1=event.x
        self.y1=event.y
        self.centx=np.sort([self.x0,self.x1])
        self.centy=np.sort([self.y0,self.y1]) 
        img=self.colab[self.centy[0]:self.centy[1],self.centx[0]:self.centx[1]]>0
        mx=np.max(img)
        print img*1
        self.prop=regionprops(img)
        self.centc=[self.prop[0].centroid[1]+self.centx[0],
                   self.prop[0].centroid[0]+self.centy[0]]
        self.center=self.centc
        self.minr, self.minc, self.maxr, self.maxc = self.prop[0].bbox
        print self.centc
        
    
def makeImg(solved):
    '''
        Takes one solved object and draws boxes and centroids over the labeled 
        image

        Still have to work on it...a lot...
    '''
    colab, centroids, borders, props = solved
    rgbcolab=label2rgb(colab, bg_label=0, bg_color=[.7,.7,.7])
    skimsave('tmp.png', rgbcolab)
    im=Image.open('tmp.png')
    draw=ImageDraw.Draw(im)
    boxes=[(props[x].bbox[1],props[x].bbox[0],props[x].bbox[3],props[x].bbox[2])  for x in range(len(props))]
    [draw.rectangle(x, fill=None, outline=(255,0,0)) for x in boxes]
    [draw.ellipse((x[0]-2,x[1]-2,x[0]+2,x[1]+2), fill=(0,255,0),outline=(0,255,0)) for x in centroids]
    #im.save(str('tmpB.png'))
    return im
#
#if __name__ == "__main__":
#    ims=[]
#    for d, s, f in os.walk('.'):
#        for x in [u for u in f if '.png' in u.lower()]:
#            ims.append(os.path.join(d,x))
#    ims.sort()
#    dr=os.getcwd()
#    names=[ims[x].split('/')[-1] for x in range(len(ims))]
#    prmCorte=[None]*len(ims)
#    prmCorte=[ovalize(im) for im in ims]
#    for y, cortes in enumerate(prmCorte):
#        solution =[autoOvalSolver(z) for z in cortes]
#        resIm=[makeImg(z) for z in solution]
#        nIms=Image.new('RGB', (600,950))
#        posy=range(0,950,190)
#        [nIms.paste(img, (0,x)) for img,x in zip(resIm[0:10:2],posy)]
#        [nIms.paste(img, (300,x)) for img,x in zip(resIm[1:10:2],posy)]
#        nIms.save(dr+'/tmp/'+names[y]+'.png')
#        
