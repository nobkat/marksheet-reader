# requirements

pip3 install numpy pillow pdf2image xlwt
pip3 install opencv-python
sudo apt-get install libsm-dev
sudo apt-get install libxrender
sudo apt-get install libxext-dev
sudo apt-get install poppler-utils

# Usage

```
python3 main.py input_file output_file
````
input_file is pdf file and output_file is xls file. (not xlsx file)

#  Note
marksheet-reader が最新のコアのマークシート読み取りプログラム
marksheet-reader-server は実際のサーバーに入っているやつ(/var/www/app/marksheet/)よりも古いが，readme.mdが残されている。