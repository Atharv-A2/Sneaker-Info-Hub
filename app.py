from flask import Flask,flash, render_template, request, redirect, session, make_response, url_for
from reportlab.lib.pagesizes import A4
from reportlab.platypus import Table, TableStyle, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph
from flask_mysqldb import MySQL
import yaml, datetime, re
import io
import mysql.connector
app = Flask(__name__)
app.secret_key = 'your secret key'

db= yaml.safe_load(open('db.yaml'))
app.config['MYSQL_HOST']=db['mysql_host']
app.config['MYSQL_USER']=db['mysql_user']
app.config['MYSQL_PASSWORD']=db['mysql_password']
app.config['MYSQL_DB']=db['mysql_db']
user_table_name= db['user_table_name']
sneaker_model= db['sneaker_model']
customer= db['customer']
store_information= db['store_information']
cart= db['cart']
accounts=db['accounts']

myseql= MySQL(app)


# Test About us
@app.route('/test_aboutus',methods=['GET','POST'])
def testabout():
    return render_template('test_aboutus.html')

#Start-Up Page
@app.route('/', methods=['GET','POST'])
def start_page():
    return render_template('test_home.html')

#cart
@app.route('/shopping_cart', methods=['GET','POST'])
def shopping_cart():
    cur1 = myseql.connection.cursor()
    cur2 = myseql.connection.cursor()
    result1 = cur1.execute("SELECT * FROM "+cart)
    total_sum = cur2.execute("SELECT SUM(Price) FROM "+cart)
    if result1>0:
        sneaker_detail=cur1.fetchall()
        sum_details = cur2.fetchall()
        return render_template('cart.html',sneaker_details=(sneaker_detail,sum_details))
    return ("Cart is Empty, Add Products to Buy!")

# Homepage
@app.route('/home',methods=['GET','POST'])
def render_home():
    return render_template('test_home.html')

@app.route('/test_home',methods=['GET','POST'])
def testhome():
    return render_template('test_home.html')


#Add Sneaker
@app.route('/add_sneak',methods=['GET','POST'])
def add_sneaker():
    if request.method=='POST':
        # Fetch Form Data
        sneaker_= request.form
        brand = sneaker_["brand"]
        modelid = int(sneaker_["modelid"])
        style = sneaker_['style']
        color = sneaker_['color']
        size = int(sneaker_['size'])
        price = int(sneaker_['price'])
        release_date = datetime.datetime.strptime(sneaker_['releasedate'], "%d/%m/%Y")
        current_date = datetime.datetime.now()

        if release_date < current_date:
            # Create cursor object to execute commands on MYSQL Server
            cur = myseql.connection.cursor()
            try:
                cur.execute("INSERT INTO "+sneaker_model+" values(%s,%s,%s,%s,%s,%s,%s)",(modelid,brand,style,color,size,release_date,price))
                myseql.connection.commit()
                cur.close()
                return redirect('/all_packages')
            except:
                return ("Sneaker ID already Exists")
        else: 
            return ("Date is Invalid")
    return render_template('add_sneaker.html')

#Adding new Customer
@app.route('/add_customer', methods=['POST'])
def add_cust():
    if request.method=='POST':
        customer_ = request.form
        # cust_id = int(customer_['cust_id'])
        cust_name = customer_['cust_name']
        cust_phone = customer_['cust_phone']

        #Create Cursor object to execute commands on MYSQL Server
        cur = myseql.connection.cursor()
        try:
            cur.execute("INSERT INTO "+customer+"(cust_name,cust_phone) VALUES (%s,%s)", (cust_name,cust_phone))
        except:
            return "Customer ID Already Exists"
        myseql.connection.commit()
        cur.close()
        return redirect('/place_order')
    return render_template('cart.html')

# Remove package
@app.route('/rem_pack',methods=['POST'])
def remove_package():
    if request.method=='POST':
        # Fetch Form Data
        sneaker_= request.form
        modelid_=sneaker_["modelid"]

        # Create cursor object to execute commands on MYSQL Server
        cur = myseql.connection.cursor()
        cur.execute("Delete from "+sneaker_model+" where modelid=(%s)",[modelid_])
        myseql.connection.commit()
        cur.close()
        return redirect('/all_packages')
    

@app.route('/del_cart',methods=['GET','POST'])
def delete_cart():
    if request.method=='POST':
        # Fetch Form Data
        sneaker_= request.form
        cartid = sneaker_["cartid"]

        # Create cursor object to execute commands on MYSQL Server
        cur = myseql.connection.cursor()
        cur.execute("Delete from "+cart+" where CartID=(%s)",[cartid])
        myseql.connection.commit()
        cur.close()
        return redirect('/shopping_cart')


