from email.message import EmailMessage
import json
import socket
import threading
import sqlite3
import databaseSend as db
from datetime import datetime, timedelta
import smtplib
import io

conn = sqlite3.connect('Boutique.db', check_same_thread=False)
cursor = conn.cursor()
db_lock = threading.Lock()

HOST = '127.0.0.1'
PORT = 12345
#dictionary to keep track of online users when they login and then remover from dictionary when logout
online_users = {}
#function to send email for buyer to confirm his/her purchase
def send_email(recipient, productList, pickup_info):
    smtp_server = 'smtp.gmail.com'
    smtp_port = 587
    sender_email = 'aub.boutique1@gmail.com'
    sender_password = 'ljrb uhpe zbdr rcdb'
    
    products_formatted = ""
    for i in range(len(productList)):
        products_formatted += str(i+1)+") "+productList[i] +'\n'
    subject = "Purchase Confirmation"
    body = f"""\
Dear customer,

Thank you for choosing AUBoutique! We are thrilled to confirm your recent purchase of 

{products_formatted}

Your order will be ready for pickup at the AUB Post Office on {pickup_info} between 9:00 am and 4:00 pm. If you have any questions or need assistance, feel free to reach out to us.

We look forward to serving you again in the future!

Best regards,
 
AUBoutique  

"""

    msg = EmailMessage()
    msg.set_content(body)
    msg['Subject'] = subject
    msg['From'] = sender_email
    msg['To'] = recipient

    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(msg)
        print("Email sent successfully")
    except Exception as e:
        print(f"Failed to send email: {e}")



def handle_client(client_socket, addr):
    print(f"[NEW CONNECTION] {addr} connected.")
    authenticated_user = None

    try:
        while True:
            request = client_socket.recv(1024).decode('utf-8')
            if not request:
                break

            try:
                data = json.loads(request)
            except json.JSONDecodeError:
                response = json.dumps({"error": "Invalid JSON format."})
                client_socket.send(response.encode('utf-8'))
                continue

            command = data.get("action")

            if command == "REGISTER":
                response = register_user(data.get("name"), data.get("email"), data.get("username"), data.get("password"))
                client_socket.send(json.dumps(response).encode('utf-8'))

            elif command == "LOGIN":
                response, authenticated_user = login_user(data.get("username"), data.get("password"))
                if authenticated_user:
                    online_users[authenticated_user[0]] = client_socket
                client_socket.send(json.dumps(response).encode('utf-8'))

            elif command == "VIEW_CONVERSATION" and authenticated_user:
                response = view_conversation(authenticated_user[0], data.get("other_username"))
                client_socket.send(json.dumps(response).encode('utf-8'))


            elif command == "VIEW_ALL_MESSAGES_RECEIVED" and authenticated_user:
                response = view_all_messages_received(authenticated_user[0])  
                client_socket.send(json.dumps(response).encode('utf-8'))

            elif command == "PURCHASE" and authenticated_user:
                product_id = data.get("product_id")
                response = purchase_product(authenticated_user[0], product_id)
                client_socket.send(json.dumps(response).encode('utf-8'))

            elif command == "SEND_MESSAGE" and authenticated_user:
                response = send_message(authenticated_user[0], data.get("receiver_username"), data.get("message_content"))
                client_socket.send(json.dumps(response).encode('utf-8'))
                
            elif command == "SEND_MESSAGE_ONLINE" and authenticated_user:
                response = send_message_online(authenticated_user[0], data.get("receiver_username"), data.get("message_content"))
                client_socket.send(json.dumps(response).encode('utf-8'))


            elif command == "ADD_PRODUCT" and authenticated_user:
                response = add_product(authenticated_user[0], data.get("product_name"), data.get("description"), data.get("price"), data.get("image_path"))
                client_socket.send(json.dumps(response).encode('utf-8'))

            elif command == "VIEW_ALL_PRODUCTS" and authenticated_user:
                response = view_products(authenticated_user[0])
                client_socket.send(json.dumps(response).encode('utf-8'))

            elif command == "SEARCH_PRODUCTS_BY_SELLER" and authenticated_user:
                response = search_products_by_seller(data.get("seller_username"))
                client_socket.send(json.dumps(response).encode('utf-8'))

            elif command == "VIEW_MY_LISTINGS" and authenticated_user:
                response = view_my_listings(authenticated_user[0])
                client_socket.send(json.dumps(response).encode('utf-8'))

            elif command == "VIEW_USERS" and authenticated_user:
                response = view_users()
                client_socket.send(json.dumps(response).encode('utf-8'))

            elif command == "VIEW_TRANSACTIONS" and authenticated_user:
                response = view_transactions(authenticated_user[0])
                client_socket.send(json.dumps(response).encode('utf-8'))

            elif command == "VIEW_IMAGE" and authenticated_user: 
                product_id = data.get("product_id")
                (response,image_data) = view_product_image(product_id)
                client_socket.send(json.dumps(response).encode('utf-8'))
                if "Data sent" in response["message"]:

                    client_socket.sendall(len(image_data).to_bytes(4, 'big'))
                    client_socket.sendall(image_data)

            elif command == "CANCEL_LISTING" and authenticated_user:
                product_id = data.get("product_id")
                response = cancel_listing(authenticated_user[0], product_id)
                client_socket.send(json.dumps(response).encode('utf-8'))

            elif command == "LOGOUT" and authenticated_user:
                user_id = authenticated_user[0]
                cursor.execute("UPDATE Users SET status = 'Offline' WHERE user_id = ?", (user_id,))
                conn.commit()
                online_users.pop(user_id, None)
                client_socket.send(json.dumps({"message": "You have been logged out."}).encode('utf-8'))
                break
        

    except Exception as e:
        print(f"[ERROR] {e}")

    finally:
        if authenticated_user:
            user_id = authenticated_user[0]
            cursor.execute("UPDATE Users SET status = 'Offline' WHERE user_id = ?", (user_id,))
            conn.commit()
            online_users.pop(user_id, None)
        client_socket.close()

