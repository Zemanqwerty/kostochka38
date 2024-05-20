__author__ = 'Vanger'
from subprocess import Popen, PIPE

Popen("chmod 777 -R /var/www/vanger/data/email/kostochka38.ru/price_zooirkutsk/.maildir/new/", shell=True, stdin=PIPE,
      stdout=PIPE).stdout.read().split()
