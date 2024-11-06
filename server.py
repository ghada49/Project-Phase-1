from email.message import EmailMessage
import json
import socket
import threading
import sqlite3
import database as db
from datetime import datetime, timedelta
import smtplib
import io

# Connect to SQLite3 database 'Boutique.db' but make sure to run the database.py file before inorder to create the database if it the first time you run
conn = sqlite3.connect('Boutique.db', check_same_thread=False)
cursor = conn.cursor()
db_lock = threading.Lock()

# server host and port to listen to incoming client connections
HOST = '127.0.0.1'
PORT = 12345
#dictionary to keep track of online users when they login and then remover from dictionary when logout
online_users = {}

#function to send email for buyer to confirm his/her purchase using smtp protocol
def send_email(recipient, productList, pickup_info):
    smtp_server = 'smtp.gmail.com'
    smtp_port = 587
    sender_email = 'aub.boutique1@gmail.com' # this is the sender mail 
    sender_password = 'ljrb uhpe zbdr rcdb'
    
    products_formatted = "" # we compute the list of product bought into a string
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
# Here we are setting : the receiver mail, the subject and the content
    msg = EmailMessage()
    msg.set_content(body)
    msg['Subject'] = subject
    msg['From'] = sender_email
    msg['To'] = recipient

    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(sender_email, sender_password) # we authenticate with out server mail 
            server.send_message(msg) # we send the message
        print("Email sent successfully")
    except Exception as e:
        print(f"Failed to send email: {e}")



def handle_client(client_socket, addr):
    print(f"[NEW CONNECTION] {addr} connected.")
    authenticated_user = None

    try:
        while True:
            request = client_socket.recv(1024).decode('utf-8') # Receive request from the client
            if not request:
                break

            try:
                data = json.loads(request) #parse JSON data from the client request
            except json.JSONDecodeError:
                response = json.dumps({"error": "Invalid JSON format."})
                client_socket.send(response.encode('utf-8'))
                continue

            command = data.get("action") # extract the action specified in the request in order to know what to proceed with
             # Command to register a new user account by getting new: name, email, username, password from the client's request
            if command == "REGISTER":
                response = register_user(data.get("name"), data.get("email"), data.get("username"), data.get("password"))
                client_socket.send(json.dumps(response).encode('utf-8'))
             # Command to log in an existing user, updating online status if successful
            elif command == "LOGIN":
                response, authenticated_user = login_user(data.get("username"), data.get("password"))
                if authenticated_user:
                    online_users[authenticated_user[0]] = client_socket
                client_socket.send(json.dumps(response).encode('utf-8'))
            # Command to view conversation history with another user
            elif command == "VIEW_CONVERSATION" and authenticated_user:
                response = view_conversation(authenticated_user[0], data.get("other_username"))
                client_socket.send(json.dumps(response).encode('utf-8'))

             # Command to view all messages received by the authenticated user from other users
            elif command == "VIEW_ALL_MESSAGES_RECEIVED" and authenticated_user:
                response = view_all_messages_received(authenticated_user[0])  
                client_socket.send(json.dumps(response).encode('utf-8'))
            # Command to purchase a product by getting the product ID inputed by the client
            elif command == "PURCHASE" and authenticated_user:
                product_id = data.get("product_id")
                response = purchase_product(authenticated_user[0], product_id)
                client_socket.send(json.dumps(response).encode('utf-8'))
            # Command to send a message to another user ( regardless if online or offline the other user is)
            elif command == "SEND_MESSAGE" and authenticated_user:
                response = send_message(authenticated_user[0], data.get("receiver_username"), data.get("message_content"))
                client_socket.send(json.dumps(response).encode('utf-8'))
            # Command to send a message to another user ( only if the other user is online) 
            elif command == "SEND_MESSAGE_ONLINE" and authenticated_user:
                response = send_message_online(authenticated_user[0], data.get("receiver_username"), data.get("message_content"))
                client_socket.send(json.dumps(response).encode('utf-8'))

            # Command to add a new product listing to the marketplace
            elif command == "ADD_PRODUCT" and authenticated_user:
                response = add_product(authenticated_user[0], data.get("product_name"), data.get("description"), data.get("price"), data.get("image_path"))
                client_socket.send(json.dumps(response).encode('utf-8'))
            # Command to view all products listed by other sellers
            elif command == "VIEW_ALL_PRODUCTS" and authenticated_user:
                response = view_products(authenticated_user[0])
                client_socket.send(json.dumps(response).encode('utf-8'))
            # Command to search for products listed by a specific seller
            elif command == "SEARCH_PRODUCTS_BY_SELLER" and authenticated_user:
                response = search_products_by_seller(data.get("seller_username"))
                client_socket.send(json.dumps(response).encode('utf-8'))
            # Command to view the listing of the seller (products that he added that were sold or not)
            elif command == "VIEW_MY_LISTINGS" and authenticated_user:
                response = view_my_listings(authenticated_user[0])
                client_socket.send(json.dumps(response).encode('utf-8'))
            # Command to view the users who registered in the AUBoutique
            elif command == "VIEW_USERS" and authenticated_user:
                response = view_users()
                client_socket.send(json.dumps(response).encode('utf-8'))
            #Command to view the transactions (what we bought or sold)
            elif command == "VIEW_TRANSACTIONS" and authenticated_user:
                response = view_transactions(authenticated_user[0])
                client_socket.send(json.dumps(response).encode('utf-8'))
            #View the image of the product the user want to see
            elif command == "VIEW_IMAGE" and authenticated_user: 
                product_id = data.get("product_id")
                (response,image_data) = view_product_image(product_id)
                client_socket.send(json.dumps(response).encode('utf-8'))
                if "Data sent" in response["message"]:

                    client_socket.sendall(len(image_data).to_bytes(4, 'big'))
                    client_socket.sendall(image_data)
            # Command to cancel a listing
            elif command == "CANCEL_LISTING" and authenticated_user:
                product_id = data.get("product_id")
                response = cancel_listing(authenticated_user[0], product_id)
                client_socket.send(json.dumps(response).encode('utf-8'))
            # Command to logout
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