def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen()
    print(f"[LISTENING] Server is listening on {HOST}:{PORT}")

    while True:
        client_socket, addr = server.accept()
        thread = threading.Thread(target=handle_client, args=(client_socket, addr))
        thread.start()
        print(f"[ACTIVE CONNECTIONS] {threading.active_count() - 1}")

def register_user(name, email, username, password):
    with db_lock:
        try:
            cursor.execute(
                "INSERT INTO Users (name, email, username, password, status) VALUES (?, ?, ?, ?, 'Offline')",
                (name, email, username, password)
            )
            conn.commit()
            return {"message": "Registration successful."}
        except sqlite3.IntegrityError:
            return {"message": "Username or email already exists."}

def login_user(username, password):
    cursor.execute(
        "SELECT * FROM Users WHERE username = ? AND password = ?", (username, password)
    )
    user = cursor.fetchone()
    if user:
        cursor.execute(
            "UPDATE Users SET status = 'Online' WHERE username = ?", (username,)
        )
        conn.commit()
        return {"message": "Login successful. Welcome to AUBoutique!"}, user
    return {"message": "Invalid credentials."}, None

def add_product(user_id, product_name, description, price, image_path=None):
    image_data = None

    if image_path:
        try:
            with open(image_path, 'rb') as file:
                image_data = file.read()
        except Exception as e:
            return {"message": "Image file not found."}

    cursor.execute("""
        INSERT INTO Products (user_id, product_name, description, price, status, image)
        VALUES (?, ?, ?, ?, 'Available', ?)
    """, (user_id, product_name, description, float(price), image_data))
    conn.commit()
    return {"message": "Product added successfully."}

def view_products(user_id):
    cursor.execute("""
        SELECT 
            Products.product_id,
            Products.product_name,
            Products.price,
            SUBSTR(Products.description, 1, 20) AS short_description,
            Products.status,
            CASE WHEN Products.image IS NOT NULL THEN 'Yes' ELSE 'No' END AS has_image,
            Seller.username || ' - ' || Seller.name AS seller_info
        FROM 
            Products
        JOIN 
            Users AS Seller ON Products.user_id = Seller.user_id
        WHERE 
            Products.user_id != ? 
            AND Products.status = 'Available'
    """, (user_id,))

    products = cursor.fetchall()

    if not products:
        return {"message": "No available products found."}

    results = []
    for product in products:
        results.append({
            "product_id": product[0],
            "product_name": product[1],
            "price": product[2],
            "short_description": product[3],
            "status": product[4],
            "has_image": product[5],
            "seller_info": product[6]
        })

    return {"message": "Product list below", "products": results}

def search_products_by_seller(seller_username):
    cursor.execute("""
        SELECT 
            Products.product_id,
            Products.product_name,
            Products.price,
            SUBSTR(Products.description, 1, 20) AS short_description,
            Products.status,
            CASE WHEN Products.image IS NOT NULL THEN 'Yes' ELSE 'No' END AS has_image,
            Seller.username || ' - ' || Seller.name AS seller_info
        FROM 
            Products
        JOIN 
            Users AS Seller ON Products.user_id = Seller.user_id
        WHERE 
            Seller.username = ?
    """, (seller_username,))
    
    products = cursor.fetchall()

    if not products:
        return {"message": f"No products found for seller '{seller_username}'."}

    results = []
    for product in products:
        results.append({
            "product_id": product[0],
            "product_name": product[1],
            "price": product[2],
            "short_description": product[3],
            "status": product[4],
            "has_image": product[5],
            "seller_info": product[6]
        })

    return {"message":f"Products for seller '{seller_username}'." ,"products": results}