# Update Sneaker cost
@app.route('/update_sneaker',methods=['GET','POST'])
def update_pack():
    if request.method=='POST':
        # Fetch Form Data
        sneaker_= request.form
        modelid=int(sneaker_["modelid"])
        price= float(sneaker_["price"])

        # Create cursor object to execute commands on MYSQL Server
        cur = myseql.connection.cursor()

        cur.execute("Update "+sneaker_model+"\nset price={0}\nwhere modelid={1}".format(price,modelid))
        myseql.connection.commit()
        cur.close()
        return redirect('/all_packages')
    return render_template('Update_sneaker.html')


# View all packages
@app.route('/all_packages')
def packages():
    cur = myseql.connection.cursor()
    result=cur.execute("SELECT * FROM "+sneaker_model)
    if result>0:
        sneaker_details=cur.fetchall()
        return render_template('packages.html',sneaker_details=sneaker_details)
    

# Add to Cart
@app.route('/add_to_cart', methods=['POST'])
def add_to_cart():
    if request.method == 'POST':
        sneaker_id = request.form['sneaker_id']
        # Fetch sneaker details from the database
        cur = myseql.connection.cursor()
        cur.execute("SELECT * FROM "+sneaker_model+" WHERE modelid = %s", (sneaker_id,))
        sneaker = cur.fetchone()
        cur.close()
        # Insert sneaker details into the cart table
        cur = myseql.connection.cursor()
        cur.execute("INSERT INTO Cart (Brand, Style, Color, Size, Price) VALUES (%s, %s, %s, %s, %s)",
                    (sneaker[1], sneaker[2], sneaker[3], sneaker[4], sneaker[6]))
        myseql.connection.commit()
        cur.close()
        return redirect('/test_home#Products')  # Redirect back to all_packages route


db1 = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",
    database="sneaker_db",
    port='3306'
)

cursor1 = db1.cursor()


#Login Functionality
@app.route('/login', methods =['GET', 'POST'])
def login():
    msg = ''
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        username = request.form['username']
        password = request.form['password']
        cursor1.execute("SELECT * FROM account WHERE username = %s", (username,))
        account = cursor1.fetchone()
        if account and account[2] == password:
            session['loggedin'] = True
            session['id'] = account[0]
            session['username'] = account[1]
            session['email'] = account[3]
            msg = 'Logged in successfully !'
            cur = myseql.connection.cursor()
            result=cur.execute("SELECT * FROM "+sneaker_model)
            if result>0:
                sneaker_details=cur.fetchall()
                return render_template('packages.html', msg = msg, sneaker_details=sneaker_details)
        else:
            msg = 'Incorrect username / password !'
    return render_template('login.html', msg = msg)