# start_server() function sets up a server that listens to multiple clients at the same time

def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # first, we are creating a new socket
    server.bind((HOST, PORT)) #binding it to the host and port
    server.listen() # the server listens for new connections 
    print(f"[LISTENING] Server is listening on {HOST}:{PORT}")

    while True: # so here, we have a "while true" which allows the server to continually accept new clients
        client_socket, addr = server.accept() #accepting connections
        thread = threading.Thread(target=handle_client, args=(client_socket, addr)) # new thread for each client
        thread.start() # we start the thread
        print(f"[ACTIVE CONNECTIONS] {threading.active_count() - 1}")

# the register_user is used to create a new "account" in AUBoutique with the name, email, username, password provided from the client side
def register_user(name, email, username, password):
    with db_lock:
        try:
            cursor.execute(
                "INSERT INTO Users (name, email, username, password, status) VALUES (?, ?, ?, ?, 'Offline')",
                (name, email, username, password)
            ) # we insert the fields mentionned above into the database so we have the account created and the user can log in with no problem
            conn.commit()
            return {"message": "Registration successful."}
        except sqlite3.IntegrityError:
            return {"message": "Username or email already exists."} # if username or email is already in the database for another account an error is thrown and the user will have to register again
            
# the login_user helps to user to login. From client side, the user provides username and the password and send it to the server. When received, the server will make sure if these fields are in the database and if so, the user can login
def login_user(username, password):
    cursor.execute(
        "SELECT * FROM Users WHERE username = ? AND password = ?", (username, password)
    ) # so here we are searching for these credentials in the database to see if that account exists
    user = cursor.fetchone()
    if user: # if it does exist, then:
        cursor.execute(
            "UPDATE Users SET status = 'Online' WHERE username = ?", (username,)
        ) # we set the user status to "Online" corresponding to the username of the user. Note that this is for the messaging option (we keep track of who is online and who is not when messaging)
        conn.commit()
        return {"message": "Login successful. Welcome to AUBoutique!"}, user
    return {"message": "Invalid credentials."}, None # we print an error if the credentials are wrong


