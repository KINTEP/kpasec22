from flask import Flask, render_template, flash, url_for, redirect, request, send_file, session, abort
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField, BooleanField, EmailField, SelectField, DateField, ValidationError
from wtforms.validators import DataRequired, Email, EqualTo, Length, NumberRange, InputRequired 
from datetime import datetime
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, login_user, current_user, logout_user, login_required
import requests
from numpy import cumsum, array, random
import uuid
import datetime as dt
from sqlalchemy.sql import extract
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
#import gspread
import string
from cryptography.fernet import Fernet
from num2words import num2words as n2w
from wtforms_sqlalchemy.fields import QuerySelectField
#from flask_migrate import Migrate
from sqlalchemy import or_, and_, func
import sqlite3
import pandas as pd
import os
from helpers import generate_student_id, generate_receipt_no, promote_student, date_transform, inside, inside2, encrypt_text, decrypt_text
from forms import (DonationForm,ClientSignUpForm, ClientLogInForm, ToDoForm, StudentPaymentsForm, ExpensesForm, ReportsForm, ChargeForm, SearchForm, StudentLedgerForm)
from wtforms import StringField, EmailField ,SubmitField, TextAreaField,DecimalField, PasswordField,IntegerField,  BooleanField, SelectField, DateField, ValidationError
from wtforms.validators import DataRequired, Email, EqualTo, Length, NumberRange, InputRequired 
from logging import FileHandler, WARNING
from sqlalchemy import create_engine
import click
from flask.cli import with_appcontext
import re




uri = os.environ.get('DATABASE_URL')
if uri.startswith("postgres://"):
    uri = uri.replace("postgres://", "postgresql://", 1)


app = Flask(__name__)

local = 'sqlite:///kpasec.db'
app.config['SQLALCHEMY_DATABASE_URI'] = uri
#app.config['SQLALCHEMY_BINDS'] = {"kpasec": "sqlite:///kpasec.db", "kpasecarchives":"sqlite:///kpasecarchives.db"}

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
local = 'sqlite:///client.db'
filehandler = FileHandler('errorlog.txt')
filehandler.setLevel(WARNING)

app.logger.addHandler(filehandler)
#migrate = Migrate(app, db)

#google_sheeet = gspread.service_account(filename="kpasec.json")
#main_sheet = google_sheeet.open("KpasecSystem")
#student_sheet = main_sheet.worksheet("StudentInfo")

def clerk_access():
	if not current_user.approval:
		return False
	if current_user.function == 'Accountant':
		return False
	if current_user.function == 'Clerk':
		return True


def account_access():
	if not current_user.approval:
		return False
	if current_user.function == 'Accountant':
		return True
	if current_user.function == 'Clerk':
		return False


@app.template_filter()
def currencyFormat(value):
	value = float(value)
	if value >= 0:
		return "{:,.2f}".format(value)
	else:
		value2 = "{:,.2f}".format(value)
		return "("+value2[1:]+")"

@app.template_filter()
def currencyFormat2(value):
	value = float(value)
	if value >= 0:
		return "{:,.2f}".format(value)
	else:
		value2 = "{:,.2f}".format(value)
		return value2[1:]



@app.template_filter()
def currencyFormat1(value):
	value = float(value)
	if value >= 0:
		value1 = "{:,.2f}".format(value)
		return value1 + " (CR)"
	else:
		value2 = "{:,.2f}".format(value)
		return value2[1:]+ " (DR)"


@login_manager.user_loader
def load_user(user_id):
	return User.query.get(int(user_id))


@app.route("/", methods = ['GET', 'POST'])
def home():
	if request.method == 'POST':
		if current_user.is_authenticated:
			if clerk_access():
				return redirect(url_for('clerk_dashboard'))
			if account_access():
				return redirect(url_for('accountant_dashboard'))
		else:
			return redirect(url_for('login'))
	return render_template("homepage1.html")


@app.route("/register_user", methods = ['GET', 'POST'])
def register_user():
	if current_user.is_authenticated:
		if clerk_access():
			return redirect(url_for('clerk_dashboard'))
		if account_access():
			return redirect(url_for('accountant_dashboard'))
	form = UserSignUpForm()
	if form.validate_on_submit():
		if request.method == "POST":
			username = form.data.get('username').strip()
			email = form.data.get('email').strip()
			password = form.data.get('password')
			function = form.data.get('function')
			hash_password = bcrypt.generate_password_hash(password).decode("utf-8")
			data = User(username=username, email=email, password=hash_password, function=function)
			db.session.add(data)
			db.session.commit()
		flash(f"Account successfully created for {form.username.data}", "success")
		return redirect(url_for("login"))
	return render_template("user_register.html", form=form)



@app.route("/login", methods = ['GET', 'POST'])
def login():
	if current_user.is_authenticated:
		if clerk_access():
			return redirect(url_for('clerk_dashboard'))
		if account_access():
			return redirect(url_for('accountant_dashboard'))
	form = UserLogInForm()
	if form.validate_on_submit():
		user = User.query.filter_by(email=form.email.data.strip()).first()
		if user and bcrypt.check_password_hash(user.password, form.password.data):
			login_user(user, remember=form.remember.data)
			next_page = request.args.get('next')
			if clerk_access():
				return redirect(url_for('clerk_dashboard'))
			if account_access():
				return redirect(url_for('accountant_dashboard'))
			else:
				flash("You need to be approved before you can access any page", 'warning')
				return redirect(next_page) if next_page else redirect(url_for('home'))
		else:
			flash("Login unsuccessful, please try again", "danger")
	return render_template("user_login1.html", form=form)



@app.route("/logout")
def logout():
	logout_user()
	return redirect(url_for("login"))


@app.route("/accountant_dashboard/pta_expenses", methods = ['GET', 'POST'])
@login_required
def pta_expenses():
	if account_access():
		title = "Make PTA Expense"
		form = PTAExpensesForm()
		form1 = NewExpenseCatForm()
		if form1.data['exp_submit'] and form1.validate_on_submit():
			category = form1.data.get('category')
			new = ExpenseCategory(adder = current_user.username, category=category)
			db.session.add(new)
			db.session.commit()
			return redirect(url_for('pta_expenses'))
		if  form.data['submit'] and form.validate_on_submit():
			detail = form.data.get('detail')
			mode = form.data.get('mode')
			totalcost = form.data.get('totalcost')
			semester = form.data.get('semester')
			category = form.data.get('category')
			exp1 = Expenses(expensor=current_user.username,detail=detail, mode=mode, category=category.category, semester=semester, 
				totalcost=totalcost)
			pta1 = PTAExpenses(expensor=current_user.username,detail=detail, mode=mode, category=category.category, semester=semester, 
				totalcost=totalcost)
			
			db.session.add(exp1)
			db.session.add(pta1)
			
			db.session.commit()
			#flash("Data successfully saved", "success")
			return redirect(url_for("gen_expenses"))
		return render_template("pta_expenses_form.html", form=form, title=title, form1=form1)
	else:
		abort(404)


