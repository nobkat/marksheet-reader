import sys, io, os, json
from math import atan 
import numpy as np
from PIL import Image
import cv2
from pdf2image import convert_from_path
import xlwt
# needs ```brew install poppler

class Marksheet:
    def __init__(self):
        pass

    def load_pdf_image(self, image, sheet_option):
        width = sheet_option["width"]
        height = sheet_option["height"]
        self.threshold = sheet_option["threshold"]
        self.std_dpm = sheet_option["std_dpm"]

        if image.shape[0]>image.shape[1]: # portrait
            self.dpm = image.shape[0] / height #dot per mm
            c = int(sheet_option["corner_size"] * self.dpm)
            if np.average(image[:c,:c,:])>np.average(image[-c:,-c:,:]):
                image = np.rot90(image, 2)
        else:
            self.dpm = image.shape[1] / height #dot per mm
            c = int(sheet_option["corner_size"] * self.dpm)
            if np.average(image[-c:,:c,:])<np.average(image[:c,-c:,:]):
                image = np.rot90(image, 2)
            else:
                image = np.rot90(image, 3)
        self.image = image

    def calibration(self, cal_option):
        marker_dpi = cal_option["marker_dpi"]
        img = cv2.imread(cal_option["marker_file"])
        marker_img = cv2.resize(img, dsize=None, fx=(self.dpm * 25.4)/marker_dpi, fy=(self.dpm * 25.4)/marker_dpi)
        (marker_h, marker_w, _) = marker_img.shape
        marks_pos = np.array(cal_option["pos"])
        window = cal_option["window"]

        marks_pos_measured=[]

        for mark_pos in marks_pos:
            x1 = int((mark_pos[0]-window)*self.dpm)
            y1 = int((mark_pos[1]-window)*self.dpm)
            x2 = int((mark_pos[0]+window)*self.dpm)
            y2 = int((mark_pos[1]+window)*self.dpm)
            result = cv2.matchTemplate(self.image[y1:y2,x1:x2,:], marker_img, cv2.TM_CCOEFF_NORMED)
            (y, x) = np.unravel_index(np.argmax(result), result.shape)
            marks_pos_measured.append([(x + x1 + marker_w/2), (y + y1 + marker_h/2)])
        marks_pos_measured.append([
            marks_pos_measured[0][0]-(marks_pos_measured[1][1]-marks_pos_measured[0][1]),
            marks_pos_measured[0][1]+(marks_pos_measured[1][0]-marks_pos_measured[0][0])
            ])
        marks_pos = np.vstack((marks_pos,
            [marks_pos[0][0]-(marks_pos[1][1]-marks_pos[0][1]),
            marks_pos[0][1]+(marks_pos[1][0]-marks_pos[0][0])]
            )) * self.std_dpm
        M = cv2.getAffineTransform(np.array(marks_pos_measured, np.float32), np.array(marks_pos, np.float32))
        self.image = cv2.warpAffine(self.image, M, self.image.shape[1::-1])
    
    def recognition(self, recodes_option):
        recodes = []
        for recode_option in recodes_option:
            box = recode_option["box"]
            cols = recode_option["cols"]
            rows = recode_option["rows"]
            axis = 0 if recode_option["direction"]=="down" else 1
        
            im_box = self.image[int(box[1]*self.std_dpm):int(box[3]*self.std_dpm),int(box[0]*self.std_dpm):int(box[2]*self.std_dpm),:]
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
                if np.all(values!=-1):
                    values = values[::-1]
                    values_ = 0
                    mul = 1
                    for digit in values:
                        values_ += digit * mul
                        mul *= 10
                    values = np.array([values_])
                else:
                    values = np.array([-1])

            recodes.extend(values.tolist())
        return recodes


def write1d_to_excel(sheet, row, col, data):
    for i, val in enumerate(data):
        sheet.write(row, col+i, val) 

def main(input_file, output_file):
    setting_json = 'setting.json'
    if os.path.exists(setting_json):
        with open(setting_json, 'r') as f:
            option = json.load(f)

    images = convert_from_path(input_file)
    
    fields = []
    for recode in option["recodes"]:
        fields.extend(recode["fields"])
    book = xlwt.Workbook()
    sheet = book.add_sheet('sheet1')
    write1d_to_excel(sheet, 0, 0, fields)

    for idx, image in enumerate(images):
        marksheet = Marksheet()
        marksheet.load_pdf_image(np.array(image), option["sheet"])
        marksheet.calibration(option["calibration"])
        values = marksheet.recognition(option["recodes"])

        write1d_to_excel(sheet, idx+1, 0, values)

    book.save(output_file)

if __name__ == "__main__":

    main(sys.argv[1],sys.argv[2])
