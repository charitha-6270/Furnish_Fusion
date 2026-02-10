"""
Furnish Fusion - AWS Application
Single file Flask application using DynamoDB, SNS, IAM, and EC2
Region: us-east-1
"""

from flask import Flask, render_template, request, redirect, session, url_for, flash
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import os
import boto3
import uuid
from datetime import datetime

# ==================== AWS CONFIGURATION ====================
# MANUALLY REPLACE THE SNS_TOPIC_ARN BELOW WITH YOUR ACTUAL ARN
AWS_REGION = 'us-east-1'  # Hardcoded to us-east-1
SNS_TOPIC_ARN = 'arn:aws:sns:us-east-1:619071311787:project_topic'  # ⚠️ REPLACE THIS WITH YOUR ARN

# DynamoDB Table Names
DYNAMODB_TABLE_USERS = 'FF_Users'
DYNAMODB_TABLE_PRODUCTS = 'FF_Products'
DYNAMODB_TABLE_CART = 'FF_Cart'
DYNAMODB_TABLE_ORDERS = 'FF_Orders'
DYNAMODB_TABLE_ORDER_ITEMS = 'FF_Order_Items'

# Initialize DynamoDB clients
dynamodb = boto3.resource('dynamodb', region_name=AWS_REGION)
dynamodb_client = boto3.client('dynamodb', region_name=AWS_REGION)

# Get table references
users_table = dynamodb.Table(DYNAMODB_TABLE_USERS)
products_table = dynamodb.Table(DYNAMODB_TABLE_PRODUCTS)
cart_table = dynamodb.Table(DYNAMODB_TABLE_CART)
orders_table = dynamodb.Table(DYNAMODB_TABLE_ORDERS)
order_items_table = dynamodb.Table(DYNAMODB_TABLE_ORDER_ITEMS)

# Initialize SNS client
sns_client = boto3.client('sns', region_name=AWS_REGION)

# ==================== FLASK CONFIGURATION ====================

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'FURNISH_FUSION')
app.config['DEBUG'] = os.environ.get('DEBUG', 'False').lower() == 'true'

# ==================== DYNAMODB FUNCTIONS ====================

# Users
def create_user(name, email, password_hash, phone_no=None, address=None, role='user'):
    """Create a new user"""
    user_id = str(uuid.uuid4())
    users_table.put_item(
        Item={
            'user_id': user_id,
            'name': name,
            'email': email,
            'password_hash': password_hash,
            'role': role,
            'phone_no': phone_no or '',
            'address': address or ''
        }
    )
    return user_id

def get_user_by_email(email):
    """Get user by email"""
    response = users_table.scan(
        FilterExpression='email = :email',
        ExpressionAttributeValues={':email': email}
    )
    items = response.get('Items', [])
    return items[0] if items else None

def get_user_by_id(user_id):
    """Get user by user_id"""
    response = users_table.get_item(Key={'user_id': user_id})
    return response.get('Item')

# Products
def get_all_products():
    """Get all products"""
    response = products_table.scan()
    return response.get('Items', [])

def get_products_by_category(category):
    """Get products by category"""
    response = products_table.scan(
        FilterExpression='category = :category',
        ExpressionAttributeValues={':category': category}
    )
    return response.get('Items', [])

def get_product_by_id(product_id):
    """Get product by product_id"""
    response = products_table.get_item(Key={'product_id': product_id})
    return response.get('Item')

def add_product(name, category, price, image):
    """Add a new product"""
    product_id = str(uuid.uuid4())
    products_table.put_item(
        Item={
            'product_id': product_id,
            'name': name,
            'category': category,
            'price': int(price),
            'image': image
        }
    )
    return product_id

def update_product(product_id, name, category, price, image):
    """Update a product"""
    products_table.update_item(
        Key={'product_id': product_id},
        UpdateExpression='SET #n = :name, category = :category, price = :price, #img = :image',
        ExpressionAttributeNames={
            '#n': 'name',
            '#img': 'image'
        },
        ExpressionAttributeValues={
            ':name': name,
            ':category': category,
            ':price': int(price),
            ':image': image
        }
    )

def delete_product(product_id):
    """Delete a product"""
    products_table.delete_item(Key={'product_id': product_id})