@app.route("/accountant_dashboard/etl_expenses", methods = ['GET', 'POST'])
@login_required
def etl_expenses():
	if account_access():
		title = "Make ETL Expense"
		form = ETLExpensesForm()
		form1 = NewExpenseCatForm()
		if form1.data['exp_submit'] and form1.validate_on_submit():
			category = form1.data.get('category')
			new = ExpenseCategory(adder = current_user.username, category=category)
			db.session.add(new)
			db.session.commit()
			#flash(f'{category} category added', 'success')
		if form.data['submit'] and form.validate_on_submit():
			detail = form.data.get('detail')
			mode = form.data.get('mode')
			totalcost = form.data.get('totalcost')
			semester = form.data.get('semester')
			category = form.data.get('category')
			#balance1 = int(obtain_cash_book_balances(ETLCashBook))
			exp1 = Expenses(expensor=current_user.username,detail=detail, mode=mode, 
				category=category.category, semester=semester, totalcost=totalcost)
			etl1 = ETLExpenses(expensor=current_user.username,detail=detail, mode=mode, 
				category=category.category, semester=semester, totalcost=totalcost)
			db.session.add(exp1)
			db.session.add(etl1)
			db.session.commit()
			#flash("Data successfully saved", "success")
			return redirect(url_for("etl_expenses"))
		return render_template("etl_expenses_form.html", form=form, title=title, form1=form1)
	else:
		abort(404)


@app.route("/account")
@login_required
def account():
	return render_template("account.html")


@app.route("/accountant_dashboard/promote_all_students")
@login_required
def promote_all_students():
	if account_access():
		return render_template('promote_student.html')
		#students = Student.query.all()
		#for stud in students:
		#	new_class = promote_student(stud.class1)
		#	if new_class:
		#		stud.class1 = new_class
		#	else:
		#		pass
		#db.session.commit()
		#return "All students promoted!"
	else:
		abort(404)


@app.route("/accountant_dashboard/semester/charges")
@login_required
def charges():
	if account_access():
		form = ChargeForm()
		if form.validate_on_submit():
			etl = form.data.get('etl')
			pta = form.data.get('pta')
			begin = form.data.get('begin_date')
			end = form.data.get('end_date')
			sem = form.data.get('semester')
			total = etl + pta
			charge = Charges(account=current_user.username,begin_date=begin, end_date=end, etl=etl, pta=pta,
			 total=total, semester=sem)
			
			db.session.add(charge)
			db.session.add(pmt)
			db.session.commit()
		return render_template("charges.html", form=form)
	else:
		abort(404)


@app.route("/accountant_dashboard/expenses/add_expense_category", methods = ['GET', 'POST'])
@login_required
def add_expense_category():
	if account_access():
		categories = ExpenseCategory.query.all()
		form = NewExpenseCatForm()
		if form.validate_on_submit():
			category = form.data.get('category')
			new = ExpenseCategory(adder = current_user.username, category=category)
			db.session.add(new)
			db.session.commit()
			flash(f"{category} added to expenses category", 'success')
			return redirect(url_for('add_expense_category'))
		return render_template("add_expense_category.html", form=form, categories=categories)
	else:
		abort(404)


@app.route("/clerk_dashboard", methods=['GET', 'POST'])
@login_required
def clerk_dashboard():
	if clerk_access():
		form1 = SearchForm()
		form2 = StudentSignUp()
		form3 = DonationForm()
		#DonationForm(name, amount, mode, semester)
		if form3.data['submit'] and form3.validate_on_submit():
			name = form3.data.get('name')
			amount = form3.data.get('amount')
			mode = form3.data.get('mode')
			semester = form3.data.get('semester')
			receipt = generate_receipt_no()
			pta1 = PTAIncome(clerk=current_user.username,name=name,tx_id=receipt, amount=amount, mode_of_payment=mode, semester=semester, type1='donation')
			db.session.add(pta1)
			db.session.commit()
			flash(f"Donation received from {name}", 'success')
		if form2.data['register_submit'] and form2.validate_on_submit():
			name = form2.data.get("name").strip()
			class1 = form2.data.get("class1")
			dob = form2.data.get("date_of_birth")
			date_ad = form2.data.get("date_admitted")
			phone = form2.data.get("parent_contact")
			phone1 = form2.data.get("phone")
			idx = generate_student_id(phone, dob)
			stud = Student(clerk=current_user.username,date=date_ad,fullname=name, phone=phone1, date_of_birth=dob, class1=class1.class1, parent_contact=phone, id_number=idx, date_admitted=date_ad)
			db.session.add(stud)
			db.session.commit()
			flash(f"{name} successfully registered!", "success")
			return redirect(url_for('clerk_dashboard'))


		if form1.data['search_submit'] and form1.validate_on_submit():
			phone = form1.data.get('parent_contact')
			dob = form1.data.get('date_of_birth')
			stud_id = generate_student_id(contact=phone, dob=dob)
			student = Student.query.filter_by(id_number=stud_id).first()
			if student:
				name = encrypt_text(student.fullname)
				dob = student.date_of_birth
				phone = encrypt_text(student.parent_contact)
				idx = student.id
				return redirect(url_for('pay_search_result', name=name, dob=dob, phone=phone, idx=idx, class1=student.class1))
			else:
				flash("No record found, please check and try again!", "danger")
		today = datetime.utcnow()
		date = dt.date(today.year, today.month, today.day)
		payments = StudentPayments.query.filter(func.date(StudentPayments.date) == date).all()
		etl = sum([pmt.etl_amount for pmt in payments if pmt.category != 'charge'])
		pta = sum([pmt.pta_amount for pmt in payments if pmt.category != 'charge'])

		student = len(set([pmt.payer.id_number for pmt in payments if pmt.payer is not None]))

		#expenses = Expenses.query.filter(func.date(Expenses.date) == date).all()
		#expense = sum([exp.totalcost for exp in Expenses.query.all()])
		total = etl + pta
		return render_template('clerk_dashboard111.html', form1=form1, form2=form2,
			etl=etl, pta=pta, total=total, student=student, form3=form3)
	else:
		abort(404)



@app.route("/accountant_dashboard/all_students")
@login_required
def all_students():
	if account_access():
		students = Student.query.all()
		return render_template("all_students.html", students=students)
	else:
		abort(404)


def prepare_etlptacash_book(mode='pta'):
    con = create_engine(uri)
    if mode == 'etl':
    	etl_exp = pd.read_sql_query("SELECT date, item, totalcost from etl_expenses", con)
    	etl_inc = pd.read_sql_query("SELECT date, amount, category from etl_income WHERE category='revenue'", con)
    	etl_exp.rename(columns={'totalcost':'amount'}, inplace = True)
    	etl_exp['amount'] = -1*etl_exp['amount']
    	etl_exp['category'] = 'payment'
    	etl_inc['item'] = 'etl payments'
    if mode == 'pta':
    	etl_exp = pd.read_sql_query("SELECT date, item, totalcost from pta_expenses", con)
    	etl_inc = pd.read_sql_query("SELECT date, amount, category from pta_income WHERE category='revenue'", con)
    	etl_exp.rename(columns={'totalcost':'amount'}, inplace = True)
    	etl_exp['amount'] = -1*etl_exp['amount']
    	etl_exp['category'] = 'payment'
    	etl_inc['item'] = 'pta payments'
    comb1 = pd.merge(etl_inc, etl_exp, how = 'outer')
    df2 = comb1.sort_values('date', ignore_index=True)
    df2['balance'] = df2['amount'].cumsum()
    df2['bf'] = df2['balance'].shift(1)
    df2['bf'] = df2['bf'].fillna(0)
    return df2


def query_cash_book(start, end, df):
	start = pd.to_datetime(start)
	end = pd.to_datetime(end)
	new1 = df[(df['date'] >= start) & (df['date'] <= end)]
	return new1


