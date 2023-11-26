# general
# -------------------------------------------------------------------------#
from flask import Flask, render_template, redirect, request, session, send_file, jsonify
import sqlite3, datetime, pandas
import random
from flask_cors import CORS
from flask_mail import Mail, Message
from tools import query,create_request_number

app = Flask(__name__)

CORS(app, headers='Content-Type')
app.secret_key = 'fghdfghdfgh'

# test

def users_data():
    rows = (query(f"SELECT * FROM users "))
    table = []
    for row in rows:
        table.append({'name': row[0], 'username': row[1], 'password': row[2], 'email': row[3], 'team': row[4]})
    return table


users_table = users_data()


def items_data():
    rows = (query(f"SELECT * FROM items "))
    table = []
    for row in rows:
        table.append({'mkt': row[0], 'category': row[1], 'item_name': row[2], 'quantity': row[3], 'added by': row[4],
                      'entrance date': row[5], 'updaating date': row[6]})
    return table


items_table = items_data()


def requests_data():
    rows = (query(f"SELECT * FROM requests "))
    table = []
    for row in rows:
        table.append(
            {'request_number': row[0], 'username': row[1], 'items': row[2], 'quantity': row[3], 'taking date': row[4],
             'returning date': row[5]})
    return table

requests_table = requests_data()



# Users - login-register-homepage
# -------------------------------------------------------------------------#
# homepage
@app.route('/')
def home():
    if session.get('username') == None:
        return redirect('/login')

    for user in users_table:
        if session.get('username') == user['username']:
            return render_template('home.html', username=session['username'])
    return redirect('/login')


# login
@app.route('/login', methods=["POST", 'GET'])
def login():
    if request.method == 'GET':
        return render_template('login.html')
    username = request.form.get('username')
    password = request.form.get('password')
    for user in users_table:
        if ((username == user['username']) and (password == user['password'])):
            session['username'] = username
            return redirect('/')
    return redirect('/register')


# register
@app.route('/register', methods=["POST", 'GET'])
def register():
    if users_table == []:
        query(
            f"INSERT INTO users VALUES('{request.form['name']}' ,'{request.form['username']}' , '{request.form['password']}' , '{request.form['phone']}' , '{request.form['email']}', '{request.form['team']}' )")
        session['username'] = request.form['username']
        send_mail()
        return redirect('/')

    if request.method == 'GET':
        return render_template('register.html')

    new_user = request.form['username']
    for user in users_table:
        if new_user == user['username']:
            return render_template('register.html')

    query(
        f"INSERT INTO users VALUES('{request.form['name']}' ,'{request.form['username']}' , '{request.form['password']}' , '{request.form['phone']}' , '{request.form['email']}', '{request.form.get('team')}' )")

    session['username'] = request.form['username']
    send_mail()
    return redirect('/')


@app.route('/forgot_password', methods=['POST', 'GET'])
def forgot_password():
    new_password = request.form.get('new_password')
    username = request.form.get('username')
    for user in users_table:
        if (username == user['username']):
            query(f"UPDATE users SET password='{new_password}'WHERE username='{username}'")
            return redirect('/login')

    return render_template('forgot_password.html')



# requests
# ----------------------------------------------------------------------------------#

@app.route('/requests', methods=['POST', 'GET'])
def requests():
    users_table = users_data()
    app.logger.info(users_table)
    app.logger.info(session.get('username'))
    # checking validation & return template
    for user in users_table:
        if session.get('username') == user['username']:
            return render_template('requests.html')

    return redirect('/login')


# print the json that received from the client
@app.route('/get_data_requests', methods=['POST', 'GET'])
def gal_requests():
    if request.method == 'POST':
        data = request.get_json()  # Get the JSON data from the request
        items = data.get('items', None)  # Safely access 'items' key from the data
        if items is None:
            return jsonify({'error': 'No items data provided'}), 400  # Return error if 'items' key is missing
        app.logger.info(items)  # Log the items data
        return jsonify(items)  # Return the items data as JSON