# Cart
def get_cart_items(user_id):
    """Get all cart items for a user"""
    response = cart_table.scan(
        FilterExpression='user_id = :user_id',
        ExpressionAttributeValues={':user_id': user_id}
    )
    return response.get('Items', [])

def get_cart_item_by_user_product(user_id, product_id):
    """Get cart item by user_id and product_id"""
    response = cart_table.scan(
        FilterExpression='user_id = :user_id AND product_id = :product_id',
        ExpressionAttributeValues={
            ':user_id': user_id,
            ':product_id': product_id
        }
    )
    items = response.get('Items', [])
    return items[0] if items else None

def add_to_cart(user_id, product_id, quantity=1):
    """Add item to cart or update quantity"""
    existing_item = get_cart_item_by_user_product(user_id, product_id)
    
    if existing_item:
        new_quantity = existing_item.get('quantity', 0) + quantity
        cart_table.update_item(
            Key={'cart_id': existing_item['cart_id']},
            UpdateExpression='SET quantity = :qty',
            ExpressionAttributeValues={':qty': new_quantity}
        )
        return existing_item['cart_id']
    else:
        cart_id = str(uuid.uuid4())
        cart_table.put_item(
            Item={
                'cart_id': cart_id,
                'user_id': user_id,
                'product_id': product_id,
                'quantity': quantity
            }
        )
        return cart_id

def remove_from_cart(cart_id):
    """Remove item from cart"""
    cart_table.delete_item(Key={'cart_id': cart_id})

def clear_cart(user_id):
    """Clear all items from user's cart"""
    items = get_cart_items(user_id)
    for item in items:
        cart_table.delete_item(Key={'cart_id': item['cart_id']})

# Orders
def create_order(user_id, total_price, payment_method, payment_status='SUCCESS', status='paid'):
    """Create a new order"""
    order_id = str(uuid.uuid4())
    orders_table.put_item(
        Item={
            'order_id': order_id,
            'user_id': user_id,
            'total_price': int(total_price),
            'payment_method': payment_method,
            'payment_status': payment_status,
            'status': status,
            'created_at': datetime.utcnow().isoformat()
        }
    )
    return order_id

def get_orders_by_user(user_id):
    """Get all orders for a user"""
    response = orders_table.scan(
        FilterExpression='user_id = :user_id',
        ExpressionAttributeValues={':user_id': user_id}
    )
    items = response.get('Items', [])
    items.sort(key=lambda x: x.get('created_at', ''), reverse=True)
    return items

def get_all_orders():
    """Get all orders (for admin)"""
    response = orders_table.scan()
    items = response.get('Items', [])
    items.sort(key=lambda x: x.get('created_at', ''), reverse=True)
    return items

def get_order_by_id(order_id):
    """Get order by order_id"""
    response = orders_table.get_item(Key={'order_id': order_id})
    return response.get('Item')

def update_order_status(order_id, status):
    """Update order status"""
    orders_table.update_item(
        Key={'order_id': order_id},
        UpdateExpression='SET #status = :status',
        ExpressionAttributeNames={'#status': 'status'},
        ExpressionAttributeValues={':status': status}
    )

# Order Items
def create_order_item(order_id, product_id, quantity, price):
    """Create an order item"""
    order_item_id = str(uuid.uuid4())
    order_items_table.put_item(
        Item={
            'order_item_id': order_item_id,
            'order_id': order_id,
            'product_id': product_id,
            'quantity': quantity,
            'price': int(price)
        }
    )
    return order_item_id

def get_order_items_by_order(order_id):
    """Get all items for an order"""
    response = order_items_table.scan(
        FilterExpression='order_id = :order_id',
        ExpressionAttributeValues={':order_id': order_id}
    )
    return response.get('Items', [])

# ==================== SNS FUNCTION ====================

def send_order_notification(order_id, total_price):
    """Send order confirmation notification via AWS SNS"""
    if not SNS_TOPIC_ARN or SNS_TOPIC_ARN == 'arn:aws:sns:us-east-1:619071311787:project_topic':
        # Fallback to console output if SNS not configured
        print("================================")
        print("ORDER CONFIRMATION NOTIFICATION")
        print(f"Order ID: {order_id}")
        print(f"Total Amount: ₹{total_price}")
        print("================================")
        return
    
    try:
        message = f"""
        Order Confirmation
        
        Order ID: {order_id}
        Total Amount: ₹{total_price}
        
        Thank you for your purchase!
        """
        
        response = sns_client.publish(
            TopicArn=SNS_TOPIC_ARN,
            Message=message,
            Subject=f'Order Confirmation - Order #{order_id}'
        )
        
        print(f"SNS notification sent: {response['MessageId']}")
        return response
        
    except Exception as e:
        print(f"Error sending SNS notification: {e}")
        # Fallback to console output
        print("================================")
        print("ORDER CONFIRMATION NOTIFICATION")
        print(f"Order ID: {order_id}")
        print(f"Total Amount: ₹{total_price}")
        print("================================")