def student_ledg(date, id1):
	con = create_engine(uri)
	date = pd.to_datetime(date)
	q1 = pd.read_sql_query(f"SELECT student_payments.date, fullname, semester, etl_amount, pta_amount, tx_id, category from student INNER JOIN student_payments ON student_payments.student_id = student.id WHERE student.id_number = '{id1}'", con)
	q2 = pd.read_sql_query("SELECT begin_date, etl, pta, semester FROM charges", con)
	q3 = q2[q2['begin_date'] >= date]
	q3['category'] = 'charge'
	q3.rename(columns={'etl':'etl_amount', 'pta':'pta_amount', 'begin_date':'date'}, inplace = True)
	q3['etl_amount'] = -1*q3['etl_amount']
	q3['pta_amount'] = -1*q3['pta_amount']
	comb1 = pd.merge(q3, q1, how = 'outer')
	comb1['etl_total'] = comb1['etl_amount'].cumsum()
	comb1['pta_total'] = comb1['pta_amount'].cumsum()
	df2 = comb1.sort_values('date', ignore_index=True)
	df2.fillna(0, inplace=True)
	return df2


@app.route("/accountant_dashboard/cash_book_report1/<start>,<end>, <cat>")
@login_required
def cash_book_report1(start, end, cat):
	if account_access():
		start1, end1 = date_transform(start,end)
		if cat == 'ETL':
			cbk = query_cash_book(str(start1), str(end1), df=prepare_etlptacash_book(mode='etl'))
		if cat == 'PTA Levy':
			cbk = query_cash_book(str(start1), str(end1), df=prepare_etlptacash_book(mode='pta'))
		if cat == 'ETL & PTA Levy':
			return redirect(url_for('combined_cash_bk', start=start,end=end, cat=cat))
		balance = list(cbk['balance'])
		date = [str(dat)[:10] for dat in cbk['date']]
		details = list(cbk['item'])
		amount = list(cbk['amount'])
		category = list(cbk['category'])
		debit = sum([i for i in amount if i >= 0])
		credit = sum([i for i in amount if i < 0])
		bf = list(cbk['bf'])[0]
		bfdate = date[0]
		bal1 = abs(debit)-abs(credit)
		return render_template("cash_book11.html", balance=balance, date=date, details=details, amount=amount,
				debit=debit, credit=credit, bal1=bal1, 
				category1=cat, category=category,start=start, end=end, bf=bf, bfdate=bfdate)
	else:
		abort(404)


@app.route("/accountant_dashboard/combined_cash_bk/<start>,<end>,<cat>")
@login_required
def combined_cash_bk(start, end, cat):
	if account_access():
		start1, end1 = date_transform(start,end)
		cbk = query_cash_book(str(start1), str(end1), df = combined_cash_book())
		balance = list(cbk['balance'])
		date = [str(dat)[:10] for dat in cbk['date']]
		details = list(cbk['item'])
		amount = list(cbk['amount'])
		category = list(cbk['main_cat'])
		debit = abs(sum([i for i in amount if i >= 0]))
		credit = sum([i for i in amount if i < 0])
		bf = list(cbk['bf'])[0]
		bfdate = date[0]
		bal1 = abs(debit) - abs(credit)
		return render_template("cash_book11.html", balance=balance, date=date, details=details, amount=amount,
				debit=debit, credit=credit, bal1 = bal1, 
				category1=cat, category=category,start=start, end=end, bf=bf, bfdate=bfdate)
	else:
		abort(404)

def combined_cash_book():
    con = create_engine(uri)
    etl_exp = pd.read_sql_query("SELECT date, item, totalcost from etl_expenses", con)
    pta_exp = pd.read_sql_query("SELECT date, item, totalcost from pta_expenses", con)
    etl_exp['category'] = 'etl_exp'
    etl_exp['main_cat'] = 'payment'
    pta_exp['category'] = 'pta_exp'
    pta_exp['main_cat'] = 'payment'
    comb1 = pd.merge(etl_exp, pta_exp, how = 'outer')
    etl_inc = pd.read_sql_query("SELECT date, amount, category from etl_income WHERE category='revenue'", con)
    pta_inc = pd.read_sql_query("SELECT date, amount, category from pta_income WHERE category='revenue'", con)
    etl_inc.rename(columns={'category':'main_cat'}, inplace = True)
    pta_inc.rename(columns={'category':'main_cat'}, inplace = True)
    pta_inc['category'] = 'pta_inc'
    etl_inc['category'] = 'etl_inc'
    pta_inc['item'] = 'pta income'
    etl_inc['item'] = 'etl income'
    comb2 = pd.merge(etl_inc, pta_inc, how = 'outer')
    comb1.rename(columns={'totalcost':'amount'}, inplace = True)
    comb1['amount'] = -1*comb1['amount']
    cash = pd.merge(comb1, comb2, how = 'outer')
    df2 = cash.sort_values('date', ignore_index=True)
    df2['balance'] = df2['amount'].cumsum()
    df2['bf'] = df2['balance'].shift(1)
    df2['bf'] = df2['bf'].fillna(0)
    return df2





def bal_date(cash_book, book):
	if len(cash_book) >= 1:
		cash_bk = cash_book[0].id
		bf1 = book.query.get_or_404(cash_bk)
		bf = bf1.balance
		bfdate = bf1.date.date()
	else:
		bf = 0
		bfdate = None
	balance = [bf] + [i.amount if i.category =="revenue" else -1*i.amount for i in cash_book]
	balance = cumsum(balance)
	return balance, bf, bfdate


@app.route("/accountant_dashboard/expenses_statement/<start1>, <end1>, <category>")
@login_required
def expenses_statement(start1, end1, category):
	if account_access():
		if category == 'ETL & PTA Levy':
			start, end = date_transform(start1,end1)
			expenses = Expenses.query.filter(Expenses.date.between(start, end)).all()
			cum1 = cumsum([exp.totalcost for exp in expenses ])
			if len(cum1) < 1:
				flash(f"No data for the period {start} to {end1}", "success")
				return redirect(url_for('accountant_dashboard'))
			return render_template("expenses_statement.html", expenses=expenses, cum1=cum1, start=start, end=end1)
		if category == 'ETL':
			return redirect(url_for('etl_expenses_statement', start1=start1, end1=end1))
		if category == 'PTA Levy':
			return redirect(url_for('pta_expenses_statement', start1=start1, end1=end1))
	else:
		abort(404)


@app.route("/accountant_dashboard/pta_expenses_statement/<start1>, <end1>")
@login_required
def pta_expenses_statement(start1, end1):
	if account_access():
		start, end = date_transform(start1,end1)
		expenses = PTAExpenses.query.filter(PTAExpenses.date.between(start, end)).all()
		cum1 = cumsum([exp.totalcost for exp in expenses ])
		if len(cum1) < 1:
			flash(f"No data for the period {start} to {end1}", "success")
			return redirect(url_for('accountant_dashboard'))
		return render_template("pta_expenses_statement.html", expenses=expenses, cum1=cum1, start=start, end=end1)
	else:
		abort(404)


