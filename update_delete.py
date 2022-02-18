

@app.route("/updatestudentinfo/<string:contact>", methods = ['GET', 'POST'])
@login_required
def updatestudentinfo(contact):
	form = UpdateStudentInfo()
	student = Student.query.filter_by(parent_contact=contact).first()
	if student:
		if form.validate_on_submit():
			student.fullname = form.data.get('name')
			student.email = form.data.get('email')
			student.class1 = form.data.get('class1')
			student.parent_contact = form.data.get('parent_contact')
			db.session.commit()
			flash(f"Account successfully updated for {form.name.data}", "success")
			return redirect(url_for("data_entry_clerk"))
		elif request.method == 'GET':
			form.name.data = student.fullname
			form.email.data = student.email
			form.class1.data = student.class1
			form.parent_contact.data = student.parent_contact
		return render_template("updatestudentinfo.html", form=form)
	return "Results not found"


@app.route("/updateexpense/<int:exp_id>", methods = ['GET', 'POST'])
@login_required
def updateexpense(exp_id):
	title = "Update Expense"
	form = ExpensesForm()
	expense = Expenses.query.get_or_404(exp_id)
	if form.validate_on_submit():
		expense.purchase_date = form.data.get('purchase_date')
		expense.item = form.data.get('item')
		expense.purpose = form.data.get('purpose')
		expense.quantity = form.data.get('quantity')
		expense.unitcost = form.data.get('unitcost')
		expense.totalcost = form.data.get('totalcost')
		db.session.commit()
		flash(f"Expense successfully updated for {expense.id}", "success")
		return redirect(url_for("gen_expenses"))
	elif request.method == 'GET':
		form.purchase_date.data = expense.purchase_date
		form.item.data = expense.item
		form.purpose.data = expense.purpose
		form.quantity.data = expense.quantity
		form.unitcost.data = expense.unitcost
		form.totalcost.data = expense.totalcost
	return render_template("expenses_form.html", form=form, title=title)

@app.route("/updateincome/<int:inc_id>", methods = ['GET', 'POST'])
@login_required
def updateincome(inc_id):
	title = "Update Cash"
	form = StudentPaymentsForm()
	income = StudentPayments.query.get_or_404(inc_id)
	cash_bk = CashBook.query.filter_by(income_id = inc_id).first()
	if form.validate_on_submit():
		income.etl_amount = form.data.get('etl_amount')
		income.pta_amount = form.data.get('pta_amount')
		income.semester = form.data.get('semester')
		income.mode_of_payment = form.data.get('mode_of_payment')
		cash_bk.etl = form.data.get("etl_amount")
		cash_bk.pta = form.data.get("pta_amount")
		cash_bk.semester = form.data.get("semester")
		cash_bk.amount = int(form.data.get("etl_amount")) + int(form.data.get("etl_amount"))
		db.session.commit()
		flash(f"Income successfully updated for {income.id}", "success")
		return redirect(url_for("total_etl_income"))
	elif request.method == 'GET':
		form.etl_amount.data = income.etl_amount
		form.pta_amount.data = income.pta_amount
		form.semester.data = income.semester
		form.mode_of_payment.data = income.mode_of_payment
	return render_template("pay_search_results.html", form=form, title=title, fullname=income.payer.fullname,
	 parent_contact = income.payer.parent_contact, date_of_birth = income.payer.date_of_birth)


@app.route("/updateuser", methods = ['GET', 'POST'])
@login_required
def updateuser():
	form = UpdateUserInfo()
	if form.validate_on_submit():
		current_user.username = form.data.get('username')
		current_user.email = form.data.get('email')
		print(current_user.username)
		print(current_user.email)
		db.session.commit()
		flash(f"Account successfully updated for {form.username.data}", "success")
		return redirect(url_for("account"))
	elif request.method == 'GET':
		form.username.data = current_user.username
		form.email.data = current_user.email
	return render_template("updateuser.html", form=form)


@app.route("/updatepaymentdata/<int:pmt_id>", methods = ['GET', 'POST'])
@login_required
def updatepaymentdata(pmt_id):
	payment = StudentPayments.query.get_or_404(pmt_id)
	print(payment)
	form = StudentPaymentsForm()
	if form.validate_on_submit():
		payment.student_fullname = form.data.get('fullname')
		payment.amount = form.data.get('amount')
		payment.semester = form.data.get('semester')
		payment.mode_of_payment = form.data.get('mode_of_payment')
		payment.category = form.data.get('category')
		db.session.commit()
		flash(f"Payment successfully updated for {form.fullname.data}", "success")
		return redirect(url_for("account"))
	elif request.method == 'GET':
		form.fullname.data = payment.student_fullname
		form.amount.data = payment.amount
		form.semester.data = payment.semester
		form.mode_of_payment.data = payment.mode_of_payment
		form.category.data = payment.category
	return render_template("updatepaymentdata.html", form=form)


@app.route("/payment/<int:pmt_id>/delete", methods=['POST'])
@login_required
def delete_payment(pmt_id):
    payment = StudentPayments.query.get_or_404(pmt_id)
    db.session.delete(payment)
    db.session.commit()
    flash('The payment has been deleted!', 'success')
    return redirect(url_for('data_entry_clerk'))


@app.route("/delete_expense/<int:exp_id>")
@login_required
def delete_expense(exp_id):
    expense = Expenses.query.get_or_404(exp_id)
    db.session.delete(expense)
    db.session.commit()
    flash('The expense has been deleted!', 'success')
    return redirect(url_for('gen_expenses'))


@app.route("/student/<int:std_id>/delete", methods=['POST'])
@login_required
def delete_student(std_id):
    student = Student.query.get_or_404(std_id)
    db.session.delete(student)
    db.session.commit()
    flash(f'The student {student.fullname} has been deleted!', 'success')
    return redirect(url_for('data_entry_clerk'))




class UpdateStudentInfo(FlaskForm):
    name = StringField("Full Name", validators=[DataRequired()])
    email = StringField("Email", validators=[DataRequired()])
    #class1 = SelectField("Class", validators=[DataRequired()], choices = [c1.class1 for c1 in Classes.query.all()])
    parent_contact = StringField("Parent Contact", validators=[DataRequired(), Length(min=10, max=10)])
    submit = SubmitField("Update")

    def validate_email(self, email):
    	if email.data != Student.query.filter_by(email = email.data).first().email:
    		stud = Student.query.filter_by(email = email.data).first()
    		if stud:
    			raise ValidationError('That email is taken. Please choose a different one.')
class UpdateUserInfo(FlaskForm):
    username = StringField("Name", validators=[DataRequired()])
    email = StringField("Email", validators=[DataRequired(), Email()])
    #password = PasswordField("Password", validators=[DataRequired(), Length(min=8, max=20)])
    #confirm_password = PasswordField("Comfirm Password", 
    #	validators = [DataRequired(), EqualTo('password')])
    submit = SubmitField("Update Info")

    def validate_email(self, email):
        if email.data != current_user.email:
            user = User.query.filter_by(email=email.data).first()
            if user:
                raise ValidationError('That email is taken. Please choose a different one.')