#LogOut Functionality
@app.route('/logout')
def logout():
    session.pop('loggedin', None)
    session.pop('id', None)
    session.pop('username', None)
    return redirect(url_for('login'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    msg = ''
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form and 'email' in request.form:
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        cursor1.execute('SELECT * FROM account WHERE username = %s', (username,))
        existing_account = cursor1.fetchone()
        if existing_account:
            msg = 'Account already exists!'
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            msg = 'Invalid email address!'
        elif not re.match(r'[A-Za-z0-9]+', username):
            msg = 'Username must contain only characters and numbers!'
        elif not username or not password or not email:
            msg = 'Please fill out the form!'
        else:
            cursor1.execute('INSERT INTO account (username, password, email) VALUES (%s, %s, %s)', (username, password, email))
            db1.commit()
            msg = 'You have successfully registered!'
    elif request.method == 'POST':
        msg = 'Please fill out the form!'
    return render_template('register.html', msg=msg)


@app.route('/place_order', methods=['GET','POST'])
def place_order():
    # Query the database to fetch order details from the 'CART' table
    order_details = fetch_order_details_from_database()
    cust_details = customer_details_from_database()

    # Generate PDF invoice
    pdf_file = generate_invoice(order_details, cust_details)

    # Send the PDF file as a response
    response = make_response(pdf_file)
    response.headers['Content-Disposition'] = 'attachment; filename=invoice.pdf'
    response.headers['Content-Type'] = 'application/pdf'
    clr_cart()
    return response

def clr_cart():
    if request.method == 'GET':
        # Delete all records from the cart table
        cur = myseql.connection.cursor()
        cur.execute("DELETE FROM cart")
        cur.execute("ALTER TABLE CART AUTO_INCREMENT = 1")
        myseql.connection.commit()
        cur.close()
        return render_template('test_home.html')
    
    
def fetch_order_details_from_database():
    cursor = myseql.connection.cursor()
    cursor.execute("SELECT * FROM CART")
    order_details = []
    for row in cursor.fetchall():
        order_details.append(row)
    cursor.close()
    return order_details

def customer_details_from_database():
    cur = myseql.connection.cursor()
    cur.execute("SELECT CUST_NAME, CUST_PHONE FROM CUSTOMER")
    cust_details = []
    for x in cur.fetchall():
        cust_details.append(x)
    cur.close()
    return cust_details

def generate_invoice(order_details, cust_details):
    # Create a PDF file
    buffer = io.BytesIO()
    pdf = SimpleDocTemplate(buffer, pagesize=A4)

    # Define styles
    styles = getSampleStyleSheet()
    style_heading = styles['Heading1']
    style_body = ParagraphStyle(
        'body',
        fontSize=12,
        textColor=colors.black,
        leading=12,
        alignment=0
    )
    style_invoice = ParagraphStyle(
        'invoice',
        parent=style_body,
        textColor=colors.blue,
        fontSize=21,
        alignment=0,
        underline=1,
        fontName='Helvetica-Bold'
    )
    style_bold = ParagraphStyle(
        'bold',
        parent=style_body,
        fontSize=15,
        textColor=colors.black,
        alignment=0,
        fontName='Helvetica-Bold'
    )

    style_company = ParagraphStyle(
        'bold',
        parent=style_body,
        fontSize = 22,
        textColor=colors.black,
        alignment=0,
        fontName='Helvetica-Bold'
    )

    # Content
    content = []


    # Company Address
    company_name = "Sneaker Information Hub"
    company_address = "Sir MVIT, Bengaluru-562157"
    company_email = "Email: aamn@gmail.com"
    company_contact = "Contact: +91-9123456787"
    company_name_para = Paragraph(company_name, style_company)
    company_address_para = Paragraph(company_address, style_body)
    company_email_para = Paragraph(company_email, style_body)
    company_contact_para = Paragraph(company_contact, style_body)
    content.extend([company_name_para]) 
    content.append(Spacer(1, 15))
    content.extend([company_address_para, company_email_para, company_contact_para])
    content.append(Spacer(1, 18))  # Adding space

    # Title - Invoice
    title = Paragraph("Invoice", style_invoice)
    content.append(title)
    content.append(Spacer(1, 15))

    #Customer Details
    cust_details_heading = Paragraph("Customer Details", style_bold)
    content.append(cust_details_heading)
    content.append(Spacer(1,6))
    cname = ""
    cphone = 0
    for det in cust_details:
        cname = det[0]
        cphone = det[1]

    content.append(Paragraph("Name : "+cname, style_body))
    content.append(Spacer(1, 2))
    content.append(Paragraph("Phone : "+str(cphone), style_body))
    content.append(Spacer(1, 18))
    

    # Order Details Heading
    order_details_heading = Paragraph("Order Details:", style_bold)
    content.append(order_details_heading)
    content.append(Spacer(1, 12))  # Adding space

    # Order Details Table
    table_data = [['CartID', 'Brand', 'Style', 'Color', 'Size', 'Price']]
    total_amount = 0
    for row in order_details:
        table_data.append(row)
        total_amount += row[-1]  # Summing up the Price attribute
    # Adding total to the table
    total_row = ['Total Amount','','','','', total_amount]
    table_data.append(total_row)

    t = Table(table_data)
    t.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                           ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                           ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                           ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                           ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                           ('BACKGROUND', (0, 1), (-1, -2), colors.beige),
                           ('BACKGROUND', (0, -1), (-1, -1), colors.beige),
                           ('GRID', (0, 0), (-1, -1), 1, colors.black)]))
    content.append(t)
    content.append(Spacer(1, 12))  # Adding space
    
    
    # Signature
    signature_para = Paragraph("Signature: _________________________", style_bold)
    content.append(signature_para)
    content.append(Spacer(1, 36))  # Adding space

    # Date & Time of Order
    now = datetime.datetime.now()
    date_time = now.strftime("%d-%m-%Y %H:%M:%S")
    order_time = f"Date & Time of Order: {date_time}"
    order_time_para = Paragraph(order_time, style_body)
    content.append(order_time_para)
    content.append(Spacer(1, 36))  # Adding space

    # Watermark
    watermark_style = ParagraphStyle(
        'watermark',
        fontSize=15,
        textColor=colors.lightgrey,
        alignment=1
    )
    watermark_text = "Sneaker Information Hub-AAMN"
    watermark_para = Paragraph(watermark_text, watermark_style)
    content.append(Spacer(1, 72))  # Adding space above watermark
    content.append(watermark_para)

    # Build PDF
    pdf.build(content, onFirstPage=add_border)

    # Get the PDF content as bytes
    pdf_content = buffer.getvalue()
    buffer.close()

    return pdf_content

def add_border(canvas, doc):
    canvas.saveState()
    w, h = A4
    border_padding = 20
    canvas.setStrokeColorRGB(0, 0, 0)
    canvas.rect(border_padding, border_padding, w - 2 * border_padding, h - 2 * border_padding)
    canvas.restoreState()


if __name__=='__main__':
    app.run(debug=True)


