from flask import Flask, render_template, request, redirect, session 
import re
import os

from flask_db2 import DB2
import ibm_db
import ibm_db_dbi
from sendemail import sendgridmail,sendmail


app = Flask(__name__)

app.secret_key = 'a'
app.config['database'] = 'bludb'
app.config['hostname'] = "0c77d6f2-5da9-48a9-81f8-86b520b87518.bs2io90l08kqb1od8lcg.databases.appdomain.cloud"
app.config['port'] = '31198'
app.config['protocol'] = 'tcpip'
app.config['uid'] = 'wkz37381'
app.config['pwd'] = 'ALNECkPjmYyEIRAR'
app.config['security'] = 'SSL'
try:
    mysql = DB2(app)

    ibm_db_conn=ibm_db.connect("DATABASE=bludb;HOSTNAME=0c77d6f2-5da9-48a9-81f8-86b520b87518.bs2io90l08kqb1od8lcg.databases.appdomain.cloud;PORT=31198;UID=wkz37381;PWD=ALNECkPjmYyEIRAR;Security=SSL;","","")
    
    print("Database connected without any error !!")
except:
    print("IBM DB Connection error   :     " + DB2.conn_errormsg())    


@app.route("/home")
def home():
    return render_template("homepage.html")


@app.route("/")
def add():
    return render_template("login.html")


@app.route("/signup")
def signup():
    return render_template("signup.html")


@app.route("/add")
def adding():
    return render_template('add.html')


@app.route('/register', methods =['GET', 'POST'])
def register():
    msg = ''
    
    if request.method == 'POST' :
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        try:
            connectionID = ibm_db_dbi.connect(conn_str, '', '')
            cursor = connectionID.cursor()
        except:
            print("No connection Established")      

        sql = "SELECT * FROM register WHERE username = ?"
        stmt = ibm_db.prepare(ibm_db_conn, sql)
        ibm_db.bind_param(stmt, 1, username)
        ibm_db.execute(stmt)
        result = ibm_db.execute(stmt)
        account = ibm_db.fetch_row(stmt)

        param = "SELECT * FROM register WHERE username = " + "\'" + username + "\'"
        res = ibm_db.exec_immediate(ibm_db_conn, param)
        dictionary = ibm_db.fetch_assoc(res)
        while dictionary != False:
            dictionary = ibm_db.fetch_assoc(res)

        if account:
            msg = 'Username already exists !'
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            msg = 'Invalid email address !'
        elif not re.match(r'[A-Za-z0-9]+', username):
            msg = 'name must contain only characters and numbers !'
        else:
            sql2 = "INSERT INTO register (username, email,password) VALUES (?, ?, ?)"
            stmt2 = ibm_db.prepare(ibm_db_conn, sql2)
            ibm_db.bind_param(stmt2, 1, username)
            ibm_db.bind_param(stmt2, 2, email)
            ibm_db.bind_param(stmt2, 3, password)
            ibm_db.execute(stmt2)

            param = "SELECT id FROM register WHERE username = " + "\'" + username + "\'" + " and password = " + "\'" + password + "\'"
            res = ibm_db.exec_immediate(ibm_db_conn, param)
            dictionary = ibm_db.fetch_assoc(res)

            if dictionary != False:
                id = dictionary["ID"]

                sql = "INSERT INTO expenses_on_category (userid) VALUES (?)"
                stmt = ibm_db.prepare(ibm_db_conn, sql)
                ibm_db.bind_param(stmt, 1, int(id))
                ibm_db.execute(stmt)

            msg = 'You have successfully registered !'
        return render_template('signup.html', msg = msg)   
 
        
@app.route('/login',methods =['GET', 'POST'])
def login():
    global userid
    msg = ''
  
    if request.method == 'POST' :
        username = request.form['username']
        password = request.form['password']
        
        sql = "SELECT * FROM register WHERE username = ? and password = ?"
        stmt = ibm_db.prepare(ibm_db_conn, sql)
        ibm_db.bind_param(stmt, 1, username)
        ibm_db.bind_param(stmt, 2, password)
        result = ibm_db.execute(stmt)
        account = ibm_db.fetch_row(stmt)
        
        param = "SELECT * FROM register WHERE username = " + "\'" + username + "\'" + " and password = " + "\'" + password + "\'"
        res = ibm_db.exec_immediate(ibm_db_conn, param)
        dictionary = ibm_db.fetch_assoc(res)

        if account:
            session['loggedin'] = True
            session['id'] = dictionary["ID"]
            userid = dictionary["ID"]
            session['username'] = dictionary["USERNAME"]
            session['email'] = dictionary["EMAIL"]
           
            return redirect('/home')
        else:
            msg = 'Incorrect username / password !'
        
    return render_template('login.html', msg = msg)