@app.route("/accountant_dashboard/etl_expenses_statement/<start1>, <end1>")
@login_required
def etl_expenses_statement(start1, end1):
	if account_access():
		start, end = date_transform(start1,end1)
		expenses = ETLExpenses.query.filter(ETLExpenses.date.between(start, end)).all()
		cum1 = cumsum([exp.totalcost for exp in expenses ])
		if len(cum1) < 1:
			flash(f"No data for the period {start} to {end1}", "success")
			return redirect(url_for('accountant_dashboard'))
		return render_template("etl_expenses_statement.html", expenses=expenses, cum1=cum1, start=start, end=end1)
	else:
		abort(404)


@app.route("/accountant_dashboard/income_statement/<start1>, <end1>, <category>")
@login_required
def income_statement(start1, end1, category):
	if account_access():
		start, end = date_transform(start1,end1)
		if category == "PTA Levy":
			incomes = PTAIncome.query.filter(PTAIncome.date.between(start, end)).filter(PTAIncome.category=='revenue').all()	
		if category == "ETL":
			incomes = ETLIncome.query.filter(ETLIncome.date.between(start, end)).filter(ETLIncome.category=='revenue').all()
		if category == "ETL & PTA Levy":
			incomes = StudentPayments.query.filter(StudentPayments.date.between(start, end)).filter(StudentPayments.category=='revenue').all()
		cum1 = cumsum([inc.amount for inc in incomes if inc.category != 'charge'])
		if len(incomes) < 1:
			flash(f"No data for the period {start} to {end1}", "success")
			return redirect(url_for('accountant_dashboard'))
		return render_template("income_statement.html", incomes=incomes, start=start, end=end1,category=category, cum1=cum1)
	else:
		abort(404)


@app.route("/accountant_dashboard/income_and_expenditure/<start1>, <end1>, <category>")
@login_required
def income_and_expenditure(start1, end1, category):
	if account_access():
		start, end = date_transform(start1,end1)
		if category == "PTA Levy":
			incomes = PTAIncome.query.filter(PTAIncome.date.between(start, end)).filter(PTAIncome.category=='revenue').all()
			expenses = PTAExpenses.query.filter(PTAExpenses.date.between(start, end)).all()	
		if category == "ETL":
			incomes = ETLIncome.query.filter(ETLIncome.date.between(start, end)).filter(ETLIncome.category=='revenue').all()
			expenses = ETLExpenses.query.filter(ETLExpenses.date.between(start, end)).all()
		if category == "ETL & PTA Levy":
			incomes = StudentPayments.query.filter(StudentPayments.date.between(start, end)).filter(StudentPayments.category=='revenue').all()
			expenses = Expenses.query.filter(Expenses.date.between(start, end)).all()
		c1 = [inc.amount for inc in incomes if inc.category != 'charge' ] 
		c2 = [-1*exp.totalcost for exp in expenses ]
		cums = cumsum(c1+c2)
		return render_template("income_expend.html", incomes=incomes, expenses=expenses, cums=cums, 
			sum1 = sum(c1), sum2=-1*sum(c2), category=category, start=start, end=end1)
	else:
		abort(404)


@app.route("/accountant_dashboard/begin_sem", methods=['GET', 'POST'])
@login_required
def begin_sem():
	if account_access():
		form = ChargeForm()
		if form.validate_on_submit():
			etl = form.data.get('etl')
			pta = form.data.get('pta')
			begin = form.data.get('begin_date')
			end = form.data.get('end_date')
			sem = form.data.get('semester')
			total = etl + pta
			charge = Charges(account=current_user.username, begin_date=begin, end_date=end, etl=etl, pta=pta,
			 total=total, semester=sem)
			etl_data = ETLIncome(clerk=current_user.username, amount=etl, tx_id=None, semester=sem, mode_of_payment=None, student_id=None, category='charge')
			pta_data = PTAIncome(clerk=current_user.username, amount=pta, tx_id=None, semester=sem, mode_of_payment=None, student_id=None, category='charge')
			pmt = StudentPayments(etl_amount=etl, pta_amount=pta, amount=total, category="charge", semester=sem)
			db.session.add(charge)
			db.session.add(pmt)
			db.session.add(etl_data)
			db.session.add(pta_data)
			db.session.commit()
			flash("Successfully saved semester charges!", "success")
			return redirect(url_for("accountant_dashboard"))
		return render_template("begin_sem.html", form=form)
	else:
		abort(404)


@app.route("/accountant_dashboard", methods=['POST', 'GET'])
@login_required
def accountant_dashboard():
	if account_access():
		studs = len(Student.query.all())
		incomes = StudentPayments.query.all()
		etl = sum([inc.etl_amount for inc in incomes if inc.category == 'revenue'])
		pta = sum([inc.pta_amount for inc in incomes if inc.category == 'revenue'])
		form1 = ExpensesForm()
		form2 = ReportsForm()
		if form2.data['submit_rep'] and form2.validate_on_submit():
			report = form2.data.get("report")
			filter_by = form2.data.get("filter_by")
			start = form2.data.get("start")
			end = form2.data.get("end")
			if report == 'INCOME & EXPENDITURE' and filter_by == 'ETL':
				return redirect(url_for('etl_income_and_expenditure', start=start, end=end))
			if report == 'INCOME & EXPENDITURE' and filter_by == 'PTA Levy':
				return  redirect(url_for('pta_income_and_expenditure', start=start, end=end))
			if report == 'CASH RECEIPT' and filter_by == 'ETL':
				return  redirect(url_for('etl_cash_receipt', start=start, end=end))
			if report == 'CASH RECEIPT' and filter_by == 'PTA Levy':
				return  redirect(url_for('pta_cash_receipt', start=start, end=end))
			if report == 'CASH PAYMENT' and filter_by == 'ETL':
				return  redirect(url_for('etl_payment_cash_book', start=start, end=end))
			if report == 'CASH PAYMENT' and filter_by == 'PTA Levy':
				return  redirect(url_for('pta_payment_cash_book', start=start, end=end))
			
			if report == "Cash Book":
				category = filter_by
				#category = encrypt_text(plain_text=filter_by)
				return redirect(url_for('cash_book_report1', start=start, end=end, cat = category))
				#return redirect(url_for('cash_book_report', start1=start, end1=end, category=category))
			if report == "Income Statement":
				return redirect(url_for('income_statement', start1=start, end1=end, category=filter_by))
			if report == "Expenditure Statement":
				return redirect(url_for('expenses_statement', start1=start, end1=end, category=filter_by))
			if report == "Income & Expenditure":
				return redirect(url_for('income_and_expenditure', start1=start, end1=end, category=filter_by))
		expense = sum([exp1.totalcost for exp1 in Expenses.query.all()])
		todo = ToDoForm()
		if todo.data['submit_do'] and todo.validate_on_submit():
			if todo.data.get('task') == "Make E.T.L Expenses":
				return redirect(url_for('etl_expenses'))
			if todo.data.get('task') == "Make P.T.A Expenses":
				return redirect(url_for('pta_expenses'))
			if todo.data.get('task') == "Begin Semester":
				return redirect(url_for('begin_sem'))

		return render_template("accountant_dashboard11.html", todo=todo, form1=form1, studs=studs, income=pta+etl, pta=pta, etl=etl,
			expense=expense, form2=form2)
	else:
		abort(404)


@app.route("/accountant_dashboard/student_classes/", methods=['POST', 'GET'])
@login_required
def student_classes():
	if account_access():
		newclass = NewClassForm()
		if newclass.validate_on_submit():
			cls1 = Classes(account=current_user.username,class1=newclass.data.get('newclass'))
			db.session.add(cls1)
			db.session.commit()
			flash(f"Class {newclass.data.get('newclass')} added class lists", "success")
		classes = Classes.query.all()
		
		return render_template("students_classes.html", newclass=newclass, classes=classes)
	else:
		abort(404)