def purchase_product(buyer_id, product_ids):
    cursor.execute("SELECT email FROM Users WHERE user_id = ?", (buyer_id,))
    email_result = cursor.fetchone()
    
    emailToSend = email_result[0]  

    productNames = []
    for product_id in product_ids:
        cursor.execute(
            "SELECT product_name, status, user_id FROM Products WHERE product_id = ?", (product_id,)
        )
        product = cursor.fetchone()

        if product:
            product_name, status, seller_id = product  
            if seller_id == buyer_id:
                return {"message": "You cannot purchase your own product."}
            elif status == "Available":
                cursor.execute(
                    "UPDATE Products SET status = 'Sold' WHERE product_id = ?", (product_id,)
                )

                transaction_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                cursor.execute(
                    "INSERT INTO Transactions (buyer_id, product_id, transaction_date) VALUES (?, ?, ?)",
                    (buyer_id, product_id, transaction_date)
                )

                conn.commit()
                productNames.append(product_name)  

        else:
            return {"message": f"Product ID {product_id} does not exist."}
    
    if productNames:
        collection_date = (datetime.now() + timedelta(days=3)).strftime('%Y-%m-%d')
        send_email(emailToSend, productNames, collection_date)
        
        return {"message": f"Purchase successful! Please collect your product(s) from the AUB post office on {collection_date} between 9:00 am and 4:00 pm."}
    else :
        return {"message": f"No products selected"}


def view_users():
    cursor.execute("""
        SELECT 
            Users.username || ' - ' || Users.name AS user_info,
            Users.status,
            COUNT(Products.product_id) AS products_added,
            SUM(CASE WHEN Products.status = 'Sold' THEN 1 ELSE 0 END) AS products_sold,
            (SELECT COUNT(*) FROM Transactions WHERE Transactions.buyer_id = Users.user_id) AS products_purchased
        FROM 
            Users
        LEFT JOIN 
            Products ON Users.user_id = Products.user_id
        GROUP BY 
            Users.user_id
    """)
    users = cursor.fetchall()

    if not users:
        return {"message": "No users found."}

    results = []
    for user in users:
        results.append({
            "user_info": user[0],
            "status": user[1],
            "products_added": user[2],
            "products_sold": user[3],
            "products_purchased": user[4]
        })

    return {"message": "Users: ","users": results}

def view_my_listings(user_id):
    cursor.execute("""
        SELECT 
            Products.product_id,
            Products.product_name,
            Products.price,
            SUBSTR(Products.description, 1, 20) AS short_description,
            Products.status,
            CASE WHEN Products.image IS NOT NULL THEN 'Yes' ELSE 'No' END AS has_image
        FROM 
            Products
        WHERE 
            Products.user_id = ?
    """, (user_id,))

    products = cursor.fetchall()

    if not products:
        return {"message": "You have no listings."}

    results = []
    for product in products:
        results.append({
            "product_id": product[0],
            "product_name": product[1],
            "price": product[2],
            "short_description": product[3],
            "status": product[4],
            "has_image": product[5]
        })

    return {"message": "These are your listing: ","products": results}

def view_transactions(user_id):
    cursor.execute("""
        SELECT 
            Products.product_name,
            Products.price,
            Transactions.transaction_date,
            Buyer.username || ' - ' || Buyer.name AS buyer_info
        FROM 
            Transactions
        JOIN 
            Products ON Transactions.product_id = Products.product_id
        JOIN 
            Users AS Buyer ON Transactions.buyer_id = Buyer.user_id
        WHERE 
            Products.user_id = ?
        ORDER BY 
            Transactions.transaction_date DESC
    """, (user_id,))
    sold_transactions = cursor.fetchall()

    if not sold_transactions:
        sold_message ="No products sold."
    else:
        sold_message = "There are products sold"

    cursor.execute("""
        SELECT 
            Products.product_name,
            Products.price,
            Transactions.transaction_date,
            Seller.username || ' - ' || Seller.name AS seller_info
        FROM 
            Transactions
        JOIN 
            Products ON Transactions.product_id = Products.product_id
        JOIN 
            Users AS Seller ON Products.user_id = Seller.user_id
        WHERE 
            Transactions.buyer_id = ?
        ORDER BY 
            Transactions.transaction_date DESC
    """, (user_id,))
    bought_transactions = cursor.fetchall()
    if not bought_transactions:
        bought_message ="No products bought."
    else:
        bought_message = "There are products bought"
     
    sold_results = []
    for trans in sold_transactions:
        sold_results.append({
            "product_name": trans[0],
            "price": trans[1],
            "transaction_date": trans[2],
            "buyer_info": trans[3]
        })

    bought_results = []
    for trans in bought_transactions:
        bought_results.append({
            "product_name": trans[0],
            "price": trans[1],
            "transaction_date": trans[2],
            "seller_info": trans[3]
        })

    return {"message":"sent", "bought_message": bought_message, "sold_message": sold_message,
        "sold_transactions": sold_results,
        "bought_transactions": bought_results
    }

