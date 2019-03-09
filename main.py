import io, os, json
from math import atan 
import numpy as np
from PIL import Image
import cv2  ``
from pdf2image import convert_from_path
# needs ```brew install poppler

class Marksheet:
    def __init__(self):
        pass

    def load_pdf_image(self, image, sheet_option):
        width = sheet_option["width"]
        height = sheet_option["height"]
        self.threshold = sheet_option["threshold"]

        imdata = np.asarray(image)
        if imdata.shape[0]>imdata.shape[1]: # portrait
            self.dpm = imdata.shape[0] / height #dot per mm
            c = int(sheet_option["corner_size"] * self.dpm)
            if np.average(imdata[:c,:c,:])>np.average(imdata[-c:,-c:,:]):
                image = image.rotate(180, expand=True)
        else:
            self.dpm = imdata.shape[1] / height #dot per mm
            c = int(sheet_option["corner_size"] * self.dpm)
            if np.average(imdata[-c:,:c,:])<np.average(imdata[:c,-c:,:]):
                image = image.rotate(-90, expand=True)
            else:
                image = image.rotate(90, expand=True)
        self.image = np.array(image)

    def calibration(self, cal_option):
        marker_dpi = cal_option["marker_dpi"]
        img = cv2.imread(cal_option["marker_file"])
        marker_img = cv2.resize(img, dsize=None, fx=(self.dpm * 25.4)/marker_dpi, fy=(self.dpm * 25.4)/marker_dpi)
        (marker_h, marker_w, _) = marker_img.shape
        marks_pos = cal_option["pos"]        
        window = cal_option["window"]


        self.mark_pos_x=[]
        self.mark_pos_y=[]

        for mark_pos in marks_pos:
            x1 = int((mark_pos["x"]-window)*self.dpm)
            y1 = int((mark_pos["y"]-window)*self.dpm)
            x2 = int((mark_pos["x"]+window)*self.dpm)
            y2 = int((mark_pos["y"]+window)*self.dpm)
            result = cv2.matchTemplate(self.image[y1:y2,x1:x2,:], marker_img, cv2.TM_CCOEFF_NORMED)
            (x, y) = np.unravel_index(np.argmax(result), result.shape)
            self.mark_pos_x.append(x + x1 + marker_w/2)
            self.mark_pos_y.append(y + y1 + marker_h/2)

        self.dx = (self.mark_pos_x[0]-marks_pos[0]["x"]*self.dpm)
        self.dy = (self.mark_pos_y[0]-marks_pos[0]["y"]*self.dpm)
            
    def recognition(self, recodes_option):
        recodes = []
        for recode_option in recodes_option:
            box = recode_option["box"]
            cols = recode_option["cols"]
            rows = recode_option["rows"]
            axis = 0 if recode_option["direction"]=="down" else 1
        
            im_box = self.image[int(box[1]*self.dpm+self.dy):int(box[3]*self.dpm+self.dy),int(box[0]*self.dpm+self.dx):int(box[2]*self.dpm+self.dx),:]
            (h, w, _) = im_box.shape
            mw = w/cols/4
            mh = h/rows/4

            levels = np.zeros((rows, cols))
            for y in range(rows):
                for x in range(cols):
                    cell = im_box[
                        int(h*y/rows+mh):
                        int(h*(y+1)/rows-mh),
                        int(w*x/cols+mw):
                        int(w*(x+1)/cols-mw)
                        ,1]
                    levels[y,x] = np.average(cell) 
            std = np.std(levels)
            avg = np.average(levels)
            binary = (levels < avg - std*self.threshold) * 1

            values = np.array(recode_option["value"])[np.argmax(binary, axis=axis)]
            values[np.sum(binary, axis=axis)!=1]=-1

            if recode_option["multidigit"]==True:
                values = values[::-1]
                values_ = 0
                mul = 1
                for digit in values:
                    values_ += digit * mul
                    mul *= 10
                values = values_

            recodes.append({"tags": recode_option["tags"], "values": values})
        return recodes


if __name__ == "__main__":
    setting_json = 'setting.json'
    if os.path.exists(setting_json):
        with open(setting_json, 'r') as f:
            option = json.load(f)

    images = convert_from_path("test3.pdf")
    
    for image in images:
        marksheet = Marksheet()
        marksheet.load_pdf_image(image, option["sheet"])
        marksheet.calibration(option["calibration"])
        print(marksheet.recognition(option["recodes"]))
