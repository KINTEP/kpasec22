@app.route('/',methods=['GET'])
def home():
    session['attempt'] = 5
    
@app.route('/login')
def login():
    username = request.form.get('username')
    session['username'] = username
    password = request.form.get('password')
    if username and password and username in users and users[username] == password:
        session['logged_in'] = True
        return redirect(url_for('index'))
    attempt= session.get('attempt')
    attempt -= 1
    session['attempt']=attempt
    #print(attempt,flush=True)
    if attempt==1:
        client_ip= session.get('client_ip')
        flash('This is your last attempt, %s will be blocked for 24hr, Attempt %d of 5'  % (client_ip,attempt), 'error')
    else:
        flash('Invalid login credentials, Attempts %d of 5'  % attempt, 'error')
    return redirect(url_for('login'))


@app.route("/accountant_dashboard/cash_book_report/<string:start1>, <string:end1>, <category>")
@login_required
def cash_book_report(start1, end1, category):
	if current_user.is_authenticated  and current_user.approval:
		start, end = date_transform(start1,end1)
		category = decrypt_text(encrypted_text=category)
		if category == "PTA Levy":
			cash_book = PTACashBook.query.filter(PTACashBook.date.between(start, end)).all()
			income = [i.amount for i in cash_book if i.category == "revenue"]
			expense = [i.amount for i in cash_book if i.category == "payment"]
			balance, bf, bfdate = bal_date(cash_book, book=PTACashBook)
		if category == "ETL":
			cash_book = ETLCashBook.query.filter(ETLCashBook.date.between(start, end)).all()
			income = [i.amount for i in cash_book if i.category == "revenue"]
			expense = [i.amount for i in cash_book if i.category == "payment"]
			balance, bf, bfdate = bal_date(cash_book, book=ETLCashBook)
		if category == "ETL & PTA Levy":
			cash_book = CashBook.query.filter(CashBook.date.between(start, end)).all()
			income = [i.amount for i in cash_book if i.category == "revenue"]
			expense = [i.amount for i in cash_book if i.category == "payment"]
			balance, bf, bfdate = bal_date(cash_book, book=CashBook)
		print(start1, end1)
		return render_template("cash_book.html", cash_book=cash_book, balance=balance, 
			debit=sum(income), credit = sum(expense), bal1 = sum(income)-sum(expense), 
			category=category, start=start, end=end1, bf=bf, bfdate=bfdate)
	else:
		abort(404)





class ETLCashBook(db.Model):
	__bind_key__ = "kpasec"
	id = db.Column(db.Integer, primary_key=True)
	date = db.Column(db.DateTime, default = datetime.utcnow())
	details = db.Column(db.String(120), default = "ETL Income")
	amount = db.Column(db.Integer)
	category = db.Column(db.String(100))
	semester = db.Column(db.String(100))
	balance = db.Column(db.Integer)
	expense_id = db.Column(db.Integer)
	income_id = db.Column(db.Integer)

	def __repr__(self):
		return f'User: {self.details}'

class PTACashBook(db.Model):
	__bind_key__ = "kpasec"
	id = db.Column(db.Integer, primary_key=True)
	date = db.Column(db.DateTime, default = datetime.utcnow())
	details = db.Column(db.String(120), default = "PTA Income")
	amount = db.Column(db.Integer)
	category = db.Column(db.String(100))
	semester = db.Column(db.String(100))
	balance = db.Column(db.Integer)
	expense_id = db.Column(db.Integer)
	income_id = db.Column(db.Integer)

	def __repr__(self):
		return f'User: {self.details}'


class CashBook(db.Model):
	__bind_key__ = "kpasec"
	id = db.Column(db.Integer, primary_key=True)
	date = db.Column(db.DateTime, default = datetime.utcnow())
	details = db.Column(db.String(120), default = "Student payments")
	etl = db.Column(db.Integer)
	pta = db.Column(db.Integer)
	amount = db.Column(db.Integer, nullable=False)
	category = db.Column(db.String(100), nullable = False)
	semester = db.Column(db.String(100), nullable = False)
	balance = db.Column(db.Integer, nullable=False)
	expense_id = db.Column(db.Integer)
	income_id = db.Column(db.Integer)

	def __repr__(self):
		return f'User: {self.details}'

class Client(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime, default = datetime.utcnow())
    company_name = db.Column(db.String(80), unique=False, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)

    def __repr__(self):
        return f'User: {self.company_name}'

@app.route("/register_client", methods = ['GET', 'POST'])
def register_client():
	if current_user.is_authenticated:
		return redirect(url_for('home'))
	form = ClientSignUpForm()
	if form.validate_on_submit():
		if request.method == "POST":
			company_name = form.data['company_name']
			email = form.data['email']
			password = form.data['password']
			hash_password = bcrypt.generate_password_hash(password).decode("utf-8")
			data = Client(company_name=company_name, email=email, password=hash_password)
			db.session.add(data)
			db.session.commit()
		flash(f"Account successfully created for {form.username.data}", "success")
		return redirect(url_for("login"))
	return render_template("register_client.html", form=form)