# return all items in stock
# example data for the requests page
@app.route('/item/quantity/', methods=['GET'])
def send_item_instock():
    chosen_item = request.args.get('Item')
    rows = (query(f"SELECT quantity_in_stock FROM items WHERE item_name='{chosen_item}'"))
    item = []
    for row in rows:
        item.append({'quantity': row[1]})
    return jsonify(item)
    


# example data for the requests page
@app.route('/user/requests', methods=['GET'])
def user_requests():
    username = session['username']
    rows = (query(f"SELECT * FROM requests WHERE username='{username}'"))
    requests = []
    for row in rows:
        requests.append({'request_number': row[0],'username':row[1],'items':row[2],'quantity':row[3],'taking_date':row[4],'returning_date':row[5],'status':row[6],'sending_date':row[7],'updated_at':row[8]})
    return jsonify(requests)







# the new route that handle both get and post methods for the new requests
# eyal !! need to fix it to work with the new requests page
@app.route('/new_requests', methods=['POST', 'GET'])
def new_requests():
    if request.method == 'GET':
        username = session.get('username')
        users = users_data()
        for user in users:
            if username == user['username']:
                return render_template('new_add_request.html')
        return redirect('/login')
    
    elif request.method == 'POST':
        try:
            request_number = create_request_number()
            username = session.get('username')
            quantity = request.form.get('quantity')
            items = request.form['Item']
            taking_date = request.form.get('taking_date')
            returning_date = request.form.get('returning_date')
            status = "not approved"
            comment = None
           
            # quantity_in_stock = query(f"SELECT quantity_in_stock FROM item WHERE item ='{items}'")
            query(f"INSERT INTO requests VALUES('{request_number}', '{username}','{items}', {quantity}, '{taking_date}', '{returning_date}','{status}','{datetime.datetime.today()}','{datetime.datetime.today()}','{comment}')")
            query(f"UPDATE items SET quantity_in_stock = quantity_in_stock - '{int(quantity)}' WHERE item_name ='{request.form.get('Item')}'")
            return render_template('new_add_requests.html')
        except:
            return "item not available"


# add request to db & updates the tables
@app.route('/insert_requests', methods=['POST', 'GET'])
def insert_requests():
    try:
        request_number = create_request_number()
        username = session.get('username')
        quantity = request.form.get('quantity')
        items = request.form['Item']
        taking_date = request.form.get('taking_date')
        returning_date = request.form.get('returning_date')
        status = "not approved"
        query(
            f"INSERT INTO requests VALUES('{request_number}', '{username}','{items}', '{quantity}', '{taking_date}', '{returning_date}','{status}','{datetime.datetime.today()}','{datetime.datetime.today()}')")
        query(
            f"UPDATE items SET quantity_in_stock = quantity_in_stock - '{int(quantity)}' WHERE item_name ='{request.form.get('Item')}'")
        return render_template('new_add_requests.html')
    except:
        return "item not available"



# return all items per category
@app.route('/select_category', methods=["GET"])
def add_item_request():
    chosen_category = request.args.get('category')
    rows = query(f"SELECT mkt,item_name FROM items WHERE category='{chosen_category}'")
    items = []
    for row in rows:
        items.append({'mkt': row[0], 'item_name': row[1]})
    return jsonify(items)



# close an open request
@app.route('/close_request',methods =['GET','POST'])
def close_request():
    request_number = request.form.get('request_number')
    status = request.form.get('status')
    comment = request.form.get('comment')
    updated_at = datetime.datetime.now()
    query_answer = query(f"SELECT request_number FROM requests WHERE request_number='{request_number}'")
    if (query_answer):
        query(f"UPDATE requests SET status = '{status}' WHERE request_number = '{request_number}'")
        query(f"UPDATE requests SET comment = '{comment}' WHERE request_number = '{request_number}'")
        query(f"UPDATE requests SET updated_at = '{updated_at}' WHERE request_number = '{request_number}'")
        print(send_mail())

    return render_template('close_requests.html')



