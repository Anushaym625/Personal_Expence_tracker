

from flask import Flask, render_template, request, redirect, session 
from flask_mysqldb import MySQL
import MySQLdb.cursors
import re
from flask_bcrypt import Bcrypt
import logging
from flask import redirect, request, session, render_template
import os
import matplotlib.pyplot as plt
import io
import base64

app = Flask(__name__)


app.secret_key = 'a'
  
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'root'
app.config['MYSQL_DB'] = 'expense_db'

mysql = MySQL(app)


#HOME--PAGE
@app.route("/home")
def home():
    return render_template("homepage.html")

@app.route("/")
def add():
    return render_template("home.html")



#SIGN--UP--OR--REGISTER

bcrypt = Bcrypt(app)

@app.route("/signup")
def signup():
    return render_template("signup.html")

from flask_bcrypt import Bcrypt
import re

bcrypt = Bcrypt(app)

@app.route('/register', methods=['GET', 'POST'])
def register():
    msg = ''
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        # Input validation
        if not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            msg = 'Invalid email address!'
        elif not re.match(r'[A-Za-z0-9]+', username):
            msg = 'Username must contain only letters and numbers!'
        elif len(password) < 8:
            msg = 'Password must be at least 8 characters long!'
        else:
            try:
                cursor = mysql.connection.cursor()
                cursor.execute('SELECT * FROM register WHERE username = %s', (username,))
                account = cursor.fetchone()
                if account:
                    msg = 'Account already exists!'
                else:
                    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
                    cursor.execute('INSERT INTO register VALUES (NULL, %s, %s, %s)', (username, email, hashed_password))
                    mysql.connection.commit()
                    msg = 'You have successfully registered!'
                    return render_template('signup.html', msg=msg)
            except Exception as e:
                msg = f"An error occurred: {e}"
            finally:
                cursor.close()

    return render_template('signup.html', msg=msg)


        
        
 
        
 #LOGIN--PAGE
    
@app.route("/signin")
def signin():
    return render_template("login.html")
        
@app.route('/login',methods =['GET', 'POST'])
def login():
    global userid
    msg = ''
   
  
    if request.method == 'POST' :
        username = request.form['username']
        password = request.form['password']
        cursor = mysql.connection.cursor()
        cursor.execute('SELECT * FROM register WHERE username = % s AND password = % s', (username, password ),)
        account = cursor.fetchone()
        print (account)
        
        if account:
            session['loggedin'] = True
            session['id'] = account[0]
            userid=  account[0]
            session['username'] = account[1]
           
            return redirect('/home')
        else:
            msg = 'Incorrect username / password !'
    return render_template('login.html', msg = msg)



       





#ADDING----DATA


@app.route("/add")
def adding():
    return render_template('add.html')

@app.route('/addexpense', methods=['POST'])
def addexpense():
    date = request.form.get('date')
    expensename = request.form.get('expensename')
    amount = request.form.get('amount')
    paymode = request.form.get('paymode')
    category = request.form.get('category')

    if not all([date, expensename, amount, paymode, category]):
        return "Missing required fields", 400

    cursor = mysql.connection.cursor()
    cursor.execute(
        'INSERT INTO expenses (userid, date, expensename, amount, paymode, category) VALUES (%s, %s, %s, %s, %s, %s)',
        (session['id'], date, expensename, amount, paymode, category)
    )
    mysql.connection.commit()
    cursor.close()

    return redirect("/display")


@app.route("/display")
def display():
    print(session["username"],session['id'])
    
    cursor = mysql.connection.cursor()
    cursor.execute('SELECT * FROM expenses WHERE userid = % s AND date ORDER BY `expenses`.`date` DESC',(str(session['id'])))
    expense = cursor.fetchall()
  
       
    return render_template('display.html' ,expense = expense)



#delete---the--data

@app.route('/delete/<string:id>', methods = ['POST', 'GET' ])
def delete(id):
     cursor = mysql.connection.cursor()
     cursor.execute('DELETE FROM expenses WHERE  id = {0}'.format(id))
     mysql.connection.commit()
     print('deleted successfully')    
     return redirect("/display")
 
    
#UPDATE---DATA

@app.route('/edit/<id>', methods = ['POST', 'GET' ])
def edit(id):
    cursor = mysql.connection.cursor()
    cursor.execute('SELECT * FROM expenses WHERE  id = %s', (id,))
    row = cursor.fetchall()
   
    print(row[0])
    return render_template('edit.html', expenses = row[0])




