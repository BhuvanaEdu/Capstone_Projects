from flask import Flask, request, render_template, redirect, url_for,jsonify,session,flash
# from flask_jwt_extended import JWTManager, jwt_required, create_access_token, get_jwt_identity
from pymongo import MongoClient
from werkzeug.security import generate_password_hash, check_password_hash
from flask_session import Session
from functools import wraps
import os
# from uuid import uuid4
from bson import json_util
from bson import ObjectId

app = Flask(__name__)

client = MongoClient('mongodb://localhost:27017/')
db = client['Effort_Estimation_Tool']  
data_collection = db['users']
estimation_data_collection = db['estimations']
historical_data_collection = db['historical_estimations']
app.secret_key ='aaab9a987171894123ea78d372c534ff5c5830c189df5a4869a39430c6de3975'


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=["GET", "POST"])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = generate_password_hash(request.form['password'])

        if data_collection.find_one({'email': email}):
            return render_template('register.html', msg='Email is already registered')
        else:
            data_collection.insert_one({'username': username, 'email': email, 'password': password})
            return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=["GET", "POST"])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = data_collection.find_one({'email': email})
        if user and check_password_hash(user['password'], password):
            session['email'] = email
            return redirect(url_for('dashboard'))
        else:
            return render_template('login.html', msg='Invalid email or password')
    return render_template('login.html')


def login_required(func):
    @wraps(func)
    def inner():
        if 'email' not in session:
            flash('Please log in first!', 'error')
            return redirect(url_for('login'))
        return func()
    return inner

@app.route('/dashboard')
@login_required
def dashboard():
    logged_user = data_collection.find_one({'email':session['email']})
    if logged_user:
        username = logged_user['username']
        return render_template('dashboard.html',username=username)
    flash('User not found','error')
    return render_template('dashboard.html')



@app.route('/submit_estimation', methods=["GET","POST"])
@login_required
def submit_estimation():
    logged_user = data_collection.find_one({'email':session['email']})
    if logged_user:
        if request.method == 'POST':
            data = request.get_json()
            tittle = data['tittle']
            complexity = data['complexity']
            size = data['size']
            type = data['type']
            description = data['description']
           

            estimation_data_collection.insert_one({
                'tittle': tittle,
                'complexity': complexity,
                'size': size,
                'type': type,
                'description': description
            })

            return jsonify({'message': 'Estimation submitted successfully'}), 201
        return render_template('submit_estimation.html')

@app.route('/calculate_estimation', methods=["GET","POST"])
def calculate_estimation():
    data = request.get_json()
    # id = data['id']
    tittle = data['tittle']
    complexity = data['complexity']
    size = data['size']
    type = data['type']

    historical_data = estimation_data_collection.find({'type': type}) 
    # print(historical_data)
    his_data = list(historical_data)
    data_len = len(his_data )
    size_values = {"small":  4, "medium":  6, "large":  8}
    cal_size = 0
    for i in his_data :
        for key,value in i.items():
            if key == "size":
                cal_size += size_values[value]
        # print(cal_size)
    
        estimated_effort = cal_size / data_len

        def confidence_level(estimated_effort):
            if estimated_effort <=4:
                return "low"
            elif estimated_effort <=6:
                return "medium"
            elif estimated_effort <=8:
                return "high"

    def estimated_range(estimated_effort):
        if estimated_effort <= 4:
            return '3-4'
        elif estimated_effort <= 6:
            return '4-6'
        else:
            return '6-8'
            
    estimated_effort = estimated_effort
    confidence_level = confidence_level(estimated_effort)
    estimated_range = estimated_range(estimated_effort)

        # Insert the data into historical_data_collection
    historical_data_collection.insert_one({
            # '_id': ObjectId(id),
            'tittle':tittle,
            'estimated_effort': estimated_effort,
            'confidence_level': confidence_level,
            'estimated_range': estimated_range
        })
    return jsonify({'estimated_effort': estimated_effort, 'confidence_level': confidence_level,'estimated_range': estimated_range}), 200



@app.route('/get_historical', methods=["GET"])
@login_required
def show_historical_data():
    logged_user = data_collection.find_one({'email':session['email']})
    if logged_user:
        if 'email' in session:
            logged_user = data_collection.find_one({'email': session['email']})
            if logged_user:
                historical_data = list(estimation_data_collection.find())
                # print(historical_data)
                return render_template('get_historical.html', data=historical_data)
            flash('User not found', 'error')
            return redirect(url_for('login'))
        else:
            flash('User not logged in', 'error')
            return redirect(url_for('login'))

@app.route('/update_estimation_data_collection/<string:id>', methods=["GET", "POST"])
def update_estimation_data_collection(id):
    task = estimation_data_collection.find_one({'_id':ObjectId(id)})
   
    if request.method == 'POST':
        print("post")
        tittle = request.form.get('tittle')
        complexity = request.form.get('complexity')
        size = request.form.get('size')
        type = request.form.get('type')
        description = request.form.get('description')

        print(tittle)
        task_data = {}

        if tittle is not None:
            task_data['tittle'] = tittle
        
        if complexity is not None:
            task_data['complexity'] = complexity
        if size is not None:
            task_data['size'] = size
        if type is not None:
            task_data['type'] = type
        if description is not None:
            task_data['description'] = description
        
        print(task)
        query = {"_id": ObjectId(id)}
        content = {"$set": task_data}
        
        result = estimation_data_collection.find_one_and_update(query, content, upsert=False)
        if result:
            return jsonify({'message': 'Update Estimation Data collection form updated successfully'}), 201
        else:
            return jsonify("Task not found")
    return render_template('update_estimation_data_collection.html', task=task)


@app.route("/his_delete_item/<string:id>", methods=["GET", "POST"])
def his_delete_item(id):
    his_data = estimation_data_collection.find_one({"_id":ObjectId(str(id))})
    if his_data:
        estimation_data_collection.delete_one({"_id":ObjectId(str(id))})
        return redirect(url_for("show_historical_data"))
    else:
        return "Data Not availeble"



@app.route('/logout')
def logout():
    session.pop('email',None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True, port=5555)