@app.route('/addexpense',methods=['GET', 'POST'])
def addexpense():
    
    date = request.form['date']
    expensename = request.form['expensename']
    amount = request.form['amount']
    paymode = request.form['paymode']
    category = request.form['category']

    p1 = date[0:10]
    p2 = date[11:13]
    p3 = date[14:]
    p4 = p1 + "-" + p2 + "." + p3 + ".00"

    sql = "INSERT INTO expenses (userid, date, expensename, amount, paymode, category) VALUES (?, ?, ?, ?, ?, ?)"
    stmt = ibm_db.prepare(ibm_db_conn, sql)
    ibm_db.bind_param(stmt, 1, session['id'])
    ibm_db.bind_param(stmt, 2, p4)
    ibm_db.bind_param(stmt, 3, expensename)
    ibm_db.bind_param(stmt, 4, amount)
    ibm_db.bind_param(stmt, 5, paymode)
    ibm_db.bind_param(stmt, 6, category)
    ibm_db.execute(stmt)

    print("Expenses added")

    sql = "SELECT "+str(category)+" , total FROM expenses_on_category WHERE userid = " + str(session['id'])
    res = ibm_db.exec_immediate(ibm_db_conn, sql)
    dictionary = ibm_db.fetch_assoc(res)
    total = 0
    category_amount = 0
    if dictionary != False:
        category_amount = dictionary[str(category).upper()]
        total = dictionary["TOTAL"]
    
    total += int(amount)
    category_amount += int(amount)

    sql = "UPDATE expenses_on_category SET "+str(category)+" = ? , total = ? WHERE userid = ?"
    stmt = ibm_db.prepare(ibm_db_conn, sql)
    ibm_db.bind_param(stmt, 1, category_amount )
    ibm_db.bind_param(stmt, 2, total )
    ibm_db.bind_param(stmt, 3, str(session['id']))
    ibm_db.execute(stmt)

    print("Expenses On Category added")

    param = "SELECT * FROM expenses WHERE userid = " + str(session['id']) + " AND MONTH(date) = MONTH(current timestamp) AND YEAR(date) = YEAR(current timestamp) ORDER BY date DESC"
    res = ibm_db.exec_immediate(ibm_db_conn, param)
    dictionary = ibm_db.fetch_assoc(res)
    expense = []
    while dictionary != False:
        temp = []
        temp.append(dictionary["ID"])
        temp.append(dictionary["USERID"])
        temp.append(dictionary["DATE"])
        temp.append(dictionary["EXPENSENAME"])
        temp.append(dictionary["AMOUNT"])
        temp.append(dictionary["PAYMODE"])
        temp.append(dictionary["CATEGORY"])
        expense.append(temp)
        dictionary = ibm_db.fetch_assoc(res)

    total=0
    for x in expense:
          total += x[4]

    param = "SELECT id, limitss FROM limits WHERE userid = " + str(session['id']) + " ORDER BY id DESC LIMIT 1"
    res = ibm_db.exec_immediate(ibm_db_conn, param)
    dictionary = ibm_db.fetch_assoc(res)
    row = []
    s = 0
    while dictionary != False:
        temp = []
        temp.append(dictionary["LIMITSS"])
        row.append(temp)
        dictionary = ibm_db.fetch_assoc(res)
        s = temp[0]

    if total > int(s):
        msg = "Hello " + session['username'] + " , " + "you have crossed the monthly limit of Rs. " + str(s) + "/- !!!" + "\n" + "Thank you, " + "\n" + "Team Personal Expense Tracker."  
        sendmail(msg,session['email'])  
    
    return redirect("/display")


@app.route("/display")
def display():

    param = "SELECT * FROM expenses WHERE userid = " + str(session['id']) + " ORDER BY date DESC"
    res = ibm_db.exec_immediate(ibm_db_conn, param)
    dictionary = ibm_db.fetch_assoc(res)
    expense = []
    while dictionary != False:
        temp = []
        temp.append(dictionary["ID"])
        temp.append(dictionary["USERID"])
        temp.append(dictionary["DATE"])
        temp.append(dictionary["EXPENSENAME"])
        temp.append(dictionary["AMOUNT"])
        temp.append(dictionary["PAYMODE"])
        temp.append(dictionary["CATEGORY"])
        expense.append(temp)
        dictionary = ibm_db.fetch_assoc(res)

    param = "SELECT * FROM expenses_on_category WHERE userid = " + str(session['id'])
    res = ibm_db.exec_immediate(ibm_db_conn, param)
    dictionary = ibm_db.fetch_assoc(res)
    expenses_on_category = [0,0,0,0,0,0,0]
    while dictionary != False:
        temp = []
        temp.append(dictionary["FOOD"])
        temp.append(dictionary["ENTERTAINMENT"])
        temp.append(dictionary["BUSINESS"])
        temp.append(dictionary["RENT"])
        temp.append(dictionary["EMI"])
        temp.append(dictionary["OTHER"])
        temp.append(dictionary["TOTAL"])
        expenses_on_category = temp
        dictionary = ibm_db.fetch_assoc(res)

    return render_template('display.html' ,expense = expense,expenses_on_category = expenses_on_category)
                          

