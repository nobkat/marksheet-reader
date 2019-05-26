# Installation

Apache and flask
```
$ sudo apt-get install apache2 apache2-dev 
$ sudo pip3 install Flask
$ sudo apt install libapache2-mod-wsgi-py3 
$ sudo pip install mod-wsgi
$ sudo pip3 install mod-wsgi
$ sudo pip install flask
$ sudo pip3 install flask
```

Requiremets for python
```
pip3 install numpy pillow pdf2image xlwt
pip3 install opencv-python
sudo apt-get install libsm-dev
sudo apt-get install libxrender
sudo apt-get install libxext-dev
sudo apt-get install poppler-utils
```

```
$ sudo mod_wsgi-express install-module
LoadModule wsgi_module "/usr/lib/apache2/modules/mod_wsgi-py27.so"
WSGIPythonHome "/usr"
```

Add the following to /etc/apache2/apache2.conf

```
LoadModule wsgi_module "/usr/lib/apache2/modules/mod_wsgi-py27.so"
WSGIPythonHome "/usr"
```

Restart Apache
```
sudo apache2ctl start
sudo apache2ctl stop
sudo apache2ctl restart
```

# Settigs of Apache
```
/etc/apache2/...
```



Flask
```sudo vim  /etc/apache2/sites-enabled/flask.conf```

References for flask

https://blog.akashisn.info/entry/%3Fp%3D258


# Usage

```
python3 main.py input_file output_file
```
input_file is pdf file and output_file is xls file. (not xlsx file)


# Deploy
```
(local)$ ssh [servername]
$ cd /var/www/test
$ sudo -uwww-data git clone git@github.com:nobkat/marksheet-reader.git marksheet
$ sudo apache2ctl restart
```

# Update
```
(local)$ ssh [servername]
$ cd /var/www/app/marksheet
$ sudo -uwww-data git pull
$ sudo apache2ctl restart
```