@app.route("/client_login", methods = ['GET', 'POST'])
@login_required
def client_login():
	if current_user.is_authenticated:
		return redirect(url_for('home'))
	form = ClientLogInForm()
	if form.validate_on_submit():
		user = User.query.filter_by(email=form.email.data).first()
		if user and bcrypt.check_password_hash(user.password, form.password.data):
			login_user(user, remember=form.remember.data)
			next_page = request.args.get('next')
			return redirect(next_page) if next_page else redirect(url_for('data_entry_clerk'))
		else:
			flash("Login unsuccessful, please try again", "danger")
	return render_template("client_login.html", form=form)



@app.route("/reports")
@login_required
def reports():
	form = ReportsForm()
	report = request.args.get("report")
	start = request.args.get("start")
	end = request.args.get("end")
	filter1 = request.args.get("filter_by")
	
	if report == "Cash Book":
		end1 = dt.datetime.strptime(end, "%Y-%m-%d").date() + dt.timedelta(1)
		if filter1 != "ETL & PTA Levy":
			cash_filter = CashBook.query.filter(CashBook.date <= end1).filter(CashBook.date >= start).filter(CashBook.details==filter1).all()
			cash_obj1, cash_cums, sum1, sum2 = extract_cash_book_data(cash_obj=cash_filter)
			return cash_book_template(cash_data=cash_obj1, cash_cums=cash_cums, sum1=sum1, sum2=sum2, start_date=start, end_date=end)
		else:
			cash_filter = CashBook.query.filter(CashBook.date <= end1).filter(CashBook.date >= start).all()
			cash_obj1, cash_cums, sum1, sum2 = extract_cash_book_data(cash_obj=cash_filter)
			return cash_book_template(cash_data=cash_obj1, cash_cums=cash_cums, sum1=sum1, sum2=sum2, start_date=start, end_date=end)
	if report == "Income & Expenditure":
		end1 = dt.datetime.strptime(end, "%Y-%m-%d").date() + dt.timedelta(1)
		inc_by_date = StudentPayments.query.filter(StudentPayments.date <= end1).filter(StudentPayments.date >= start)
		exp_by_date = Expenses.query.filter(Expenses.date <= end1).filter(Expenses.date >= start)
		inc_obj, inc_cum, exp_obj, exp_cum, total = extract_income_and_expense_data(inc_obj=inc_by_date, exp_obj=exp_by_date)
		return income_expenditure_template(income=list(inc_obj), inc_cum=inc_cum, expense=exp_obj, exp_cum=exp_cum, total=total, start_date=start, end_date=end)
	if report == "Income Statement":
		end1 = dt.datetime.strptime(end, "%Y-%m-%d").date() + dt.timedelta(1)
		if filter1 != "ETL & PTA Levy":
			inc_by_date = StudentPayments.query.filter(StudentPayments.date <= end1).filter(StudentPayments.date >= start).filter(StudentPayments.category == filter1).all()
			income, inc_cum = extract_income_data(inc_obj = inc_by_date)
			return income_template(income=income, inc_cum=inc_cum, start_date=start, end_date=end1)
		else:
			inc_by_date = StudentPayments.query.filter(StudentPayments.date <= end1).filter(StudentPayments.date >= start).all()
			income, inc_cum = extract_income_data(inc_obj = inc_by_date)
			return income_template(income=income, inc_cum=inc_cum, start_date=start, end_date=end)
	if report == "Expenditure Statement":
		end1 = dt.datetime.strptime(end, "%Y-%m-%d").date() + dt.timedelta(1)
		exp_by_date = Expenses.query.filter(Expenses.date <= end1).filter(Expenses.date >= start).all()
		expense, exp_cum = extract_expense_data(exp_obj=exp_by_date)
		return expenditure_template(expense=expense, exp_cum=exp_cum, start_date=start, end_date=end)
	return render_template("reports.html", form=form)



@app.route("/download")
def download():
	file = "downloads/file1.jpg"
	return send_file(file, as_attachment = True)


@click.command(name='create_db')
@with_appcontext
def create_db():
	db.create_all()

@click.command(name='drop_db')
@with_appcontext
def drop_db():
	db.drop_all()

@click.command(name='create_tables')
@with_appcontext
def create_tables():
	User.__table__.create(db.engine)
	PTAIncome.__table__.create(db.engine)
	ETLIncome.__table__.create(db.engine)
	PTAExpenses.__table__.create(db.engine)
	ETLExpenses.__table__.create(db.engine)
	Expenses.__table__.create(db.engine)
	StudentPayments.__table__.create(db.engine)
	Charges.__table__.create(db.engine)
	Student.__table__.create(db.engine)

@click.command(name='delete_tables')
@with_appcontext
def delete_tables():
	User.__table__.drop(db.engine)
	PTAIncome.__table__.drop(db.engine)
	ETLIncome.__table__.drop(db.engine)
	PTAExpenses.__table__.drop(db.engine)
	ETLExpenses.__table__.drop(db.engine)
	Expenses.__table__.drop(db.engine)
	StudentPayments.__table__.drop(db.engine)
	Charges.__table__.drop(db.engine)
	Student.__table__.drop(db.engine)
	


app.cli.add_command(create_db)
app.cli.add_command(drop_db)
app.cli.add_command(create_tables)
app.cli.add_command(delete_tables)