@app.route("/accountant_dashboard/search_ledgers", methods=['POST','GET'])
@login_required
def search_ledgers():
	if account_access():
		form = StudentLedgerForm()
		if form.validate_on_submit():
			phone = form.data.get("phone")
			dob = form.data.get("dob")
			dob1 = dt.date(day=dob.day, month=dob.month, year=dob.year)
			phone = encrypt_text(str(phone))
			return redirect(url_for('ledger_results', phone=phone, dob=dob1))
		return render_template("search_ledger.html", form=form)
	else:
		abort(404)


@app.route("/clerk_dashboard/student/pay_search_result/<name>,<dob>,<phone>, <int:idx>, <class1>", methods=['GET', 'POST'])
@login_required
def pay_search_result(name, dob, phone, idx, class1):
	if clerk_access():
		form = StudentPaymentsForm()
		
		name = decrypt_text(name)
		dob = dob
		phone = decrypt_text(phone)
		idx = idx

		if form.validate_on_submit():
			pta = form.pta_amount.data
			etl = form.etl_amount.data
			semester = form.semester.data
			cheq_no = form.cheq_no.data
			mode = form.mode.data
			if mode == 'Cash':
				tx_id = generate_receipt_no()
			else:
				tx_id = cheq_no
			
			#balance1 = int(obtain_cash_book_balances(ETLCashBook))
			#balance2 = int(obtain_cash_book_balances(PTACashBook))

			if etl and not pta:
				amount = float(etl)
				pta = 0
				pmt_data = StudentPayments(etl_amount=etl, pta_amount=0, semester=semester, mode_of_payment=mode, student_id=idx, amount=amount, tx_id=tx_id)
				etl_data = ETLIncome(clerk=current_user.username,amount=etl, tx_id=tx_id, semester=semester, mode_of_payment=mode, student_id=idx)
				id2 = ETLIncome.query.all()[-1].id
				id1 = StudentPayments.query.all()[-1].id
				#etlcash = ETLCashBook(amount=etl, category="revenue", semester=semester, balance = balance1, income_id=id2+1)
				
				db.session.add(etl_data)
				db.session.add(pmt_data)
				

			if pta and not etl:
				amount = float(pta)
				etl = 0
				pmt_data = StudentPayments(etl_amount=0, pta_amount=pta, semester=semester, mode_of_payment=mode, student_id=idx, amount=amount, tx_id=tx_id)
				pta_data = PTAIncome(clerk=current_user.username,amount=pta, tx_id=tx_id, semester=semester, mode_of_payment=mode, student_id=idx)
				id1 = StudentPayments.query.all()[-1].id
				id2 = PTAIncome.query.all()[-1].id
				#ptacash = PTACashBook(amount=pta, category="revenue", semester=semester, balance = balance2, income_id=id2+1)
				
				db.session.add(pta_data)
				db.session.add(pmt_data)
				

			if pta and etl:
				amount = float(pta) + float(etl)
				pmt_data = StudentPayments(etl_amount=etl, pta_amount=pta, semester=semester, mode_of_payment=mode, student_id=idx, amount=amount, tx_id=tx_id)
				pta_data = PTAIncome(clerk=current_user.username, amount=pta, tx_id=tx_id, semester=semester, mode_of_payment=mode, student_id=idx)
				etl_data = ETLIncome(clerk=current_user.username, amount=etl, tx_id=tx_id, semester=semester, mode_of_payment=mode, student_id=idx)
				#ptacash = PTACashBook(amount=pta, category="revenue", semester=semester, balance = balance2, income_id=id2+1)
				#etlcash = ETLCashBook(amount=etl, category="revenue", semester=semester, balance = balance1, income_id=id3+1)
				
				db.session.add(pta_data)
				db.session.add(etl_data)
				db.session.add(pmt_data)


			student = Student.query.get_or_404(idx)
			name = student.fullname
			contact = student.parent_contact
			class1 = student.class1
		
			db.session.commit()

			tx_id = encrypt_text(str(tx_id))
			name = encrypt_text(name)
			contact = encrypt_text(contact)

			#flash(f"Payment successfully made!", "success")
			return redirect(url_for('receipt', num=tx_id, name=name, etl_amount=etl, pta_amount=pta, contact=contact, class1=class1))
				
		return render_template("pay_search_results.html", class1=class1, fullname=name, date_of_birth=dob, 
			parent_contact=phone, form=form)
	else:
		abort(404)


@app.route("/clerk_dashboard/receipt/<num>, <name>, <etl_amount>, <pta_amount>, <contact>, <class1>")
@login_required
def receipt(num, name, etl_amount, pta_amount, contact, class1):
	if clerk_access():
		num = decrypt_text(num)
		name = decrypt_text(name)
		contact = decrypt_text(contact)
		today = dt.datetime.now()
		total = float(etl_amount) + float(pta_amount)
		return render_template("receipt.html",day=today.day, month=today.month, year=today.year, 
			num=num, name=name, etl_amount=etl_amount, pta_amount=pta_amount, total=total, 
			contact=contact, class1=class1)
	else:
		abort(404)

@app.route("/accountant_dashboard/expenses/gen_expenses")
@login_required
def gen_expenses():
	if account_access():
		expenses = Expenses.query.all()
		total = sum([exp.totalcost for exp in expenses])
		return render_template("gen_expenses.html", expenses=expenses, total=total)
	else:
		abort(404)

@app.route("/accountant_dashboard/total_etl_income")
@login_required
def total_etl_income():
	if account_access():
		incomes = ETLIncome.query.all()
		return render_template("total_etl_income.html", incomes=incomes)
	else:
		abort(404)

@app.route("/accountant_dashboard/total_pta_income")
@login_required
def total_pta_income():
	if account_access():
		incomes = PTAIncome.query.all()
		return render_template("total_pta_income.html", incomes=incomes)
	else:
		abort(404)

@app.route("/accountant_dashboard/pta_cash_receipt/<start>,<end>")
@login_required
def pta_cash_receipt(start, end):
	if account_access():
		start1, end1 = date_transform(start, end)
		incomes = PTAIncome.query.filter_by(category = 'revenue').filter(PTAIncome.date.between(start1, end1)).order_by(PTAIncome.category.desc()).all()
		cash = sum([i.amount for i in incomes if i.mode_of_payment != 'Cheque'])
		cheq = sum([i.amount for i in incomes if i.mode_of_payment == 'Cheque'])
		dues = sum([i.amount for i in incomes if i.type1 == 'dues'])
		dona = sum([i.amount for i in incomes if i.type1 == 'donation'])
		return render_template("pta_cash_receipt.html", incomes=incomes, cash=cash, cheq=cheq,dona=dona,dues=dues, start=start1, end=end)
	else:
		abort(404)


@app.route("/accountant_dashboard/etl_cash_receipt/<start>,<end>")
@login_required
def etl_cash_receipt(start, end):
	if account_access():
		start1, end1 = date_transform(start, end)
		incomes = ETLIncome.query.filter_by(category = 'revenue').filter(ETLIncome.date.between(start1, end1)).order_by(ETLIncome.category.desc()).all()
		cash = sum([i.amount for i in incomes if i.mode_of_payment == 'Cash'])
		cheq = sum([i.amount for i in incomes if i.mode_of_payment == 'Cheque'])
		tot = cash + cheq
		return render_template("etl_cash_receipt.html", incomes=incomes, cash=cash, cheq=cheq, tot = tot, start=start1, end=end)
	else:
		abort(404)

