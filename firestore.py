
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
import datetime
import os
import json

data = {
  "type": "service_account",
  "project_id": "kpasecsystem",
  "private_key_id": os.environ.get('private_key_id'),
  "private_key": os.environ.get('private_key').replace("\\n",'\n'),
  "client_email": os.environ.get('client_email'),
  "client_id": os.environ.get('client_id'),
  "auth_uri": os.environ.get('auth_uri'),
  "token_uri": os.environ.get('token_uri'),
  "auth_provider_x509_cert_url": os.environ.get('auth_provider_x509_cert_url'),
  "client_x509_cert_url": os.environ.get('client_x509_cert_url')
}



cred = credentials.Certificate(data)
firebase_admin.initialize_app(cred)
db = firestore.client()


def add_student(id, clerk, date_ad, fullname, class1, p_phone, phone, idx, dob):
	db.collection('Student').add({
	'id': id,
	'date': str(datetime.datetime.utcnow()),
	'dob':str(dob),
	'clerk': clerk,
	'date_admitted':str(date_ad),
	'fullname':fullname,
	'class':class1,
	'parent_contact':p_phone,
	'phone':phone,
	'id_number':idx,
	'status':True
	})

def add_etl_payment(id, clerk, payer,amount, tx_id, semester, mode, category, name, type1):
	db.collection('ETLIncome').add({
	'id': id,
	'date': str(datetime.datetime.utcnow()),
	'payer':payer,
	'clerk': clerk,
	'amount':amount,
	'tx_id':tx_id,
	'semester':semester,
	'mode':mode,
	'category':category,
	'name':name,
	'type1':type1
	})


def add_pta_payment(id, clerk, payer,amount, tx_id, semester, mode, category, name, type1):
	db.collection('PTAIncome').add({
	'id': id,
	'date': str(datetime.datetime.utcnow()),
	'payer':payer,
	'clerk': clerk,
	'amount':amount,
	'tx_id':tx_id,
	'semester':semester,
	'mode':mode,
	'category':category,
	'name':name,
	'type1':type1
	})

def add_pta_expense(id, clerk, detail, semester, mode, category, quantity, totalcost):
	db.collection('PTAExpense').add({
	'id': id,
	'date': str(datetime.datetime.utcnow()),
	'clerk': clerk,
	'detail':detail,
	'semester':semester,
	'mode':mode,
	'category':category,
	'quantity':str(quantity),
	'totalcost':str(totalcost)
	})

def add_etl_expense(id, clerk, detail, semester, mode, category, quantity, totalcost):
	db.collection('ETLExpense').add({
	'id': id,
	'date': str(datetime.datetime.utcnow()),
	'clerk': clerk,
	'detail':detail,
	'semester':semester,
	'mode':mode,
	'category':category,
	'quantity':str(quantity),
	'totalcost':str(totalcost)
	})