def view_product_image(product_id):
    cursor.execute("SELECT image FROM Products WHERE product_id = ?", (product_id,))
    result = cursor.fetchone()

    if not result or not result[0]:
        return {"message":"No image data"}  

    image_data = result[0]
    return ({"message":"Data sent"},image_data)


def send_message(sender_id, receiver_username, content):
    message_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    cursor.execute("SELECT user_id FROM Users WHERE username = ?", (receiver_username,))
    receiver = cursor.fetchone()

    if receiver:
        receiver_id = receiver[0]
        cursor.execute(
            "INSERT INTO Messages (sender_id, receiver_id, content, message_date) VALUES (?, ?, ?, ?)",
            (sender_id, receiver_id, content, message_date)
        )
        conn.commit()
        return {"message": "Message sent."}
    return {"message": "User not found."}

def send_message_online(sender_id, receiver_username, content):
    message_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    cursor.execute("SELECT user_id FROM Users WHERE username = ? AND status=? ", (receiver_username,'Online'))
    receiver = cursor.fetchone()

    if receiver:
        receiver_id = receiver[0]
        cursor.execute(
            "INSERT INTO Messages (sender_id, receiver_id, content, message_date) VALUES (?, ?, ?, ?)",
            (sender_id, receiver_id, content, message_date)
        )
        conn.commit()
        return {"message": "Message sent."}
    return {"message": "User not found or not online."}

def view_conversation(user_id, other_username):
    cursor.execute("SELECT user_id FROM Users WHERE username = ?", (other_username,))
    other_user = cursor.fetchone()

    if not other_user:
        return {"message": "User not found."}

    other_user_id = other_user[0]
    cursor.execute("""
        SELECT 
            sender_id, 
            receiver_id, 
            content, 
            message_date 
        FROM 
            Messages 
        WHERE 
            (sender_id = ? AND receiver_id = ?) OR 
            (sender_id = ? AND receiver_id = ?)
        ORDER BY 
            message_date ASC
    """, (user_id, other_user_id, other_user_id, user_id))

    messages = cursor.fetchall()

    if not messages:
        return {"message": "No messages found."}

    results = []
    for message in messages:
        cursor.execute("SELECT username FROM Users WHERE user_id= ?", (message[0],) )
        sender_name = cursor.fetchone()
        cursor.execute("SELECT username FROM Users WHERE user_id= ?", (message[1],) )
        receiver_name = cursor.fetchone()
        results.append({
            "sender_name": sender_name[0],
            "receiver_name": receiver_name[0],
            "content": message[2],
            "message_date": message[3]
        })

    return {"message":"Messages found", "results": results}

def view_all_messages_received(user_id):
    cursor.execute("""
        SELECT 
            m.message_id, 
            sender.username AS sender_username, 
            m.content, 
            m.message_date 
        FROM 
            Messages m
        JOIN 
            Users sender ON m.sender_id = sender.user_id
        WHERE 
            m.receiver_id = ? 
        ORDER BY 
            m.message_date ASC
    """, (user_id,))  
    
    messages = cursor.fetchall()

    if not messages:
        return {"message": "No messages found."}

    results = []
    for message in messages:
        results.append({
            "sender_username": message[1],
            "content": message[2],
            "message_date": message[3]
        })

    return {"message": "Messages found", "results": results}


def cancel_listing(user_id, product_id):
    cursor.execute("SELECT user_id FROM Products WHERE product_id = ?", (product_id,))
    result = cursor.fetchone()

    if result and result[0] == user_id:
        cursor.execute("DELETE FROM Products WHERE product_id = ?", (product_id,))
        conn.commit()
        return {"message": "Product listing canceled."}
    return {"message": "You cannot cancel a listing that you do not own."}

if __name__ == "__main__":
    start_server()
