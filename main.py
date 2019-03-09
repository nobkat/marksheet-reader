import PyPDF2
import io
from PIL import Image
import numpy as np
import cv2
from math import atan 

pdf = PyPDF2.PdfFileReader('test.pdf')

mark_img = cv2.imread('mark.png')
marks=((169,15),(13,95)) # (x,y) [mm]
r = 10 # search radius [mm]
mark_dpi = 600
box = (131, 27.5,  171, 92.5)
rows = 13
columns = 10
coeff=1.5

for p, page in enumerate(pdf.pages):
    xObject = page['/Resources']['/XObject'].getObject()
    print(len(xObject))
    for obj in xObject:
        if xObject[obj]['/Subtype'] != '/Image' or xObject[obj]['/Filter'] != '/DCTDecode':
            continue
        im = Image.open(io.BytesIO(xObject[obj]._data))
        imdata = np.asarray(im)
        if imdata.shape[0]>imdata.shape[1]: # portrait
            dpm = imdata.shape[0] / 257 #dot per mm
            corner = int(6 * dpm)
            if np.average(imdata[:corner,:corner,:])>np.average(imdata[-corner:,-corner:,:]):
                im = im.rotate(180, expand=True)
        else:
            dpm = imdata.shape[1] / 257 #dot per mm
            corner = int(6 * dpm)
            if np.average(imdata[-corner:,:corner,:])<np.average(imdata[:corner,-corner:,:]):
                im = im.rotate(-90, expand=True)
            else:
                im = im.rotate(90, expand=True)
        im.save(str(p)+'.jpg')
        im = np.array(im)

    mark_img_resized = cv2.resize(mark_img, dsize=None, fx= (dpm * 25.4)/600, fy= (dpm * 25.4)/600)

    mark_pos_x=[]
    mark_pos_y=[]
    for mark in marks:
        x1 = int((mark[0]-r)*dpm)
        y1 = int((mark[1]-r)*dpm)
        x2 = int((mark[0]+r)*dpm)
        y2 = int((mark[1]+r)*dpm)
        result = cv2.matchTemplate(im[y1:y2,x1:x2,:], mark_img_resized, cv2.TM_CCOEFF_NORMED)
        max_point = np.unravel_index(np.argmax(result), result.shape)
        print((max_point[1]+x1)/dpm, (max_point[0]+y1)/dpm)
        mark_pos_x.append(max_point[1]+x1+mark_img_resized.shape[1]/2)
        mark_pos_y.append(max_point[0]+y1+mark_img_resized.shape[0]/2)

    dx = (mark_pos_x[0]-marks[0][0]*dpm)
    dy = (mark_pos_y[0]-marks[0][1]*dpm)
    print(dx,dy)
    im_box = im[int(box[1]*dpm+dy):int(box[3]*dpm+dy),int(box[0]*dpm+dx):int(box[2]*dpm+dx),:]
    w = im_box.shape[1]
    h = im_box.shape[0]
    mw = w/columns/4
    mh = h/rows/4

    values = np.zeros((rows,columns))
    for y in range(rows):
        for x in range(columns):
            cell = im_box[
                int(h*y/rows+mh):
                int(h*(y+1)/rows-mh),
                int(w*x/columns+mw):
                int(w*(x+1)/columns-mw)
                ,1]
            values[y,x] = np.average(cell) 
    std = np.std(values)
    avg = np.average(values)
    print((values<avg-std*coeff)*1)

    cv2.imshow("test",im_box)
    cv2.waitKey(0)