@app.route('/update/<id>', methods = ['POST'])
def update(id):
  if request.method == 'POST' :
   
      date = request.form['date']
      expensename = request.form['expensename']
      amount = request.form['amount']
      paymode = request.form['paymode']
      category = request.form['category']
    
      cursor = mysql.connection.cursor()
       
      cursor.execute("UPDATE `expenses` SET `date` = % s , `expensename` = % s , `amount` = % s, `paymode` = % s, `category` = % s WHERE `expenses`.`id` = % s ",(date, expensename, amount, str(paymode), str(category),id))
      mysql.connection.commit()
      print('successfully updated')
      return redirect("/display")
     
    
logging.basicConfig(level=logging.DEBUG)

@app.route("/limit")
def limit():
    # Redirect to the limit overview page
    return redirect('/limitn')

@app.route("/limitnum", methods=['POST'])
def limitnum():   
    if request.method == "POST":
        try:
            # Retrieve limit number and limit type from the form
            limit_number = request.form['limit_number']
            limit_type = request.form['limit_type']  # Can be 'year', 'month', or 'day'

            # Ensure the user is logged in and session['id'] exists
            if 'id' not in session:
                logging.error("User is not logged in.")
                return redirect('/login')  # Redirect to login page if the user is not logged in

            # Validate limit_number (ensure it is a valid float)
            try:
                limit_number = float(limit_number)
                if limit_number <= 0:
                    logging.error(f"Invalid limit number: {limit_number}. It must be greater than 0.")
                    return "Limit number must be greater than 0."
            except ValueError:
                logging.error(f"Invalid input for limit_number: {limit_number}. Must be a numeric value.")
                return "Invalid limit number. Please enter a valid number."

            # Log the session ID and the values from the form
            logging.info(f"Session ID: {session.get('id')}")
            logging.info(f"Limit number: {limit_number}, Limit type: {limit_type}")

            # Create a cursor to interact with the database
            cursor = mysql.connection.cursor()

            # Insert or update the limit for the user in the database
            cursor.execute('''
                INSERT INTO limits (id, limit_type, limit_number, created_at) 
                VALUES (%s, %s, %s, NOW()) 
                ON DUPLICATE KEY UPDATE limit_number = %s, created_at = NOW()
            ''', (session['id'], limit_type, limit_number, limit_number))

            # Commit the transaction to save the changes in the database
            mysql.connection.commit()

            # Log the successful operation
            logging.info(f"Limit set successfully for user {session['id']} with limit_type: {limit_type} and amount: {limit_number}")

            # Redirect to the limit overview page after successful submission
            return redirect('/limitn')  

        except Exception as e:
            # Rollback the transaction in case of an error
            mysql.connection.rollback()
            logging.error(f"Error occurred while setting the limit: {str(e)}")
            return "An error occurred while setting the limit. Please try again later."

# Route to show the limit details
@app.route("/limitn")
def limitn():
    # Check if the user is logged in
    if 'id' not in session:
        return redirect('/login')  # Redirect to login page if the user is not logged in

    # Fetch the user's latest limit type from the database
    cursor = mysql.connection.cursor()
    cursor.execute('SELECT limit_type, limit_number FROM limits WHERE id = %s ORDER BY created_at DESC LIMIT 1', (session['id'],))
    x = cursor.fetchone()
    
    # Default values if no limit found
    limit_type = x[0] if x else 'month'
    limit_number = x[1] if x else 0

    # Make sure limit_number is treated as an integer
    try:
        limit_number = int(limit_number)
    except ValueError:
        limit_number = 0  # Default to 0 if it's not a valid number

    # Log the values
    logging.debug(f"Limit Type: {limit_type}, Limit Number: {limit_number}")

    # Render the template with the limit values
    return render_template("limit.html", y=limit_number, limit_type=limit_type)


#REPORT
@app.route("/today")
def today():
    cursor = mysql.connection.cursor()

    # Fetch today's expenses for summary
    cursor.execute('SELECT TIME(date), amount FROM expenses WHERE userid = %s AND DATE(date) = DATE(NOW())', (str(session['id'])))
    texpense = cursor.fetchall()  # Store the result here for use in the template

    cursor.execute('SELECT * FROM expenses WHERE userid = %s AND DATE(date) = DATE(NOW()) ORDER BY `expenses`.`date` DESC', (str(session['id'])))
    expense = cursor.fetchall()
    
    total = 0
    t_food = 0
    t_entertainment = 0
    t_business = 0
    t_rent = 0
    t_EMI = 0
    t_other = 0

    for x in expense:
        try:
            amount = float(x[4])  # Ensure that we are working with numbers
        except ValueError:
            # Skip or set to 0 if the conversion fails (e.g., 'cash' or other non-numeric value)
            amount = 0

        total += amount

        if x[6] == "food":
            t_food += amount
        elif x[6] == "entertainment":
            t_entertainment += amount
        elif x[6] == "business":
            t_business += amount
        elif x[6] == "rent":
            t_rent += amount
        elif x[6] == "EMI":
            t_EMI += amount
        elif x[6] == "other":
            t_other += amount

    return render_template("today.html", texpense=texpense, expense=expense, total=total,
                           t_food=t_food, t_entertainment=t_entertainment, t_business=t_business,
                           t_rent=t_rent, t_EMI=t_EMI, t_other=t_other)


     