# ==================== AUTH DECORATORS ====================

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if session.get("role") != "admin":
            return redirect("/home")
        return f(*args, **kwargs)
    return wrapper

# ==================== ROUTES ====================

@app.route("/")
def landing():
    return render_template("landing.html")

@app.route("/home")
@login_required
def home():
    return render_template("home.html")

@app.route("/health")
def health():
    return {"status": "healthy"}, 200

# ==================== AUTH ROUTES ====================

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        try:
            name = request.form["name"]
            email = request.form["email"]
            password = request.form["password"]
            password_hash = generate_password_hash(password)

            phone_no = request.form.get("phone_no", "")
            address = request.form.get("address", "")

            # Check if user already exists
            existing_user = get_user_by_email(email)
            if existing_user:
                flash("Email already registered. Please login.", "error")
                return redirect(url_for("login"))

            # Create user
            user_id = create_user(name, email, password_hash, phone_no, address, role='user')

            flash("Registration successful! Please login.", "success")
            return redirect(url_for("login"))
        except Exception as e:
            flash(f"Registration failed: {str(e)}", "error")

    return render_template("auth/register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        try:
            email = request.form["email"]
            password = request.form["password"]

            user = get_user_by_email(email)

            if user and check_password_hash(user["password_hash"], password):
                # If user is an admin, redirect them to admin login page
                if user.get("role") == "admin":
                    flash("Please use Admin Login for administrator access.", "info")
                    return redirect(url_for("admin_login"))
                
                session["user_id"] = user["user_id"]
                session["role"] = user.get("role", "user")

                flash("Login successful!", "success")
                return redirect("/home")

            flash("Invalid email or password", "error")
        except Exception as e:
            flash(f"Login error: {str(e)}", "error")

    return render_template("auth/login.html")

@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("login"))

@app.route("/admin/register", methods=["GET", "POST"])
def admin_register():
    if request.method == "POST":
        try:
            name = request.form["name"]
            email = request.form["email"]
            password = request.form["password"]
            password_hash = generate_password_hash(password)

            phone_no = request.form.get("phone_no", "")
            address = request.form.get("address", "")

            # Check if admin already exists
            existing_user = get_user_by_email(email)
            if existing_user:
                flash("Email already registered. Please login.", "error")
                return redirect(url_for("admin_login"))

            # Create admin user with role='admin'
            user_id = create_user(name, email, password_hash, phone_no, address, role='admin')

            flash("Admin registration successful! Please login.", "success")
            return redirect(url_for("admin_login"))
        except Exception as e:
            flash(f"Registration failed: {str(e)}", "error")

    return render_template("auth/admin_register.html")

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        try:
            email = request.form["email"]
            password = request.form["password"]

            user = get_user_by_email(email)

            if user and check_password_hash(user["password_hash"], password):
                # Check if user is an admin
                if user.get("role") != "admin":
                    flash("Access denied. This is for administrators only.", "error")
                    return redirect(url_for("admin_login"))
                
                session["user_id"] = user["user_id"]
                session["role"] = "admin"

                flash("Admin login successful!", "success")
                return redirect("/admin")

            flash("Invalid email or password", "error")
        except Exception as e:
            flash(f"Login error: {str(e)}", "error")

    return render_template("auth/admin_login.html")

# ==================== PRODUCT ROUTES ====================

@app.route("/sofas")
@login_required
def sofas():
    products = get_products_by_category("sofa")
    return render_template("products/sofas.html", products=products)

@app.route("/beds")
@login_required
def beds():
    products = get_products_by_category("bed")
    return render_template("products/beds.html", products=products)

@app.route("/tables")
@login_required
def tables():
    products = get_products_by_category("table")
    return render_template("products/tables.html", products=products)

