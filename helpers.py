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
    data = [i for i in string.ascii_lowercase] + [' ']
    return ch.lower() in data 

def date_transform(start1,end1):
    start = dt.datetime.strptime(start1, "%Y-%m-%d").date()
    start = dt.date(year=start.year, month=start.month, day=start.day)
    end =  dt.datetime.strptime(end1, "%Y-%m-%d").date() + dt.timedelta(1)
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



def generate_student_id(contact, dob):
    date_of_birth = str(dob)
    date_of_birth = date_of_birth.replace("-","")
    res = str(contact) + str(date_of_birth)
    return res



def promote_student(current_class):
    index = int(current_class[0])
    if index < 3:
        index += 1
        return str(index) + current_class[1]
    else:
        return False