#sending email
mail = Mail(app)
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = 'govawarehouse@gmail.com'
app.config['MAIL_PASSWORD'] = 'smem ofsw qlko itvn'  
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
mail = Mail(app)

def send_mail():
    if request.method == 'POST':
        url = request.url
        if '/close_request' in url:
            username=session.get('username')
            recipient_email_query = (query(f"SELECT email FROM users WHERE username='{username}'"))
            recipient_email = recipient_email_query[0][0]
            request_number = request.form.get('request_number')
            subject = f'Request number #{request_number}'
            msg = Message(subject, sender='govawarehouse@gmail.com', recipients=[recipient_email])
            msg.body = f'''Hello your request number {request_number} has been closed successfully.
            Thank you
            - Tech support - '''
            mail.send(msg)
            return "Email sent successfully."
        
        elif '/register' in url:
            username=session.get('username')
            recipient_email = request.form.get('email')
            subject = f'{username } registration'
            msg = Message(subject, sender='govawarehouse@gmail.com', recipients=[recipient_email])
            msg.body = f'''Hello {username} 
            Thank you for your registration. 
            have a nice day 
            -Tech support- '''
            mail.send(msg)
            return "Email sent successfully."
        

        elif '/forgot_password' in url:
            username =session.get('username')
            recipient_email_query = (query(f"SELECT email FROM users WHERE username='{username}'"))
            recipient_email = recipient_email_query[0][0]
            subject = f"Reset password for - {username}"
            msg = Message(subject, sender='govawarehouse@gmail.com', recipients=[recipient_email])
            msg.body = f'''Hello the password for {username} has been reset successfully.
            Thank you
            - Tech support - '''
            mail.send(msg)
            return "Email sent successfully."










# Exit
# ----------------------------------------------------------------------------------#
@app.route('/exit')
def exit():
    session['username'] = None
    return redirect('/login')


# Superuser
# ----------------------------------------------------------------------------------#
@app.route('/admin')
def admin():
    if session.get('username') == 'admin':
        return render_template('admin.html')
    else:
        return render_template('admin_error.html')


# - user
# ----------------------------------------------------------------------------------#

# users menu - admin
@app.route('/admin/users_menu')
def users_menu():
    username = session.get('username')
    if username != 'admin':
        return redirect('/')
    return render_template('users_menu.html')


# delete user
@app.route('/admin/users_menu/delete', methods=['GET', 'POST'])
def delete_user():
    deleted_user = request.form.get('username')
    query(f"DELETE FROM users WHERE username='{deleted_user}'")

    return render_template('delete_user.html')


# export users table to excel
@app.route('/download_excel_users', methods=['GET', 'POST'])
def excel_users():
    with sqlite3.connect('users.db') as conn:
        query1 = "SELECT * FROM users"
        df = pandas.read_sql_query(query1, conn)
    df.to_excel('users.xlsx', index=False)
    return send_file(
        'users.xlsx',
        as_attachment=True,
        download_name='users_data.xlsx',
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )


# items
# -------------------------------------------------------------------------------------#

# items menu
@app.route('/items')
def items():
    if session.get('username') != 'admin':
        return redirect('/')
    return render_template('items_menu.html')


# add items
@app.route('/items/add_items', methods=['GET', 'POST'])
def get_items():
    if session.get('username') != 'admin':
        return redirect('/')

    # for item in items_table:
    #     if request.form.get("mkt") == item["mkt"]:
    #        return render_template('add_items.html')

    query(
        f"INSERT INTO items VALUES('{request.form.get('mkt')}', '{request.form.get('category')}', '{request.form.get('item_name')}', '{request.form.get('quantity')}','{request.form.get('quantity')}' ,'{request.form.get('added_by')}','{request.form.get('entrance_date')}','{datetime.datetime.now()}')")
    return render_template('add_items.html')