@app.route("/accountant_dashboard/etl_payment_cash_book/<start>,<end>")
@login_required
def etl_payment_cash_book(start, end):
	if account_access():
		start1, end1 = date_transform(start, end)
		expenses = ETLExpenses.query.filter(ETLExpenses.date.between(start1, end1)).order_by(ETLExpenses.category.desc()).all()
		cash = sum([i.totalcost for i in expenses if i.mode == 'Cash'])
		bank = sum([i.totalcost for i in expenses if i.mode == 'Bank'])
		tot = cash + bank
		return render_template("etl_payment_cash_book.html", expenses=expenses, cash=cash, bank=bank, tot=tot, start=start1, end=end)
	else:
		abort(404)


@app.route("/accountant_dashboard/pta_payment_cash_book/<start>,<end>")
@login_required
def pta_payment_cash_book(start, end):
	if account_access():
		start1, end1 = date_transform(start, end)
		expenses = PTAExpenses.query.filter(PTAExpenses.date.between(start1, end1)).order_by(PTAExpenses.category.desc()).all()
		cash = sum([i.totalcost for i in expenses if i.mode == 'Cash'])
		bank = sum([i.totalcost for i in expenses if i.mode == 'Bank'])
		tot = cash + bank
		return render_template("pta_payment_cash_book.html", expenses=expenses, cash=cash, bank=bank, tot = tot, start=start1, end=end)
	else:
		abort(404)


@app.route("/accountant_dashboard/etl_income_and_expenditure/<start>, <end>")
@login_required
def etl_income_and_expenditure(start, end):
	start1, end1 = date_transform(start,end)
	if account_access():
		dues = ETLIncome.query.filter(ETLIncome.date.between(start1, end1)).filter_by(category='revenue').all()
		dues = sum([i.amount for i in dues])
		bf = 200
		profit = 34029
		inc_tot = dues + bf + profit
		cust = ETLExpenses.query.filter(ETLExpenses.date.between(start1, end1)).order_by(ETLExpenses.category.desc()).all()
		set1 = list(set([i.category for i in cust]))
		dbs = [ETLExpenses.query.filter_by(category=i).filter(ETLExpenses.date.between(start1, end1)).order_by(ETLExpenses.category.desc()).all() for i in set1]
		dict1 = {k:v for k,v in zip(set1, dbs)}
		tx = db.session.query(ETLExpenses.category.desc(), func.sum(ETLExpenses.totalcost)).filter(ETLExpenses.date.between(start1, end1)).group_by(ETLExpenses.category).all()
		dict2 =  {d1:k1 for d1, k1 in tx}
		surplus = inc_tot - sum([i for i in dict2.values()])
		return render_template("etl_income_and_expenditure.html", dues=dues, bf=bf, profit=profit, 
			start=start1, end=end, dict1=dict1, dict2=dict2, inc_tot=inc_tot, surplus=surplus)
	else:
		abort(404)

@app.route("/accountant_dashboard/pta_income_and_expenditure/<start>, <end>")
@login_required
def pta_income_and_expenditure(start, end):
	start1, end1 = date_transform(start,end)
	if account_access():
		dues = PTAIncome.query.filter(PTAIncome.date.between(start1, end1)).filter_by(category='revenue').all()
		dues = sum([i.amount for i in dues])
		dues0 = PTAIncome.query.filter(PTAIncome.date < start1).filter_by(category='revenue').all()
		expe0 = PTAExpenses.query.filter(PTAExpenses.date < start1).filter_by(category='revenue').all()
		inc0 = sum([i.amount for i in dues0])
		exp0 = sum([i.totalcost for i in expe0])
		prf0 = 0
		bf = inc0 + prf0 - exp0
		profit = 34029
		inc_tot = dues + bf + profit
		cust = PTAExpenses.query.filter(PTAExpenses.date.between(start1, end1)).order_by(PTAExpenses.category.desc()).all()
		set1 = list(set([i.category for i in cust]))
		dbs = [PTAExpenses.query.filter_by(category=i).filter(PTAExpenses.date.between(start1, end1)).order_by(PTAExpenses.category.desc()).all() for i in set1]
		dict1 = {k:v for k,v in zip(set1, dbs)}
		tx = db.session.query(PTAExpenses.category.desc(), func.sum(PTAExpenses.totalcost)).filter(PTAExpenses.date.between(start1, end1)).group_by(PTAExpenses.category).all()
		dict2 =  {d1:k1 for d1, k1 in tx}
		surplus = inc_tot - sum([i for i in dict2.values()])

		return render_template("pta_income_and_expenditure.html", dues=dues, bf=bf, profit=profit, 
			start=start1, end=end, dict1=dict1, dict2 = dict2, inc_tot=inc_tot, surplus=surplus)
	else:
		abort(404)

@app.route("/clerk_dashboard/clerk_daily_report")
@login_required
def clerk_daily_report():
	if clerk_access():
		today = datetime.utcnow()
		date = dt.date(today.year, today.month, today.day)
		#payments = StudentPayments.query.filter(func.date(StudentPayments.date) == date).all()
		pta_payments = PTAIncome.query.filter(func.date(PTAIncome.date) == date).filter_by(category='revenue').all()
		etl_payments = ETLIncome.query.filter(func.date(ETLIncome.date) == date).filter_by(category='revenue').all()
		etl = sum([pmt.amount for pmt in etl_payments])
		pta = sum([pmt.amount for pmt in pta_payments])
		return render_template("clerk_daily_report.html", pta_payments=pta_payments,etl_payments=etl_payments ,etl=etl, pta=pta, date=date)
	else:
		abort(404)


@app.route("/accountant_dashboard/account_daily_report")
@login_required
def account_daily_report():
	if account_access():
		today = datetime.utcnow()
		date = dt.date(today.year, today.month, today.day)
		#payments = StudentPayments.query.filter(func.date(StudentPayments.date) == date).all()
		pta_payments = PTAIncome.query.filter(func.date(PTAIncome.date) == date).filter_by(category='revenue').all()
		etl_payments = ETLIncome.query.filter(func.date(ETLIncome.date) == date).filter_by(category='revenue').all()
		etl = sum([pmt.amount for pmt in etl_payments])
		pta = sum([pmt.amount for pmt in pta_payments])
		return render_template("account_daily_report.html", pta_payments=pta_payments,etl_payments=etl_payments ,etl=etl, pta=pta, date=date)
	else:
		abort(404)


@app.route("/accountant_dashboard/student_stats")
@login_required
def student_stats():
	if account_access():
		return render_template("student_stats.html")
	else:
		abort(404)