# The add_product() function takes the inputs (product name, description, price and image path) of the user from the client side and then add them into the database to create a new product. The username of the one who added the product will be added as well.
def add_product(user_id, product_name, description, price, image_path=None):
    image_data = None

    if image_path: # here we are checking if we are able to open the image and checking that the image path is valid
        try:
            with open(image_path, 'rb') as file:
                image_data = file.read()
        except Exception as e:
            return {"message": "Image file not found."}

    cursor.execute("""
        INSERT INTO Products (user_id, product_name, description, price, status, image)
        VALUES (?, ?, ?, ?, 'Available', ?)
    """, (user_id, product_name, description, float(price), image_data)) # as mentionned above, we are adding the characteristics mentioned above and we also have accounted an availibilty variable in the database to put if the product is available
    conn.commit()
    return {"message": "Product added successfully."}

# The view_products function shows all the products available 
def view_products(user_id):
    cursor.execute("""
        SELECT 
            Products.product_id, # Notice how here it is "Products.something" because we want to select all the products not only a specific one
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
            AND Products.status = 'Available' # we only select available product 
    """, (user_id,)) #  here we are selecting all the products from the database

    products = cursor.fetchall()

    if not products: # if no products
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
        }) # here we are appending all the information of products and note that it will be translated into a tabular form
    
    return {"message": "Product list below", "products": results}

#search_products_byseller has the same logic as view product except that we get from the user a specific seller (username) and view his product
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
            Seller.username = ? # note that here  we check the products of our wanted seller
    """, (seller_username,))
    
    products = cursor.fetchall()

    if not products:
        return {"message": f"No products found for seller '{seller_username}'."}

    results = []
    for product in products: #same as before
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

#The purchase function helps the user to select many products at the same time and purchase them
def purchase_product(buyer_id, product_ids):
    cursor.execute("SELECT email FROM Users WHERE user_id = ?", (buyer_id,))
    email_result = cursor.fetchone()
    
    emailToSend = email_result[0]  

    productNames = [] 
    for product_id in product_ids: # remember, product_ids is the list of ID of the products that we sent from the client side, so this list has the IDs of the products that the user wants
        cursor.execute(
            "SELECT product_name, status, user_id FROM Products WHERE product_id = ?", (product_id,)
        )
        product = cursor.fetchone() #we fetch to obtain the product

        if product: #if product is here
            product_name, status, seller_id = product  
            if seller_id == buyer_id: # a user is not allowed to buy his own product
                return {"message": "You cannot purchase your own product."}
            elif status == "Available":
                cursor.execute(
                    "UPDATE Products SET status = 'Sold' WHERE product_id = ?", (product_id,)
                ) # Here we update from available to Sold since the product is bought

                transaction_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S') # the transaction time is set at this instant
                cursor.execute(
                    "INSERT INTO Transactions (buyer_id, product_id, transaction_date) VALUES (?, ?, ?)",
                    (buyer_id, product_id, transaction_date)
                ) # we add the transaction fields (buyer_id, product_id, transaction_date) into the table

                conn.commit()
                productNames.append(product_name) # for each product we keep track of the name of the product and add it to our list which is an argument for the send email function since when sending a mail to the buyer we are also naming the products he bought  

        else:
            return {"message": f"Product ID {product_id} does not exist."} 
    
    if productNames:
        collection_date = (datetime.now() + timedelta(days=3)).strftime('%Y-%m-%d')
        send_email(emailToSend, productNames, collection_date) # here we send an email
        
        return {"message": f"Purchase successful! Please collect your product(s) from the AUB post office on {collection_date} between 9:00 am and 4:00 pm."}
    else :
        return {"message": f"No products selected"}

# The view_users functions show all the users that have an AUBoutique account
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
    users = cursor.fetchall() # here it gets all the data from the USERS database and give it to the client

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
        }) # we can see all these fields of the user

    return {"message": "Users: ","users": results}
# view listing permits the user (seller) to see what products he sold or not
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
    """, (user_id,)) # here we are selecting those products that he has added 

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
        }) # and here is the information shown to the client side to the seller

    return {"message": "These are your listing: ","products": results}

