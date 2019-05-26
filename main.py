import sys, io, os, json, glob
from math import atan 
import numpy as np
from PIL import Image
import cv2
import xlwt
import zipfile


class Marksheet:
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
                image = np.rot90(image, 3)
            else:
                image = np.rot90(image, 1)
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
            avg = np.mean(levels, axis=axis, keepdims=True)
            binary = (levels < avg - self.threshold) * 1

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
    # Read Setting
    setting_json = 'setting.json'
    if os.path.exists(setting_json):
        with open(setting_json, 'r') as f:
            option = json.load(f)
    tmp_image_path = option["tmp_image_path"]
    img_ext_list = option["img_ext_list"]

    fields = []
    for idx,recode in enumerate(option["recodes"]):
        if recode["fields"][0]=="type":
            type_idx = idx
        else:
            fields.extend(recode["fields"])

    values = []
    has_score = False
    has_answer = False

    # Read PDF file
    os.makedirs(tmp_image_path, exist_ok=True)
    root, ext = os.path.splitext(input_file)
    if ext in ['.pdf', '.PDF']:
        os.system("pdfimages -j -jp2 " + input_file + " ./images/img")
    elif ext in ['.zip', '.ZIP']:
        with zipfile.ZipFile(input_file) as existing_zip:
            existing_zip.extractall(tmp_image_path)
    img_files = []
    for ext in img_ext_list:
        img_files.extend(glob.glob(os.path.join(tmp_image_path, "./**/*." + ext), recursive=True))
    img_files = sorted(img_files)
    
    for img_file in img_files:
        image = Image.open(img_file).convert("RGB")

        marksheet = Marksheet()
        marksheet.load_pdf_image(np.array(image), option["sheet"])
        marksheet.calibration(option["calibration"])
        value = marksheet.recognition(option["recodes"])
        type = value.pop(type_idx)
        if type == option["answer"]["score_id"]:
            scores = value
            has_score = True
        elif type == option["answer"]["answer_id"]:
            answers = value
            has_answer = True
        else:
            values.append(value)

    os.system("rm -rf " + os.path.join(tmp_image_path, "*"))


    book = xlwt.Workbook()
    sheet = book.add_sheet('sheet1')

    if has_score and has_answer:
        fields.insert(option["answer"]["score_field_idx"], "score")
    write1d_to_excel(sheet, 0, 0, fields)

    for idx, row in enumerate(values):
        if has_score and has_answer:
            total_score = 0
            for value,answer,score in zip(row, answers, scores):
                if score!=-1 and value==answer:
                    total_score += score
            row.insert(option["answer"]["score_field_idx"], total_score)        
        write1d_to_excel(sheet, idx+1, 0, row)
    book.save(output_file)

if __name__ == "__main__":
    if len(sys.argv)==3:
        main(sys.argv[1],sys.argv[2])
    else:
        main("file.zip","out.xls")
