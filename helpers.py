import datetime as dt
from numpy import random
import string
from cryptography.fernet import Fernet
import os


key = os.environ.get("KPASEC_KEY").encode()

def encrypt_text(plain_text, key=key):
    f = Fernet(key)
    encrypted_text = f.encrypt(bytes(plain_text, "UTF-8"))
    return encrypted_text.decode()


def decrypt_text(encrypted_text, key=key):
    f = Fernet(key)
    return f.decrypt(bytes(encrypted_text,"UTF-8")).decode()

def inside(ch):
    data = [i for i in string.ascii_lowercase] + [' '] + [str(i) for i in range(10)]
    return ch.lower() in data 

def inside2(ch):
    data = ['+'] + [str(i) for i in range(10)]
    return ch.lower() in data 

def date_transform(start1,end1):
    start = dt.datetime.strptime(start1, "%Y-%m-%d").date()
    start = dt.date(year=start.year, month=start.month, day=start.day)
    end =  dt.datetime.strptime(end1, "%Y-%m-%d").date() + dt.timedelta(1)
    end = dt.date(year=end.year, month=end.month, day=end.day)
    return start, end

def date_transform2(start1,end1):
    #start = dt.datetime.strptime(start1, "%Y-%m-%d").date()
    start = dt.date(year=start1.year, month=start1.month, day=start1.day)
    end =  end1 + dt.timedelta(1)
    end = dt.date(year=end.year, month=end.month, day=end.day)
    return start, end


def generate_receipt_no():
    today = dt.datetime.now()
    if today.month == 1 and today.day == 1:
        name = f"nums{today.year}.txt"
        newf = open(name, "a")
    y1 = str(dt.datetime.now().year) + str(dt.datetime.now().month)
    name = "nums2022.txt"
    rand = random.randint(10000, 100000)
    newf = open(name, "a")
    file = open(name, "r")
    idx = y1+str(rand)
    read = file.read()
    file.close()
    if idx not in read:
        with open(name, "a") as f1:
            f1.write(f"{idx}\n")
        return idx



def generate_student_id(contact, firstname):
    firstname = str(firstname).lower()
    res = str(contact) + firstname
    return res



def promote_student(current_class):
    index = int(current_class[0])
    if index < 3:
        index += 1
        return str(index) + current_class[1:]
    else:
        return False


def sort_dict_values(dd2):
    marklist = sorted(dd2.items(), key=lambda x:x[1])
    sortdict = dict(marklist)
    return sortdict