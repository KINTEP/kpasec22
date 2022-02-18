from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField,IntegerField, PasswordField, BooleanField, SelectField, DateField, ValidationError
from wtforms.validators import DataRequired, Email, EqualTo, Length, NumberRange, InputRequired 
from datetime import datetime
from helpers import inside
import datetime as dt



class ClientSignUpForm(FlaskForm):
    company_name = StringField("Name", validators=[DataRequired()])
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=8, max=20)])
    confirm_password = PasswordField("Comfirm Password", 
    	validators = [DataRequired(), EqualTo('password')])
    submit = SubmitField("Sign Up")

    def validate_email(self, email):
    	user = User.query.filter_by(email=email.data).first()
    	if user:
    		raise ValueError("The email is already in use, please choose a different one")


class StudentLedgerForm(FlaskForm):
	phone = IntegerField("Parent's Contact", validators=[DataRequired()])
	dob = DateField("DoB", validators=[DataRequired()])
	submit = SubmitField("Generate")

	def validate_phone(self, phone):
		num = str(phone.data)
		print(len(num))
		if len(num) != 9:
			raise ValidationError("Phone number must be 10 digits")

class ClientLogInForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    remember = BooleanField("Remember me")
    submit = SubmitField("Log In")


class ToDoForm(FlaskForm):
    task = SelectField("Choose A Task", choices = ['Make E.T.L Expenses','Make P.T.A Expenses', 'Begin Semester'],  validators=[DataRequired()])
    submit_do = SubmitField("Proceed")


class StudentPaymentsForm(FlaskForm):
	date = DateField("Date" ,validators=[DataRequired()])
	etl_amount = IntegerField("ETL", validators=[InputRequired(), NumberRange(min=0, max=3000)])
	pta_amount = IntegerField("PTA", validators=[InputRequired(), NumberRange(min=0, max=3000)])
	semester = SelectField("Semester", choices = ["","SEM1", "SEM2	"], validators=[DataRequired()])
	mode_of_payment = SelectField("Payment Mode", choices = ['Cash', 'Cheque', 'Momo'], validators=[DataRequired()])
	submit = SubmitField("Receive")

class ExpensesForm(FlaskForm):
	purchase_date = DateField("Purchase Date", validators=[DataRequired()])
	item = StringField("Item", validators=[DataRequired(), Length(max=20)])
	purpose = StringField("Purpose", validators=[DataRequired(), Length(max=50)])
	unitcost = IntegerField("Quantity", validators=[DataRequired(), NumberRange(min=1, max=30000)])
	quantity = IntegerField("Quantity", validators=[DataRequired(), NumberRange(min=1, max=30000)])
	totalcost = IntegerField("Total Cost", validators=[DataRequired(), NumberRange(min=1, max=300000)])
	submit = SubmitField("Debit")
		
	def validate_item(self, item):
		for char in item.data:
			if inside(ch=char) == False:
				raise ValidationError('Invalid characters')
			
	def validate_purpose(self, purpose):
		for char in purpose.data:
			if inside(ch=char) == False:
				raise ValidationError('Invalid characters')

	def validate_totalcost(self, totalcost):
		if totalcost.data != self.quantity.data * self.unitcost.data:
			raise ValidationError(f"Totals cost should be {self.quantity.data * self.unitcost.data} NOT {totalcost.data}")


	def validate_purchase_date(self, purchase_date):
		today = datetime.utcnow()
		today = dt.date(year=today.year, month=today.month, day=today.day)
		purchase_date1 = dt.date(year=purchase_date.data.year, month=purchase_date.data.month, day=purchase_date.data.day)
		if purchase_date1 > today:
			raise ValidationError(f"Date cant't be further than {today}")


class ETLExpensesForm(FlaskForm):
	purchase_date = DateField("Purchase Date", validators=[DataRequired()])
	item = StringField("Item", validators=[DataRequired(), Length(max=20)])
	purpose = StringField("Purpose", validators=[DataRequired(), Length(max=50)])
	unitcost = IntegerField("Quantity", validators=[DataRequired(), NumberRange(min=1, max=30000)])
	quantity = IntegerField("Quantity", validators=[DataRequired(), NumberRange(min=1, max=30000)])
	totalcost = IntegerField("Total Cost", validators=[DataRequired(), NumberRange(min=1, max=300000)])
	submit = SubmitField("Debit")
		
	def validate_item(self, item):
		for char in item.data:
			if inside(ch=char) == False:
				raise ValidationError('Invalid characters')
			
	def validate_purpose(self, purpose):
		for char in purpose.data:
			if inside(ch=char) == False:
				raise ValidationError('Invalid characters')

	def validate_totalcost(self, totalcost):
		if totalcost.data != self.quantity.data * self.unitcost.data:
			raise ValidationError(f"Totals cost should be {self.quantity.data * self.unitcost.data} NOT {totalcost.data}")

	def validate_purchase_date(self, purchase_date):
		today = datetime.utcnow()
		today = dt.date(year=today.year, month=today.month, day=today.day)
		purchase_date1 = dt.date(year=purchase_date.data.year, month=purchase_date.data.month, day=purchase_date.data.day)
		if purchase_date1 > today:
			raise ValidationError(f"Date cant't be further than {today}")



