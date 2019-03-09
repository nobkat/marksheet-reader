import PyPDF2
import io
import os
from PIL import Image
import numpy as np
import cv2
from math import atan 
import json



class Marksheet:
    def __init__(self):
        pass

    def load_pdf_image(self, image, sheet_option):
        width = sheet_option["width"]
        height = sheet_option["height"]

        imdata = np.asarray(image)
        if imdata.shape[0]>imdata.shape[1]: # portrait
            self.dpm = imdata.shape[0] / height #dot per mm
            corner = int(6 * self.dpm)
            if np.average(imdata[:corner,:corner,:])>np.average(imdata[-corner:,-corner:,:]):
                image = image.rotate(180, expand=True)
        else:
            self.dpm = imdata.shape[1] / height #dot per mm
            corner = int(6 * self.dpm)
            if np.average(imdata[-corner:,:corner,:])<np.average(imdata[:corner,-corner:,:]):
                image = image.rotate(-90, expand=True)
            else:
                image = image.rotate(90, expand=True)
        self.image = np.array(image)
    
    def calibration(self, cal_option):
        marker_img = cv2.imread(cal_option["marker_file"])
        marker_dpi = cal_option["marker_dpi"]
        window = cal_option["window"]

        marks_pos = cal_option["pos"]
        marker_img_resized = cv2.resize(marker_img, dsize=None, fx= (self.dpm * 25.4)/600, fy= (self.dpm * 25.4)/600)

        self.mark_pos_x=[]
        self.mark_pos_y=[]

        for mark_pos in marks_pos:
            x1 = int((mark_pos["x"]-window)*self.dpm)
            y1 = int((mark_pos["y"]-window)*self.dpm)
            x2 = int((mark_pos["x"]+window)*self.dpm)
            y2 = int((mark_pos["y"]+window)*self.dpm)
            result = cv2.matchTemplate(self.image[y1:y2,x1:x2,:], marker_img_resized, cv2.TM_CCOEFF_NORMED)
            max_point = np.unravel_index(np.argmax(result), result.shape)
            print((max_point[1]+x1)/self.dpm, (max_point[0]+y1)/self.dpm)
            self.mark_pos_x.append(max_point[1]+x1+marker_img_resized.shape[1]/2)
            self.mark_pos_y.append(max_point[0]+y1+marker_img_resized.shape[0]/2)

        self.dx = (self.mark_pos_x[0]-marks_pos[0]["x"]*self.dpm)
        self.dy = (self.mark_pos_y[0]-marks_pos[0]["y"]*self.dpm)
            
    def recognition(self):
        box = (131, 27.5,  171, 92.5)
        rows = 13
        columns = 10
        coeff=1.5
        
        print(self.dx,self.dy)
        im_box = self.image[int(box[1]*self.dpm+self.dy):int(box[3]*self.dpm+self.dy),int(box[0]*self.dpm+self.dx):int(box[2]*self.dpm+self.dx),:]
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


if __name__ == "__main__":
    setting_json = 'setting.json'
    if os.path.exists(setting_json):
        with open(setting_json, 'r') as f:
            option = json.load(f)
            sheet_option = option["sheet"]
            cal_option = option["calibration"]
            recodes_option = option["recodes"]

    pdf = PyPDF2.PdfFileReader("test.pdf")

    for p, page in enumerate(pdf.pages):
        xObject = page['/Resources']['/XObject'].getObject()
        print(len(xObject))
        for obj in xObject:
            if xObject[obj]['/Subtype'] != '/Image' or xObject[obj]['/Filter'] != '/DCTDecode':
                continue
            image = Image.open(io.BytesIO(xObject[obj]._data))
            
            marksheet = Marksheet()
            marksheet.load_pdf_image(image, option["sheet"])
            marksheet.calibration(option["calibration"])
            marksheet.recognition()