@app.route("/month")
def month():
    cursor = mysql.connection.cursor()
    # Fetch expenses for the current month with daily summaries
    cursor.execute('SELECT DATE(date), SUM(amount) FROM expenses WHERE userid = %s AND MONTH(DATE(date)) = MONTH(now()) GROUP BY DATE(date) ORDER BY DATE(date)', (str(session['id'])))
    texpense = cursor.fetchall()  # Store the result for summary of expenses per day
    print(texpense)
    
    cursor = mysql.connection.cursor()
    # Fetch all expenses for the current month
    cursor.execute('SELECT * FROM expenses WHERE userid = %s AND MONTH(DATE(date)) = MONTH(now()) ORDER BY `expenses`.`date` DESC', (str(session['id'])))
    expense = cursor.fetchall()  # Store the result for detailed expense information
    
    total = 0
    t_food = 0
    t_entertainment = 0
    t_business = 0
    t_rent = 0
    t_EMI = 0
    t_other = 0

    # Process each expense to calculate totals for each category
    for x in expense:
        try:
            amount = float(x[4])  # Ensure that we are working with numbers
        except ValueError:
            amount = 0  # If there's an issue with converting, set it to 0

        total += amount  # Accumulate total amount

        # Categorize the expense based on its type
        if x[6] == "food":
            t_food += amount
        elif x[6] == "entertainment":
            t_entertainment += amount
        elif x[6] == "business":
            t_business += amount
        elif x[6] == "rent":
            t_rent += amount
        elif x[6] == "EMI":
            t_EMI += amount
        elif x[6] == "other":
            t_other += amount

    print(total)
    print(t_food)
    print(t_entertainment)
    print(t_business)
    print(t_rent)
    print(t_EMI)
    print(t_other)

    # Return the results to be rendered in the month.html template
    return render_template(
        "month.html", 
        texpense=texpense, 
        expense=expense, 
        total=total,
        t_food=t_food, 
        t_entertainment=t_entertainment,
        t_business=t_business, 
        t_rent=t_rent,
        t_EMI=t_EMI, 
        t_other=t_other
    )

                          
@app.route("/year")
def year():
    cursor = mysql.connection.cursor()
    # Fetch the sum of amounts grouped by month for the current year
    cursor.execute('SELECT MONTH(date), SUM(amount) FROM expenses WHERE userid= %s AND YEAR(DATE(date))= YEAR(now()) GROUP BY MONTH(date) ORDER BY MONTH(date)', (str(session['id'])))
    texpense = cursor.fetchall()
    print(texpense)

    cursor = mysql.connection.cursor()
    # Fetch all expenses for the current year
    cursor.execute('SELECT * FROM expenses WHERE userid = %s AND YEAR(DATE(date))= YEAR(now()) ORDER BY `expenses`.`date` DESC', (str(session['id'])))
    expense = cursor.fetchall()

    total = 0
    t_food = 0
    t_entertainment = 0
    t_business = 0
    t_rent = 0
    t_EMI = 0
    t_other = 0

    # Loop through the expenses and sum up the amounts
    for x in expense:
        try:
            amount = float(x[4])  # Convert the amount to a float
        except ValueError:
            amount = 0  # If the amount is not a valid number, set it to 0

        total += amount

        # Add to the category totals based on the type of expense
        if x[6] == "food":
            t_food += amount
        elif x[6] == "entertainment":
            t_entertainment += amount
        elif x[6] == "business":
            t_business += amount
        elif x[6] == "rent":
            t_rent += amount
        elif x[6] == "EMI":
            t_EMI += amount
        elif x[6] == "other":
            t_other += amount

    print(total)
    print(t_food)
    print(t_entertainment)
    print(t_business)
    print(t_rent)
    print(t_EMI)
    print(t_other)

    # Render the template with the data
    return render_template("today.html", texpense=texpense, expense=expense, total=total,
                           t_food=t_food, t_entertainment=t_entertainment,
                           t_business=t_business, t_rent=t_rent,
                           t_EMI=t_EMI, t_other=t_other)


#log-out

@app.route('/logout')

def logout():
   session.pop('loggedin', None)
   session.pop('id', None)
   session.pop('username', None)
   return render_template('home.html')

@app.route('/expenses')
def expenses():
    cursor = mysql.connection.cursor()
    cursor.execute('SELECT * FROM expenses WHERE userid = %s', (session['id'],))
    expenses = cursor.fetchall()
    cursor.close()
    return render_template('expenses.html', expenses=expenses)


if __name__ == "__main__":
    app.run(debug=True)