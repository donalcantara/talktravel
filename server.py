from flask import Flask, request, redirect, render_template, session, flash
from mysqlconnection import MySQLConnector
from time import time

app = Flask(__name__)
mysql = MySQLConnector(app, 'wall')

app.secret_key = "ThisIsSecret!"

@app.route('/register', methods=['POST'])
def submit():
	temp = request.form['username']
	username = temp.lower()
	error = 0
	if request.form['name'].isalpha() == True:
		flash("Name cannot contain numbers!")
		error += 1
	if len(request.form['username']) < 1:
		flash("Username cannot be blank!")
		error += 1
	if len(request.form['name']) < 1:
		flash("Name cannot be blank!")
		error += 1
	if len(request.form['email']) < 1:
		flash("Email cannot be blank!")
		error += 1
	if len(request.form['password']) < 8:
		flash("Password cannot be less than 8 characters!")
		error += 1
	if len(request.form['password']) != len(request.form['confirm']):
		flash("Confirmed password doesn't match!")
		error += 1
	user = "SELECT * FROM users WHERE users.email = :email LIMIT 1"
	data = {'email': request.form['email']}
	user = mysql.query_db(user, data)
	if len(user) > 0:
		flash('That email is already registered!')
		error += 1
	user = "SELECT * FROM users WHERE users.username = :user LIMIT 1"
	data = {'user': username}
	user = mysql.query_db(user, data)
	if len(user) > 0:
		flash('That username is already taken!')
		error += 1
	if error > 0:
		print error
		return redirect('/')
	if error == 0:
		query = "INSERT INTO users(name, username, email, password, created_at, updated_at) VALUES (:name, :user, :email, :password, NOW(), NOW())"
		data = {
			'name': request.form['name'],
			'user': username,
			'email': request.form['email'],
			'password': request.form['password']
			}
		user = mysql.query_db(query, data)
		flash("Great!  Now log in below!")
		return redirect('/')

@app.route('/')
def index():
	session['email'] = []
	session['username'] = []
	session['password'] = []
	session['password'] = []
	query = "SELECT * FROM users"
	users = mysql.query_db(query)
	return render_template('index.html', users = users)

@app.route('/login', methods=['POST'])
def login():
	error = 0
	temp = request.form['username']
	username = temp.lower()
	print username
	password = request.form['password']
	if len(username) < 1:
		flash("Username cannot be empty")
		error += 1
	if len(request.form['password']) < 1:
		flash("Password cannot be empty")
		error += 1
	query = "SELECT * FROM users WHERE users.username = :username LIMIT 1"
	data = {'username': username}
	user = mysql.query_db(query, data)
	if error > 0:
		print error
		return redirect('/')
	if len(user) == 0:
		flash('There is no account with that username!')
		return redirect('/')
	if user[0]:
		if user[0]['password'] == password:
			session['id'] = user[0]['id']
			session['username'] = username
			return redirect('/wall')
		else:
			flash("Incorrect username and/or password!")
			return redirect('/')

@app.route('/wall')
def wall():
	query = "SELECT * FROM users WHERE users.username = :username LIMIT 1"
	data = {'username': session['username']}
	users = mysql.query_db(query, data)
	print session['username']
	posts = mysql.query_db("SELECT posts.content, posts.created_at, users.name, users.username, users.id AS user_id, posts.id AS post_id FROM posts join users ON users.id = posts.user_id ORDER BY posts.created_at DESC")
	for post in posts:
		post['created_at'] = post['created_at'].strftime('%m/%d/%Y %-I:%M:%S %p')
		comments = mysql.query_db("SELECT * FROM users JOIN comments on users.id = comments.user_id ORDER BY comments.created_at ASC")
	for comment in comments:
		comment['created_at'] = comment['created_at'].strftime('%m/%d/%Y %-I:%M:%S %p')
	return render_template('wall.html', posts=posts, comments=comments)

@app.route('/account/<username>', methods=['GET'])
def show(username): #user_id is the variable that you're passing
	print username
	query = "SELECT * FROM users WHERE username = :specific_id" #this is the query you're sending to the database
	data = {'specific_id': username} # this is the data you're sending to the datbase
	users = mysql.query_db(query, data) #combine the query with the data and you'll get back data from the database
	return render_template('edit.html', users=users) #this sends you to the edit.html page with friends being the data you requested

@app.route('/post/<user_id>', methods=['POST'])
def post(user_id):
	message = request.form['message']
	query = 'INSERT INTO posts (user_id, content, created_at, updated_at) VALUES (:id, :post, NOW(), NOW())'
	data = {
		'id': user_id,
		'post': message
		}
	posts = mysql.query_db(query, data)
	return redirect('/wall')

@app.route('/comment/<post_id>', methods=["POST"])
def comment(post_id):
	user_id = session['id']
	comment = request.form['comment']
	query = 'INSERT INTO comments (user_id, post_id, content, created_at, updated_at) VALUES (:user_id, :post_id, :comment, NOW(), NOW())'
	data = {
		'user_id': user_id,
		'post_id': post_id,
		'comment': comment
		}
	mysql.query_db(query, data)
	return redirect('/wall')


@app.route('/logout')
def logout():
	return redirect('/')

@app.route('/delete/<user_id>')
def delete(user_id):
	query = "DELETE FROM users WHERE id = :id" #this is the query
	data = {'id': user_id} #this is the data
	mysql.query_db(query, data) #this is the result from the query with the data from the db
	return redirect('/') #redirect back to the front page

@app.route('/deletepost/<post_id>')
def deletepost(post_id):
	query = 'SET foreign_key_checks = 0; DELETE FROM comments WHERE post_id = :id; SET foreign_key_checks = 1;'
	data = {'id': post_id}
	mysql.query_db(query, data)
	query = 'SET foreign_key_checks = 0; DELETE FROM posts WHERE id = :id; SET foreign_key_checks = 1;'
	data = {'id': post_id}
	mysql.query_db(query, data)
	return redirect('/wall')

@app.route('/deletecomment/<comment_id>')
def deletecomment(comment_id):
	query = 'SET foreign_key_checks = 0; DELETE FROM comments WHERE id = :id; SET foreign_key_checks = 1;'
	data = {'id': comment_id}
	mysql.query_db(query, data)
	return redirect('/wall')


@app.route('/update/<user_id>', methods=['POST'])
def update(user_id):
	query = "UPDATE users SET name = :name, username = :username, email = :email, updated_at = NOW() WHERE id = :id" #the query that you're updating info from the db back to the db
	data = { #this is the data you'll be updating in the db
		'name': request.form['name'], 
		'username':  request.form['username'],
		'email': request.form['email'],
		'id': user_id
		}
	mysql.query_db(query, data)
	return redirect('/wall')

app.run(debug=True)