@app.route("/accountant_dashboard/search_ledgers/ledger_results/<string:phone>, <string:dob>")
@login_required
def ledger_results(phone, dob):
	if account_access():
		phone1 = '0' + decrypt_text(phone)
		idx = generate_student_id(phone1, dob)
		student = Student.query.filter_by(id_number=idx).first()
		if student:
			df2 = student_ledg(date = student.date_admitted, id1=idx)
			date = [str(i)[:10] for i in df2['date']]
			ch1 = df2[df2['category'] == 'charge']
			if len(ch1['pta_amount']) > 0:
				pta_charge = float(list(ch1['pta_amount'])[-1])
				etl_charge = float(list(ch1['etl_amount'])[-1])
			else:
				pta_charge = 0
				etl_charge = 0
			etls = list(df2['etl_amount'])
			ptas = list(df2['pta_amount'])
			sems = list(df2['semester'])
			category = list(df2['category'])
			pta = [i for i in ptas if i > 0]
			etl = [i for i in etls if i > 0]
			total = sum(etl) + sum(pta)
			cum1 = cumsum(etls)
			cum2 = cumsum(ptas)
			return render_template("ledger_results1.html", student=student, cum1=cum1, cum2=cum2,sems=sems,
			 pta_charge=pta_charge, etl_charge=etl_charge,etls=etls, ptas=ptas, date=date, category=category)
		else:
			flash("Student not found!", "danger")
			return redirect(url_for('search_ledgers'))
	else:
		abort(404)



@app.route("/accountant_dashboard/delete_class/<int:id>", methods=['GET'])
@login_required
def delete_class(id):
	if account_access():
		cls1 = Classes.query.get_or_404(id)
		db.session.delete(cls1)
		db.session.commit()
		flash(f'The class {cls1.class1} has been deleted!', 'success')
		return redirect(url_for('student_classes'))
	else:
		abort(404)



@app.route("/accountant_dashboard/delete_expense_category/<int:id>", methods=['GET'])
@login_required
def delete_expense_category(id):
	if account_access():
		cls1 = ExpenseCategory.query.get_or_404(id)
		db.session.delete(cls1)
		db.session.commit()
		flash(f'The class {cls1.category} has been deleted!', 'success')
		return redirect(url_for('add_expense_category'))
	else:
		abort(404)