# update items
@app.route('/admin/items/update', methods=['GET', 'POST'])
def update_items():
    if session.get('username') != 'admin':
        return redirect('/')

    for item in items_table:
        if request.form.get('mkt') == item['mkt']:
            query(
                f"UPDATE items SET quantity= quantity +'{int(request.form.get('quantity'))}' WHERE mkt='{request.form.get('mkt')}'")
            query(
                f"UPDATE items SET quantity_in_stock = quantity_in_stock +'{int(request.form.get('quantity'))}' WHERE mkt='{request.form.get('mkt')}'")

    query(f"UPDATE items SET added_by='{request.form.get('added_by')}' WHERE mkt='{request.form.get('mkt')}'")
    query(f"UPDATE items SET updating_date='{datetime.datetime.now()}' WHERE mkt='{request.form.get('mkt')}'")
    return render_template('update_items.html')


# delete_item from db
@app.route('/admim/items/delete', methods=['GET', 'POST'])
def delete_item():
    query(f"DELETE FROM items WHERE mkt='{request.form.get('mkt')}'")
    return render_template('delete_items.html')


# export items table to excel
@app.route('/download_file', methods=['GET', 'POST'])
def excel_items():
    with sqlite3.connect('users.db') as conn:
        query1 = "SELECT * FROM items"
        df = pandas.read_sql_query(query1, conn)
    df.to_excel('items.xlsx', index=False)
    return send_file(
        'items.xlsx',
        as_attachment=True,
        download_name='items_data.xlsx',
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )


# requests
# -------------------------------------------------------------------------------------#

# requests menu
@app.route('/requests_menu')
def requests_menu():
    if session.get('username') != 'admin':
        return redirect('/')
    return render_template('requests_menu.html')




#search a request
@app.route('/search_request', methods=['GET', 'POST'])
def search_request():
    if request.method == 'GET':
        return render_template('search_request.html')
    elif request.method == 'POST':
        request_num = request.form.get('request_number')
        requests = (query(f"SELECT items,quantity FROM requests WHERE request_number='{request_num}'"))
        items = []
        for row in requests:
            items.append({'item': row[0],'quantity':row[1]})
        return jsonify(items)
    






# delete request from db
@app.route('/requests_menu/delete_requests', methods=['GET', 'POST'])
def delete_request():
    request_number = request.form.get('request_number')
    query(f"DELETE FROM requests WHERE request_number='{request_number}'")
    return render_template('delete_requests.html')


# update request from db
@app.route('/requests_menu/update_requests')
def update_requests():
    request_number = request.form.get('request_munber')
    category = request.form.get('category')
    item_name = request.form.get('item_name')
    quantity = request.form.get('quantity')
    taking_date = request.form.get('taking_date')
    returning_date = request.form.get('returning_date')
    status = request.form.get('status')
    updated_at = datetime.datetime.today()
    comment = None

    for requests in requests_table:
        if request_number == requests['request_number']:
            query(f"UPDATE requests SET category='{category}' WHERE request_number='{request_number}'")
            query(f"UPDATE requests SET items='{item_name}' WHERE request_number='{request_number}'")
            query(f"UPDATE requests SET quantity='{quantity}' WHERE request_number='{request_number}'")
            query(f"UPDATE requests SET taking_date='{taking_date}' WHERE request_number='{request_number}'")
            query(f"UPDATE requests SET returning_date='{returning_date}' WHERE request_number='{request_number}'")
            query(f"UPDATE requests SET status='{status}' WHERE request_number='{request_number}'")
            query(f"UPDATE requests SET updated_at='{updated_at}' WHERE request_number='{request_number}'")
            query(f"UPDATE requests SET comment='{comment}' WHERE request_number='{request_number}'")
    return render_template('update_request.html')


# export requests table to excel
@app.route('/download_excel_requests', methods=['GET', 'POST'])
def excel_requests():
    with sqlite3.connect('users.db') as conn:
        query1 = "SELECT * FROM requests"
        df = pandas.read_sql_query(query1, conn)
    df.to_excel('requests.xlsx', index=False)
    return send_file(
        'requests.xlsx',
        as_attachment=True,
        download_name='requests_data.xlsx',
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
