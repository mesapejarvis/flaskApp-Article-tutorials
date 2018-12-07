from flask import Flask, render_template,flash, request, redirect, url_for, session, logging
# pulling data from file from data import Article
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from passlib.hash import sha256_crypt
from functools import wraps
from flaskext.mysql import MySQL
app = Flask(__name__)

# mysql = MySQL()
# mysql.init_app(app)
# cursor = mysql.get_db().cursor()

# Config Mysql
app.config['MYSQL_DATABASE_HOST'] = 'localhost'
app.config['MYSQL_DATABASE_USER'] = 'root'
app.config['MYSQL_DATABASE_PASSWORD'] = ''
app.config['MYSQL_DATABASE_DB'] = 'flasktutorial'
app.config['MYSQL_DATABASE_CURSORCLASS'] = 'DictCursor'
# app.config['MYSQL_DATABASE_USER'] = 'root'
# app.config['MYSQL_DATABASE_PASSWORD'] = ''
# app.config['MYSQL_DATABASE_DB'] = 'flasktutorial'

# Init mysql
mysql = MySQL(app)



# pulling data from file Art = Article()

# home route
@app.route('/')
def index():
	return render_template('home.html')
	pass

# all articles page
@app.route('/article')
def article():
	# create cursor
	cur = mysql.get_db().cursor()

	# execute query
	result = cur.execute("SELECT * FROM articles")

	articles = cur.fetchall()
	

	# check if they are aricles
	if result > 0:
		return render_template('article.html', articles = articles)
	else:
		msg ="No articles found"
		return render_template('article.html', msg = msg)
	# close con
	cur.close()
	

# get individual article
@app.route('/articles/<string:id>/')
def articles(id):
	# create cursor
	cur = mysql.get_db().cursor()

	# execute query
	result = cur.execute("SELECT * FROM articles WHERE id=%s", [id])

	article = cur.fetchone()
	

	return render_template('articles.html', article = article)
	
# about us page
@app.route('/about')
def about():
	return render_template('about.html')
	pass

# check if user is logged in
def is_logged_in(f):
	@wraps(f)
	def wrap(*args, **kwargs):
		if 'logged_in' in session:
			return f(*args, **kwargs)
		else:
			flash('Unauthorized User','danger')
			return redirect(url_for('login'))
	return wrap
			

		


# dashboard
@app.route('/dashboard')
@is_logged_in
def dashboard():

	# create cursor
	cur = mysql.get_db().cursor()

	# execute query
	result = cur.execute("SELECT * FROM articles")

	articles = cur.fetchall()


	# check if they are aricles
	if result > 0:
		return render_template('dashboard.html', articles = articles)
	else:
		msg ="NO articles found"
		return render_template('dashboard.html', msg = msg)
	# close con
	cur.close()

	

# logout
@app.route('/logout')
# check if session is set
@is_logged_in
def logout():
	session.clear()
	flash('You are now logged out', 'success')
	return redirect(url_for('login'))
	

# signing up a user
@app.route('/signup')
def signup():
	return render_template('signup.html')
	pass
# Registration form
class RegisterForm(Form):
	name = StringField('Name', [validators.length(min=1, max=50)])
	username = StringField('Username', [validators.length(min=4, max=25)])
	email = StringField('Email', [validators.length(min=6, max=50)])
	password = PasswordField('Password', [
		validators.DataRequired(),
		validators.EqualTo('confirm', message='Passwords do not match')

		])
	confirm = PasswordField('Confirm Password')

# User registration
@app.route('/register', methods = ['GET','POST'])
def register():
	form = RegisterForm(request.form)
	if request.method == 'POST' and form.validate():
		name = form.name.data
		username = form.username.data
		email = form.email.data
		password = sha256_crypt.encrypt(str(form.password.data))

		# create cursor object
		cur = mysql.get_db().cursor()
		cur.execute("INSERT INTO user(name, email, username, password) VALUES(%s,%s,%s,%s)", (name, email, username, password))

		# comimit to db
		mysql.get_db().commit()

		# close db
		cur.close()

		flash('You are now rgisterd! Please login to access the Dashboard','success')
		return redirect(url_for('login'))
		

	return render_template('register.html', form = form)


@app.route('/login', methods=['GET','POST'])
def login():

	if request.method == 'POST':
		username = request.form['username']
		password_candidate = request.form['password']

		#create cursor
		cur = mysql.get_db().cursor()
		app.logger.info(username)


		# Get user by username
		result = cur.execute("SELECT * FROM user WHERE username =%s",[username])
		app.logger.info(result)

		# Check results and get stored harsh
		if result > 0:
			data = cur.fetchone()
			password = data[4]

			# Compare passwords
			if sha256_crypt.verify(password_candidate, password):

				# app.logger.info('PASSWORD MATCHED')
				session['logged_in'] = True
				session['username'] = username
				flash('You are now logged in','success')
				return redirect(url_for('dashboard'))
		        #return redirect(url_for('dashboard'))

			else:
				# app.logger.info('PASSWORD NOT MATCHED')
				error ='Invalid Password'
				return render_template('login.html', error=error)
				cur.close()
				

		else:
			# app.logger.info('NO user with that name')
			error ='Invalid Username'
			return render_template('login.html', error=error)
		

	return render_template('login.html')

# Create article form
class ArticleForm(Form):
	title = StringField('Title', [validators.length(min=1, max=50)])
	body = TextAreaField('Body', [validators.length(min=20)])


# adding articles
@app.route('/add_article', methods=['POST', 'GET'])
@is_logged_in
def add_article():
	form = ArticleForm(request.form)
	if request.method == 'POST' and form.validate():
		title = form.title.data
		body = form.body.data

		# Create cursor
		cur =  mysql.get_db().cursor()

		# execute query
		cur.execute("INSERT INTO articles (title, body, author) VALUES (%s,%s,%s)", (title,body, session['username']))

		# commit to db
		mysql.get_db().commit()

		# close connection
		cur.close()
		flash('Article successfully created', 'success')
		return redirect(url_for('dashboard'))


	return render_template('add_article.html', form = form)



# editing article
@app.route('/edit_article/<string:id>', methods=['POST', 'GET'])
@is_logged_in
def edit_article(id):
	# create cursor
	cur = mysql.get_db().cursor()

	# execute query
	result = cur.execute("SELECT * FROM articles WHERE id=%s", [id])

	article = cur.fetchone()

    # getting the form
	form = ArticleForm(request.form)

	# populate form values
	form.title.data = article[1]
	form.body.data = article[2]
	
 
	if request.method == 'POST' and form.validate():
		title = request.form['title']
		body = request.form['body']

		# Create cursor
		cur =  mysql.get_db().cursor()

		# execute query
		cur.execute("UPDATE articles SET title =%s, body=%s WHERE id =%s", (title,body,id))

		# commit to db
		mysql.get_db().commit()
 
		# close connection
		cur.close() 
		flash('Article successfully Updated', 'success')
		return redirect(url_for('dashboard'))


	return render_template('edit_article.html', form = form)

	
@app.route('/delete_article/<string:id>' , methods=['POST'])
@is_logged_in
def delete_article(id):
	# Create cursor
		cur =  mysql.get_db().cursor()

		# execute query
		cur.execute("DELETE FROM articles WHERE id =%s", (id))

		# commit to db
		mysql.get_db().commit()
 
		# close connection
		cur.close() 
		flash('Article successfully Deleted', 'success')
		return redirect(url_for('dashboard'))
	

if __name__ == '__main__':
	app.secret_key = 'secret631'
	app.run(debug=True)