@app.route("/chairs")
@login_required
def chairs():
    products = get_products_by_category("chair")
    return render_template("products/chairs.html", products=products)

# ==================== CART ROUTES ====================

@app.route("/add-to-cart/<product_id>")
@login_required
def add_to_cart_route(product_id):
    try:
        user_id = session["user_id"]
        add_to_cart(user_id, product_id, quantity=1)
        flash("Item added to cart!", "success")
    except Exception as e:
        flash(f"Error adding to cart: {str(e)}", "error")
    return redirect(url_for("view_cart"))

@app.route("/cart")
@login_required
def view_cart():
    try:
        user_id = session["user_id"]
        cart_items = get_cart_items(user_id)
        
        # Get product details for each cart item
        items_with_details = []
        total = 0
        
        for item in cart_items:
            product = get_product_by_id(item["product_id"])
            if product:
                item_detail = {
                    "cart_id": item["cart_id"],
                    "name": product["name"],
                    "price": product["price"],
                    "quantity": item["quantity"],
                    "image": product.get("image", "")
                }
                items_with_details.append(item_detail)
                total += product["price"] * item["quantity"]
        
        return render_template("cart/cart.html", items=items_with_details, total=total)
    except Exception as e:
        flash(f"Error loading cart: {str(e)}", "error")
        return redirect("/home")

@app.route("/remove-from-cart/<cart_id>")
@login_required
def remove_from_cart_route(cart_id):
    try:
        remove_from_cart(cart_id)
        flash("Item removed from cart", "success")
    except Exception as e:
        flash(f"Error removing item: {str(e)}", "error")
    return redirect(url_for("view_cart"))

# ==================== ORDER ROUTES ====================

@app.route("/place-order")
@login_required
def place_order():
    try:
        user_id = session["user_id"]
        cart_items = get_cart_items(user_id)
        
        if not cart_items:
            flash("Your cart is empty", "warning")
            return redirect("/cart")
        
        # Calculate total
        total_price = 0
        for item in cart_items:
            product = get_product_by_id(item["product_id"])
            if product:
                total_price += product["price"] * item["quantity"]
        
        return render_template("payment.html", total=total_price)
    except Exception as e:
        flash(f"Error: {str(e)}", "error")
        return redirect("/cart")

@app.route("/process-payment", methods=["POST"])
@login_required
def process_payment():
    try:
        user_id = session["user_id"]
        payment_method = request.form.get("payment_method", "cash")
        
        # Get cart items
        cart_items = get_cart_items(user_id)
        
        if not cart_items:
            flash("Your cart is empty", "warning")
            return redirect("/home")
        
        # Calculate total
        total_price = 0
        cart_with_products = []
        for item in cart_items:
            product = get_product_by_id(item["product_id"])
            if product:
                item_total = product["price"] * item["quantity"]
                total_price += item_total
                cart_with_products.append({
                    "product_id": item["product_id"],
                    "quantity": item["quantity"],
                    "price": product["price"]
                })
        
        # Create order
        order_id = create_order(
            user_id=user_id,
            total_price=total_price,
            payment_method=payment_method,
            payment_status="SUCCESS",
            status="paid"
        )
        
        # Create order items
        for item in cart_with_products:
            create_order_item(
                order_id=order_id,
                product_id=item["product_id"],
                quantity=item["quantity"],
                price=item["price"]
            )
        
        # Clear cart
        clear_cart(user_id)
        
        # Send notification
        send_order_notification(order_id, total_price)
        
        flash("Order placed successfully 🎉", "success")
        return render_template(
            "orders/confirmation.html",
            order_id=order_id,
            total_price=total_price,
            payment_method=payment_method
        )
    except Exception as e:
        flash(f"Error processing payment: {str(e)}", "error")
        return redirect("/cart")

@app.route("/my-orders")
@login_required
def my_orders():
    try:
        user_id = session["user_id"]
        orders = get_orders_by_user(user_id)
        
        # Get order items for each order
        for order in orders:
            order_items = get_order_items_by_order(order["order_id"])
            items_with_details = []
            for oi in order_items:
                product = get_product_by_id(oi["product_id"])
                if product:
                    items_with_details.append({
                        "name": product["name"],
                        "image": product.get("image", ""),
                        "quantity": oi["quantity"]
                    })
            order["items"] = items_with_details
        
        return render_template("orders/history.html", orders=orders)
    except Exception as e:
        flash(f"Error loading orders: {str(e)}", "error")
        return redirect("/home")