@app.route('/delete/<string:id>', methods = ['POST', 'GET' ])
def delete(id):

    param = "SELECT * FROM expenses WHERE id = " + id
    res = ibm_db.exec_immediate(ibm_db_conn, param)
    dictionary = ibm_db.fetch_assoc(res)
    expenses = []
    if dictionary != False:
        temp = []
        temp.append(dictionary["CATEGORY"])
        temp.append(dictionary["AMOUNT"])
        expenses = temp

    param = "SELECT "+str(expenses[0])+" , total FROM expenses_on_category WHERE userid = " + str(session['id'])
    res = ibm_db.exec_immediate(ibm_db_conn, param)
    dictionary = ibm_db.fetch_assoc(res)
    expenses_on_category = []
    if dictionary != False:
        temp = []
        temp.append(dictionary[ str(expenses[0]).upper() ])
        temp.append(dictionary["TOTAL"])
        expenses_on_category = temp

    sql = "UPDATE expenses_on_category SET "+str(expenses[0])+" = ? , total = ? WHERE userid = ?"
    stmt = ibm_db.prepare(ibm_db_conn, sql)
    ibm_db.bind_param(stmt, 1, int(expenses_on_category[0])-int(expenses[1]) )
    ibm_db.bind_param(stmt, 2, int(expenses_on_category[1])-int(expenses[1]) )
    ibm_db.bind_param(stmt, 3, str(session['id']))
    ibm_db.execute(stmt)

    param = "DELETE FROM expenses WHERE  id = " + id
    res = ibm_db.exec_immediate(ibm_db_conn, param)

    print('Deleted successfully')    
    return redirect("/display")
 

@app.route('/edit/<id>', methods = ['POST', 'GET' ])
def edit(id):

    param = "SELECT * FROM expenses WHERE  id = " + id
    res = ibm_db.exec_immediate(ibm_db_conn, param)
    dictionary = ibm_db.fetch_assoc(res)
    row = []
    while dictionary != False:
        temp = []
        temp.append(dictionary["ID"])
        temp.append(dictionary["USERID"])
        temp.append(dictionary["DATE"])
        temp.append(dictionary["EXPENSENAME"])
        temp.append(dictionary["AMOUNT"])
        temp.append(dictionary["PAYMODE"])
        temp.append(dictionary["CATEGORY"])
        row.append(temp)
        dictionary = ibm_db.fetch_assoc(res)

    return render_template('edit.html', expenses = row[0])


@app.route('/update/<id>', methods = ['POST'])
def update(id):
    if request.method == 'POST' :
        date = request.form['date']
        expensename = request.form['expensename']
        amount = request.form['amount']
        paymode = request.form['paymode']
        category = request.form['category']

        p1 = date[0:10]
        p2 = date[11:13]
        p3 = date[14:]
        p4 = p1 + "-" + p2 + "." + p3 + ".00"

        sql = "UPDATE expenses SET date = ? , expensename = ? , amount = ?, paymode = ?, category = ? WHERE id = ?"
        stmt = ibm_db.prepare(ibm_db_conn, sql)
        ibm_db.bind_param(stmt, 1, p4)
        ibm_db.bind_param(stmt, 2, expensename)
        ibm_db.bind_param(stmt, 3, amount)
        ibm_db.bind_param(stmt, 4, paymode)
        ibm_db.bind_param(stmt, 5, category)
        ibm_db.bind_param(stmt, 6, id)
        ibm_db.execute(stmt)

        print('Successfully updated')
        return redirect("/display")
     
      
@app.route("/changelimit" , methods = ['POST' ])
def changelimit():
     if request.method == "POST":
        number= request.form['number']

        sql = "INSERT INTO limits (userid, limitss) VALUES (?, ?)"
        stmt = ibm_db.prepare(ibm_db_conn, sql)
        ibm_db.bind_param(stmt, 1, session['id'])
        ibm_db.bind_param(stmt, 2, number)
        ibm_db.execute(stmt)
        
        return redirect('/limit')
     
         