class Classes(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	date = db.Column(db.DateTime, default = datetime.utcnow())
	class1 = db.Column(db.String(10), unique=True, nullable=False)
	account = db.Column(db.String(120), nullable=False)

	def __repr__(self):
		return f'User: {self.class1}'


class ExpenseCategory(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	date = db.Column(db.DateTime, default = datetime.utcnow())
	adder = db.Column(db.String(120))
	category = db.Column(db.String(120), nullable=False)

	def __repr__(self):
		return f'User: {self.category}'


#FORMS
def classquery():
	return Classes.query


def expensequery():
	return ExpenseCategory.query

class StudentSignUp(FlaskForm):
    name = StringField("Full Name", validators=[DataRequired()])
    date_of_birth = DateField("Date of Birth", validators=[DataRequired()])
    date_admitted = DateField("Date of Admission", validators=[DataRequired()])
    class1 = QuerySelectField(query_factory=classquery, get_label = 'class1', allow_blank = True)
    parent_contact = StringField("Parent Contact", validators=[DataRequired(), Length(min=10, max=13)])
    phone = StringField("Student Phone #", validators = [Length(min=10, max=13)])
    register_submit = SubmitField("Register")

    def validate_date_admitted(self, date_admitted):
    	today = datetime.utcnow()
    	today = dt.date(year=today.year, month=today.month, day=today.day)
    	date_admitted1 = dt.date(year=date_admitted.data.year, month=date_admitted.data.month, day=date_admitted.data.day)
    	if date_admitted1 > today:
    		raise ValidationError(f"Date cant't be further than {today}")

    def validate_name(self, name):
    	for char in name.data:
    		if inside(ch=char) == False:
    			raise ValidationError(f'Character {char} is not allowed')

    def validate_parent_contact(self, parent_contact):
    	for char in parent_contact.data:
    		if inside2(ch=char) == False:
    			raise ValidationError(f'Character {char} is not allowed')

    def validate_phone(self, phone):
    	for char in phone.data:
    		if inside2(ch=char) == False:
    			raise ValidationError(f'Character {char} is not allowed')

class UserSignUpForm(FlaskForm):
	username = StringField("Full Name", validators=[DataRequired()])
	email = EmailField("Email", validators=[DataRequired(), Email()])
	password = PasswordField("Password", validators=[DataRequired(), Length(min=8, max=20)])
	confirm_password = PasswordField("Comfirm Password", validators = [DataRequired(), EqualTo('password')])
	function = SelectField("Role", choices = [('','Choose Role...'),('Accountant', 'Accountant'), ('Clerk','Clerk')], validators=[DataRequired()])
	submit = SubmitField("Register")

	def validate_email(self, email):
		user = User.query.filter_by(email=email.data).first()
		if user:
			raise ValidationError("The email is already in use, please choose a different one")

	def validate_username(self, username):
		for char in username.data:
			if inside(ch=char) == False:
				raise ValidationError(f'Character {char} is not allowed')


class UserLogInForm(FlaskForm):
    email = EmailField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    remember = BooleanField("Remember me")
    submit = SubmitField("Login")

    def validate_password(self, password):
    	characters = ['=', '.','<','>', '-', '_', '/', '?', '!', '&', '\\', '$']
    	for char in characters:
    		if char in password.data:
    			raise ValidationError(f'Character {char} is not allowed')



class NewClassForm(FlaskForm):
	newclass = StringField("Class Name", validators=[DataRequired(), Length(max	= 5)])
	submit = SubmitField("create")

	def validate_newclass(self, newclass):
		cls1 = Classes.query.filter_by(class1=newclass.data).first()
		if cls1:
			raise ValidationError("Class already exist!")


class NewExpenseCatForm(FlaskForm):
	category = StringField("New Category Name", validators=[DataRequired(), Length(max	= 200)])
	exp_submit = SubmitField("Create")

	def validate_category(self, category):
		cls1 = ExpenseCategory.query.filter_by(category=category.data).first()
		if cls1:
			raise ValidationError("Expense category already exist!")



class ETLExpensesForm(FlaskForm):
	detail = StringField("Item", validators=[DataRequired(), Length(max=120)])
	mode = SelectField("Mode of Payment", validators=[DataRequired()], choices = [('','Choose mode...'),('Cash', 'Cash'), ('Bank','Bank')])
	semester = SelectField("Semester", validators = [DataRequired()], choices = [('','Choose semester...'),('SEM1', 'SEM1'), ('SEM2','SEM2')])
	totalcost = DecimalField("Total Cost", validators=[DataRequired(), NumberRange(min=1, max=3000000)])
	category = QuerySelectField(query_factory=expensequery, get_label = 'category', allow_blank = False)
	submit = SubmitField("Debit")

	def validate_detail(self, detail):
		for char in detail.data:
			if inside(ch=char) == False:
				raise ValidationError(f'Character {char} is not allowed')


class PTAExpensesForm(FlaskForm):
	detail = StringField("Item", validators=[DataRequired(), Length(max=120)])
	mode = SelectField("Mode of Payment", validators=[DataRequired()], choices = [('','Choose mode...'),('Cash', 'Cash'), ('Bank','Bank')])
	semester = SelectField("Semester", validators = [DataRequired()], choices = [('','Choose semester...'),('SEM1', 'SEM1'), ('SEM2','SEM2')])
	totalcost = DecimalField("Total Cost", validators=[DataRequired(), NumberRange(min=1, max=3000000)])
	category = QuerySelectField(query_factory=expensequery, get_label = 'category', allow_blank = False)
	submit = SubmitField("Debit")

	def validate_detail(self, detail):
		for char in detail.data:
			if inside(ch=char) == False:
				raise ValidationError(f'Character {char} is not allowed')

#DATABASES


class User(db.Model, UserMixin):
	id = db.Column(db.Integer, primary_key=True)
	date = db.Column(db.DateTime, default = datetime.utcnow())
	username = db.Column(db.String(80), nullable=False)
	email = db.Column(db.String(120), unique=True, nullable=False)
	password = db.Column(db.String(120), nullable=False)
	is_admin = db.Column(db.Boolean,  default=False)
	function = db.Column(db.String(120))
	approval = db.Column(db.Boolean, default=False)
	

	def __repr__(self):
		return f'User: {self.username}'




class Student(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	date = db.Column(db.DateTime, default = datetime.utcnow())
	clerk = db.Column(db.String(120),nullable=False)
	date_admitted = db.Column(db.DateTime)
	fullname = db.Column(db.String(80), nullable=False)
	date_of_birth = db.Column(db.String(10), nullable=False)
	class1 = db.Column(db.String(10), nullable=False)
	parent_contact = db.Column(db.String(12), nullable=False)
	phone = db.Column(db.String(12))
	id_number = db.Column(db.String(120), unique=True, nullable=False)
	status = db.Column(db.Boolean, default=True)
	pta = db.relationship('PTAIncome', backref='pta_payer', lazy=True)#Here we reference the class
	etl = db.relationship('ETLIncome', backref='etl_payer', lazy=True)
	payer = db.relationship('StudentPayments', backref='payer', lazy=True)

	def __repr__(self):
		return f'User: {self.fullname}'


class PTAIncome(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	date = db.Column(db.DateTime, default = datetime.utcnow())
	clerk = db.Column(db.String(120), nullable=False)
	amount = db.Column(db.Float)
	tx_id = db.Column(db.String(16))
	semester = db.Column(db.String(10))
	mode_of_payment = db.Column(db.String(20))
	category = db.Column(db.String(20), default="revenue")
	name = db.Column(db.String(120))
	type1 = db.Column(db.String(20), default='dues')
	student_id = db.Column(db.Integer, db.ForeignKey('student.id'))#Here we reference the table name

	def __repr__(self):
		return f'User: {self.student_id}'

class ETLIncome(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	date = db.Column(db.DateTime, default = datetime.utcnow())
	clerk = db.Column(db.String(120),nullable=False)
	amount = db.Column(db.Float)
	tx_id = db.Column(db.String(16))
	semester = db.Column(db.String(10), nullable = False)
	mode_of_payment = db.Column(db.String(20))
	name = db.Column(db.String(120))
	category = db.Column(db.String(20), default="revenue")
	student_id = db.Column(db.Integer, db.ForeignKey('student.id'))#Here we reference the table name

	def __repr__(self):
		return f'User: {self.student_id}'


class StudentPayments(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	date = db.Column(db.DateTime, default = datetime.utcnow())
	etl_amount = db.Column(db.Float)
	pta_amount = db.Column(db.Float)
	amount = db.Column(db.Float)
	tx_id = db.Column(db.String(16))
	semester = db.Column(db.String(10))
	mode_of_payment = db.Column(db.String(20))
	name = db.Column(db.String(120))
	type1 = db.Column(db.String(20), default='dues')
	category = db.Column(db.String(20), default="revenue")
	student_id = db.Column(db.Integer, db.ForeignKey('student.id'))

	def __repr__(self):
		return f'User: {self.student_id}'

class Expenses(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	date = db.Column(db.DateTime, default = datetime.utcnow())
	expensor = db.Column(db.String(120), nullable=False)
	detail = db.Column(db.String(120))
	category = db.Column(db.String(120))
	mode = db.Column(db.String(120))
	semester = db.Column(db.String(120))
	totalcost = db.Column(db.Float)
	
	def __repr__(self):
		return f'User: {self.detail}'


class PTAExpenses(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	date = db.Column(db.DateTime, default = datetime.utcnow())
	expensor = db.Column(db.String(120), nullable=False)
	detail = db.Column(db.String(120))
	category = db.Column(db.String(120))
	mode = db.Column(db.String(120))
	semester = db.Column(db.String(120))
	totalcost = db.Column(db.Float)
	
	def __repr__(self):
		return f'User: {self.detail}'


class ETLExpenses(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	date = db.Column(db.DateTime, default = datetime.utcnow())
	expensor = db.Column(db.String(120), nullable=False)
	detail = db.Column(db.String(120))
	category = db.Column(db.String(120))
	mode = db.Column(db.String(20))
	semester = db.Column(db.String(20))
	totalcost = db.Column(db.Float)
	
	def __repr__(self):
		return f'User: {self.detail}'


class Charges(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	begin_date = db.Column(db.DateTime)
	end_date = db.Column(db.DateTime)
	account = db.Column(db.String(120), nullable=False)
	etl = db.Column(db.Float, nullable=False)
	pta = db.Column(db.Float, nullable=False)
	total = db.Column(db.Float, nullable=False)
	semester = db.Column(db.String(10), nullable = False)

	def __repr__(self):
		return f'User: {self.total}'


#class OtherBusiness(db.Model):
#	id = db.Column(db.Integer, primary_key=True)
#	date0 = db.Column(db.DateTime, default=dt.datetime.utcnow())
#	date = db.Column(db.DateTime, nullable=False)
#	detail = db.Column(db.String(120), nullable=False)
#	amount = db.Column(db.Float, nullable=False)
#
#	def __repr__(self):
#		return f'User: {self.detail}'

#current_sem = 'SEM1'#Charges.query.all()[-1].semester




#Archives
def create_student_ledger(tablename, dbname, df2):
    engine = create_engine('sqlite:///', echo=False)
    engine = create_engine(f'sqlite:///Archives/StudentLedgers/{dbname}.db', echo=False)
    sqlite_connection = engine.connect()
    sqlite_table = tablename
    df2.to_sql(sqlite_table, sqlite_connection, if_exists='fail')


def move_to_archives(std_id):
	std = Student.get_or_404(std_id)
	dob = std.date_of_birth
	phone = std.parent_contact
	hash1 = sha256(str(std_id).encode()).hexdigest()

	etl = PTAIncome.query.filter_by(student_id=stud_id_id).first()
	pta = ETLIncome.query.filter_by(student_id=stud_id_id).first()
	#create_student_ledger(tablename='allpayments', dbname=hash1, df2)

	db.delete(std)
	db.delete(pmt)
	db.delete(etl)
	db.delete(pta)
	db.session.commit()



def obtain_cash_book_balances(database):
	cash = db.session.query(database).order_by(database.date)
	obj = [i.amount if i.category =="revenue" else -1*i.amount for i in cash]
	cum = cumsum(obj)
	if cum.size < 1:
		return 0
	if cum.size >= 1:
		return cum[-1]




class MyModelView(ModelView):
	def is_accessible(self):
		if current_user.is_authenticated:# and current_user.approval and current_user.is_admin:
			return True
		else:
			return False


admin = Admin(app, template_mode='bootstrap4', name = 'Kpasec PTA')
admin.add_view(MyModelView(User, db.session))
admin.add_view(MyModelView(Classes, db.session))
#admin.add_view(MyModelView(StudentPayments, db.session))
#admin.add_view(MyModelView(Expenses, db.session))
#admin.add_view(MyModelView(PTAIncome, db.session))


if __name__ == '__main__':
	app.run(debug = False)





#enctype in forms
#securities
#flask admin
#rss feed


#Install prostgres
#pip install psycopg2