@app.route("/cancel-order/<order_id>")
@login_required
def cancel_order(order_id):
    try:
        user_id = session["user_id"]
        order = get_order_by_id(order_id)
        
        if order and order["user_id"] == user_id:
            if order["status"] in ["placed", "paid"]:
                update_order_status(order_id, "cancelled")
                flash("Order cancelled successfully", "info")
            else:
                flash("Cannot cancel this order", "error")
        else:
            flash("Order not found", "error")
    except Exception as e:
        flash(f"Error cancelling order: {str(e)}", "error")
    
    return redirect("/my-orders")

@app.route("/return-order/<order_id>")
@login_required
def return_order(order_id):
    try:
        user_id = session["user_id"]
        order = get_order_by_id(order_id)
        
        if order and order["user_id"] == user_id:
            if order["status"] == "delivered":
                update_order_status(order_id, "returned")
                flash("Return request submitted", "info")
            else:
                flash("Can only return delivered orders", "error")
        else:
            flash("Order not found", "error")
    except Exception as e:
        flash(f"Error submitting return: {str(e)}", "error")
    
    return redirect("/my-orders")

# ==================== ADMIN ROUTES ====================

@app.route("/admin")
@admin_required
def admin_dashboard():
    try:
        products = get_all_products()
        return render_template("admin/dashboard.html", products=products)
    except Exception as e:
        flash(f"Error loading dashboard: {str(e)}", "error")
        return redirect("/home")

@app.route("/admin/add", methods=["GET", "POST"])
@admin_required
def admin_add_product():
    if request.method == "POST":
        try:
            name = request.form["name"]
            category = request.form["category"]
            price = request.form["price"]
            image = request.form["image"]
            
            add_product(name, category, price, image)
            flash("Product added successfully", "success")
            return redirect("/admin")
        except Exception as e:
            flash(f"Error adding product: {str(e)}", "error")
    
    return render_template("admin/add_product.html")

@app.route("/admin/edit/<product_id>", methods=["GET", "POST"])
@admin_required
def admin_edit_product(product_id):
    try:
        if request.method == "POST":
            name = request.form["name"]
            category = request.form["category"]
            price = request.form["price"]
            image = request.form["image"]
            
            update_product(product_id, name, category, price, image)
            flash("Product updated successfully", "success")
            return redirect("/admin")
        
        product = get_product_by_id(product_id)
        if not product:
            flash("Product not found", "error")
            return redirect("/admin")
        
        return render_template("admin/edit_product.html", product=product)
    except Exception as e:
        flash(f"Error: {str(e)}", "error")
        return redirect("/admin")

@app.route("/admin/delete/<product_id>")
@admin_required
def admin_delete_product(product_id):
    try:
        delete_product(product_id)
        flash("Product deleted successfully", "success")
    except Exception as e:
        flash(f"Error deleting product: {str(e)}", "error")
    return redirect("/admin")

@app.route("/admin/orders")
@admin_required
def admin_orders():
    try:
        orders = get_all_orders()
        
        # Get customer names and order items
        for order in orders:
            user = get_user_by_id(order["user_id"])
            order["customer_name"] = user.get("name", "Unknown") if user else "Unknown"
            
            order_items = get_order_items_by_order(order["order_id"])
            items_with_details = []
            for oi in order_items:
                product = get_product_by_id(oi["product_id"])
                if product:
                    items_with_details.append({
                        "name": product["name"],
                        "image": product.get("image", ""),
                        "quantity": oi["quantity"]
                    })
            order["items"] = items_with_details
        
        return render_template("admin/orders.html", orders=orders)
    except Exception as e:
        flash(f"Error loading orders: {str(e)}", "error")
        return redirect("/admin")

@app.route("/admin/order-status/<order_id>/<status>")
@admin_required
def admin_update_order_status(order_id, status):
    try:
        update_order_status(order_id, status)
        flash("Order status updated", "success")
    except Exception as e:
        flash(f"Error updating order status: {str(e)}", "error")
    return redirect("/admin/orders")

# ==================== RUN APPLICATION ====================

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 8000))
    app.run(host='0.0.0.0', port=port, debug=app.config['DEBUG'])
