from flask import Flask, request, render_template,jsonify
import tensorflow as tf
import numpy as np
import json
import os
from PIL import Image
import sqlite3
import base64

database="new.db"

def createtable():
    conn=sqlite3.connect(database)
    cursor=conn.cursor()
    cursor.execute("create table if not exists register (id integer primary key autoincrement, name text, mail text, password text)")   
    conn.commit()
    conn.close()
createtable()

conn = sqlite3.connect(database)
cursor = conn.cursor()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS plant_medi (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_name TEXT NOT NULL,
        product_price REAL NOT NULL,
        stock TEXT NOT NULL,
        brand_name TEXT NOT NULL,
        category TEXT NOT NULL,
        description TEXT NOT NULL,
        image BLOB NOT NULL
    )
''')
cursor.execute('''
CREATE TABLE IF NOT EXISTS cart (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    mail TEXT NOT NULL,
    product_name TEXT NOT NULL,
    product_price REAL NOT NULL,
    product_brand TEXT NOT NULL
    
)
''')

app = Flask(__name__)

device = "/gpu:0" if tf.config.list_physical_devices('GPU') else "/cpu:0"

with open('data1.json', 'r') as f:
    plant_data = json.load(f)

# Load TensorFlow models
model1 = tf.keras.models.load_model('model1.h5')


@app.route('/index',methods=["GET","POST"])
def index1():
        return render_template('index.html')


@app.route('/',methods=["GET","POST"])
def index():
        return render_template('login.html')
    
@app.route('/etrading',methods=["GET","POST"])
def etrading():
    return render_template('etrading.html')


@app.route('/plant_medi',methods=["GET","POST"])
def plant_medi():
    try:
        conn = sqlite3.connect(database)
        cursor = conn.cursor()
        cursor.execute("SELECT image, product_name, product_price, description FROM plant_medi")
        records = cursor.fetchall()
        conn.commit()
        conn.close()

        encoded_records= []
        for record in records:
            encoded_image= base64.b64encode(record[0]).decode('utf-8')
            encoded_records.append((encoded_image, record[1], record[2], record[3],))
        return render_template('etrading.html', records=encoded_records)
    except Exception as e:
        return f"An error occurred: {str(e)}"

@app.route('/fertilizer',methods=["GET","POST"])
def fertilizer():
    if request.method=="POST":
        product_name=request.form['product_name']
        product_price=request.form['product_price']
        stock=request.form['stock']
        brand_name=request.form['brand_name']
        category=request.form['category']
        description=request.form['description']
        f=request.files['file']

        basepath = os.path.dirname(__file__)
        file_path = os.path.join(basepath, "static/upload_img.png")
        f.save(file_path)

        with open(file_path, 'rb') as img_file:
            blobdata = img_file.read()

        
        conn=sqlite3.connect(database)
        cursor=conn.cursor()
        cursor.execute('''
                     INSERT INTO plant_medi (product_name, product_price, stock, brand_name, category, description,image)  
                     VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (product_name, product_price, stock, brand_name, category, description,blobdata))
        conn.commit()
        conn.close()
        return render_template('storage.html',message='Products Stored')

@app.route('/add_to_cart', methods=['POST'])
def add_to_cart():
    mails = mail



    product_data = request.json
    print(product_data)  # Example: print the product data to the console
##
    conn = sqlite3.connect(database)
    cursor = conn.cursor()
    

    
    cursor.execute('''
        INSERT INTO cart (mail, product_name, product_price, product_brand)
        VALUES (?, ?, ?, ?)
    ''', (mails, product_data['productName'], product_data['productPrice'], product_data['productBrand']))

    
    conn.commit()
    conn.close()

    return 'Product added to cart successfully.', 200

ADMIN_USERNAME='admin'
ADMIN_PASSWORD='admin'

@app.route('/admin',methods=["GET","POST"])
def admin():
    if request.method=='POST':
        username = request.form['username']
        password = request.form['password']

        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            return render_template('storage.html')
    return render_template('admin.html')

@app.route('/register',methods=["GET","POST"])
def register():
    if request.method=="POST":
         name=request.form['name']         
         mail=request.form['mail']         
         password=request.form['password']
         confirm_pass= request.form['confirm_pass']
         if password != confirm_pass:
            return jsonify({'error': 'Password does not match'}), 400
         con=sqlite3.connect(database)
         cur=con.cursor()
         cur.execute("SELECT mail FROM register WHERE mail=?", (mail,))
         registered = cur.fetchall()
         if registered:
             return jsonify({'error': 'Email already registered'}), 400

         else:   
             cur.execute("insert into register(name, mail, password)values(?,?,?)",(name, mail, password))
             con.commit()
             return render_template('login.html')
    return render_template('login.html')




@app.route('/login',methods = ["GET","POST"])
def login():
    global mail
    if request.method=="POST":
        mail=request.form['mail']
        password=request.form['password']
        con=sqlite3.connect(database)
        cur=con.cursor()
        cur.execute("select * from register where mail=? and password=?",(mail,password))
        data=cur.fetchone()
        if data is None:
                return "failed"        
        else:  
            con=sqlite3.connect(database)
            cur=con.cursor()
            cur.execute("select *from register where mail=?",(mail,))
            results = cur.fetchone()            
            con.commit()
            return render_template('index.html')

@app.route('/viewcart', methods=["POST","GET"])
def viewcart():
    try:
        
        conn = sqlite3.connect(database)
        cursor = conn.cursor()
        cursor.execute("SELECT product_name, product_price, product_brand FROM cart where mail = ?",(mail,))
        records = cursor.fetchall()
        print(records)
        conn.commit()
        conn.close()

        return render_template('viewcart.html', records=records)
        
    except Exception as e:
        return f"An error occurred: {str(e)}"
        
@app.route('/upload', methods=['GET', 'POST'])
def upload():
    return render_template('style-demo.html')   

@app.route('/predict', methods=['POST'])
def predict():
    data = request.files['image']
    image_path = 'static/input.jpg'  
    data.save(image_path)

    img = Image.open(image_path).convert("RGB")
    img = img.resize((224, 224))
    img_array = np.array(img) / 255.0  # Normalize
    img_array = np.expand_dims(img_array, axis=0)  # Add batch dimension

    with tf.device(device):
        predictions = model1.predict(img_array)
        predicted_class1 = np.argmax(predictions, axis=1)[0]

    plant_info = plant_data[str(predicted_class1)]  
    #name = plant_info['name']
    
    return render_template("prediction1.html", plant=plant_info)


if __name__ == '__main__':
    app.run(debug=False, port=600)