# view transactions helps the user seller or buyer to see what he bought or sold and more details on that
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
    sold_transactions = cursor.fetchall() # here we are getting all the sold products 

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
    """, (user_id,)) #Here all the bought products
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

# view product image sents the data of the photo to the client so that it can open the picture and show it to the user
def view_product_image(product_id):
    cursor.execute("SELECT image FROM Products WHERE product_id = ?", (product_id,))
    result = cursor.fetchone() # we get the data necessary to open the image

    if not result or not result[0]: # if no data
        return {"message":"No image data"}  

    image_data = result[0]
    return ({"message":"Data sent"},image_data)# we send the data 

# send message uses the receiver username enter by the user on the client side along with the content and send it to the receiver
def send_message(sender_id, receiver_username, content):
    message_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S') # we take account of the data of the sent message
    cursor.execute("SELECT user_id FROM Users WHERE username = ?", (receiver_username,)) # we select he user Id of the username (receiver)
    receiver = cursor.fetchone()

    if receiver:
        receiver_id = receiver[0]
        cursor.execute(
            "INSERT INTO Messages (sender_id, receiver_id, content, message_date) VALUES (?, ?, ?, ?)",
            (sender_id, receiver_id, content, message_date)
        ) # we insert the message and the other fields into the database and to view the message received, the receiver will user the view messages function that takes these informations from the Messages table
        conn.commit()
        return {"message": "Message sent."}
    return {"message": "User not found."}

# send_message_online is a similar function except that here we check if the user we want to talk to is online or not and then we make the decision to send messages or not
def send_message_online(sender_id, receiver_username, content):
    message_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    cursor.execute("SELECT user_id FROM Users WHERE username = ? AND status=? ", (receiver_username,'Online')) # as you can see, in the tuple, we have put "Online" to see if the user is online or not
    receiver = cursor.fetchone() # note that here we will get an answer if the username exists AND the user is online

    if receiver: # if both then no problem
        receiver_id = receiver[0]
        cursor.execute(
            "INSERT INTO Messages (sender_id, receiver_id, content, message_date) VALUES (?, ?, ?, ?)",
            (sender_id, receiver_id, content, message_date)
        )
        conn.commit()
        return {"message": "Message sent."}
    return {"message": "User not found or not online."} # else here the username does not exists or the user is not online

# viewing conversation takes the username of another user and gives all the messages that were sent between the other user and the user that is requesting this
def view_conversation(user_id, other_username):
    cursor.execute("SELECT user_id FROM Users WHERE username = ?", (other_username,)) # here we select the ID of the other user from the user table because in the Messages table it is the user ID that is used as variable
    other_user = cursor.fetchone()

    if not other_user:
        return {"message": "User not found."}

    other_user_id = other_user[0]
    cursor.execute("""
        SELECT 
            sender_id,  # as you see we are selecting these information here 
            receiver_id, 
            content, 
            message_date 
        FROM 
            Messages 
        WHERE 
            (sender_id = ? AND receiver_id = ?) OR 
            (sender_id = ? AND receiver_id = ?) # here we see both sent or received messages between the user
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
        }) # we added the information in results and it will be shown in a tabular form for the client

    return {"message":"Messages found", "results": results}

# view messages received allows the user to see who sent him any messages, so it is like inbox
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
            m.receiver_id = ? # so here the receiver is the user himself
        ORDER BY 
            m.message_date ASC
    """, (user_id,))  # so here we select all the messages received by the user 
    
    messages = cursor.fetchall()

    if not messages: # if no messages
        return {"message": "No messages found."}

    results = []
    for message in messages:
        results.append({
            "sender_username": message[1],
            "content": message[2],
            "message_date": message[3]
        }) # again as before, we store the information in results 

    return {"message": "Messages found", "results": results}

# Cancel a product listing by setting its status to 'Cancelled'
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