@app.route("/limit") 
def limit():
    
    param = "SELECT id, limitss FROM limits WHERE userid = " + str(session['id']) + " ORDER BY id DESC LIMIT 1"
    res = ibm_db.exec_immediate(ibm_db_conn, param)
    dictionary = ibm_db.fetch_assoc(res)
    row = []
    s = " /-"
    while dictionary != False:
        temp = []
        temp.append(dictionary["LIMITSS"])
        row.append(temp)
        dictionary = ibm_db.fetch_assoc(res)
        s = temp[0]
    
    return render_template("limit.html" , y= s)


@app.route("/totalexpense", methods = ['POST', 'GET' ])
def totalexpense():

    if request.method == 'GET' :
        period = request.args.get('period')
        print(period)

        today_attributes = ["TN","AMOUNT"]
        month_attributes = ["DT","TOT"]
        year_attributes = ["MN","TOT"]

        current_attributes = []

        if period == "today":
            current_attributes = today_attributes
            param = "SELECT TIME(date) as tn, amount FROM expenses WHERE userid = " + str(session['id']) + " AND DATE(date) = DATE(current timestamp) ORDER BY date DESC"
        elif period == "month":
            current_attributes = month_attributes
            param = "SELECT DATE(date) as dt, SUM(amount) as tot FROM expenses WHERE userid = " + str(session['id']) + " AND MONTH(date) = MONTH(current timestamp) AND YEAR(date) = YEAR(current timestamp) GROUP BY DATE(date) ORDER BY DATE(date)"
        else:
            current_attributes = year_attributes
            param = "SELECT MONTH(date) as mn, SUM(amount) as tot FROM expenses WHERE userid = " + str(session['id']) + " AND YEAR(date) = YEAR(current timestamp) GROUP BY MONTH(date) ORDER BY MONTH(date)"
        
        resultSet = ibm_db.exec_immediate(ibm_db_conn, param)
        dictionary = ibm_db.fetch_assoc(resultSet)
        total_expenses = []

        while dictionary != False:
            temp = []
            print(current_attributes)
            temp.append(dictionary[ current_attributes[0] ])
            temp.append(dictionary[ current_attributes[1] ])
            total_expenses.append(temp)
            dictionary = ibm_db.fetch_assoc(resultSet)

        if period == "today":
            param = "SELECT * FROM expenses WHERE userid = " + str(session['id']) + " AND DATE(date) = DATE(current timestamp) ORDER BY date DESC"
        elif period == "month":
            param = "SELECT * FROM expenses WHERE userid = " + str(session['id']) + " AND MONTH(date) = MONTH(current timestamp) AND YEAR(date) = YEAR(current timestamp) ORDER BY date DESC"
        else:
            param = "SELECT * FROM expenses WHERE userid = " + str(session['id']) + " AND YEAR(date) = YEAR(current timestamp) ORDER BY date DESC"

        resultSet = ibm_db.exec_immediate(ibm_db_conn, param)
        dictionary = ibm_db.fetch_assoc(resultSet)
        expense = []
        while dictionary != False:
            temp = []
            temp.append(dictionary["ID"])
            temp.append(dictionary["USERID"])
            temp.append(dictionary["DATE"])
            temp.append(dictionary["EXPENSENAME"])
            temp.append(dictionary["AMOUNT"])
            temp.append(dictionary["PAYMODE"])
            temp.append(dictionary["CATEGORY"])
            expense.append(temp)
            dictionary = ibm_db.fetch_assoc(resultSet)


        total=0
        total_food=0
        total_entertainment=0
        total_business=0
        total_rent=0
        total_EMI=0
        total_other=0

        
        for x in expense:

            total += x[4]

            if x[6] == "food":
                total_food += x[4]
            elif x[6] == "entertainment":
                total_entertainment  += x[4]
            elif x[6] == "business":
                total_business  += x[4]
            elif x[6] == "rent":
                total_rent  += x[4]
            elif x[6] == "EMI":
                total_EMI  += x[4]
            elif x[6] == "other":
                total_other  += x[4]
        
        return render_template("totalexpense.html", texpense = total_expenses, expense = expense,  total = total ,
                            t_food = total_food,t_entertainment =  total_entertainment,
                            t_business = total_business,  t_rent =  total_rent, 
                            t_EMI =  total_EMI,  t_other =  total_other )


@app.route('/logout')
def logout():
   session.pop('loggedin', None)
   session.pop('id', None)
   session.pop('username', None)
   session.pop('email', None)
   return render_template('login.html')


if __name__ == "__main__":
    app.secret_key = os.urandom(12)
    app.run(debug=True, host='0.0.0.0', port='7777')