class PTAExpensesForm(FlaskForm):
	purchase_date = DateField("Purchase Date", validators=[DataRequired()])
	item = StringField("Item", validators=[DataRequired(), Length(max=20)])
	purpose = StringField("Purpose", validators=[DataRequired(), Length(max=50)])
	unitcost = IntegerField("Quantity", validators=[DataRequired(), NumberRange(min=1, max=30000)])
	quantity = IntegerField("Quantity", validators=[DataRequired(), NumberRange(min=1, max=30000)])
	totalcost = IntegerField("Total Cost", validators=[DataRequired(), NumberRange(min=1, max=300000)])
	submit = SubmitField("Debit")
		
	def validate_item(self, item):
		for char in item.data:
			if inside(ch=char) == False:
				raise ValidationError('Invalid characters')
			
	def validate_purpose(self, purpose):
		for char in purpose.data:
			if inside(ch=char) == False:
				raise ValidationError('Invalid characters')

	def validate_totalcost(self, totalcost):
		if totalcost.data != self.quantity.data * self.unitcost.data:
			raise ValidationError(f"Totals cost should be {self.quantity.data * self.unitcost.data} NOT {totalcost.data}")

	def validate_purchase_date(self, purchase_date):
		today = datetime.utcnow()
		today = dt.date(year=today.year, month=today.month, day=today.day)
		purchase_date1 = dt.date(year=purchase_date.data.year, month=purchase_date.data.month, day=purchase_date.data.day)
		if purchase_date1 > today:
			raise ValidationError(f"Date cant't be further than {today}")


class ReportsForm(FlaskForm):
    report = SelectField("Choose A Report", validators=[DataRequired()], choices = ["",'Cash Book', 'Income & Expenditure', 'Expenditure Statement', 'Income Statement'])
    filter_by = SelectField("Choose Category", choices = ['','PTA Levy', 'ETL', 'ETL & PTA Levy'])
    start = DateField("Start", validators=[DataRequired()])
    end = DateField("End", validators=[DataRequired()])
    submit_rep = SubmitField("Generate")

    def validate_end(self, end):
    	if end.data <= self.start.data:
    		raise ValidationError("Date must be latter than start date")

    def validate_start(self, start):
    	today = datetime.utcnow()
    	today = dt.date(year=today.year, month=today.month, day=today.day)
    	start1 = dt.date(year=start.data.year, month=start.data.month, day=start.data.day)
    	if start1 > today:
    		raise ValidationError(f"Date is greater than {today}")

class ChargeForm(FlaskForm):
    semester = SelectField("Choose semester", validators=[DataRequired()], 
    	choices = ['','SEM1', 'SEM2'])
    begin_date = DateField("Start Date", validators= [DataRequired()])
    end_date = DateField("End Date", validators= [DataRequired()])
    pta = IntegerField("PTA Levy", validators=[DataRequired()])
    etl = IntegerField("ETL", validators=[DataRequired()])
    submit = SubmitField("Get Started")

    def validate_begin_date(self, begin_date):
    	today = datetime.utcnow()
    	today = dt.date(year=today.year, month=today.month, day=today.day)
    	begin_date1 = dt.date(year=begin_date.data.year, month=begin_date.data.month, day=begin_date.data.day)
    	if begin_date1 > today:
    		raise ValidationError(f"Date is greater than {today}")

    def validate_end_date(self, end_date):
    	if end_date.data <= self.begin_date.data:
    		raise ValidationError("End date must be latter than start date")

    	

class SearchForm(FlaskForm):
    parent_contact = StringField("Parent Contact", validators=[DataRequired(), Length(min=8, max=20)])
    date_of_birth = DateField("Date of Birth", validators=[DataRequired()])
    search_submit = SubmitField("Search")