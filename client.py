import socket
import json
import io
from PIL import Image
from tabulate import tabulate

HOST = '127.0.0.1'
PORT = 12345

client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect((HOST, PORT))

authenticated = False
current_user = None


def send_request(data):
    json_data = json.dumps(data)
    client_socket.sendall(json_data.encode('utf-8'))
    response = client_socket.recv(4096).decode('utf-8')
    
    try:
        response_data = json.loads(response)
        return response_data
    except json.JSONDecodeError:
        print("Failed to decode JSON response from server.")
        return {}


def register():
    print("\n--- Registration ---")
    name = input("Enter your name: ")
    email = input("Enter your email: ")
    username = input("Enter a new username: ")
    password = input("Enter a new password: ")

    command = {
        "action": "REGISTER",
        
            "name": name,
            "email": email,
            "username": username,
            "password": password
        
    }
    
    response = send_request(command)
    if response.get("message"):
        print(response["message"])


def login():
    global authenticated, current_user
    print("\n--- Login ---")
    username = input("Enter your username: ")
    password = input("Enter your password: ")

    command = {
        "action": "LOGIN",
        
            "username": username,
            "password": password
        
    }

    response = send_request(command)

    if "Login successful" in response.get("message"):
        authenticated = True
        current_user = username
        print(response.get("message"))
        print("Welcome back!\nList of available prodcuts below: \n")
        command2 = {"action": "VIEW_ALL_PRODUCTS"}
        response2 =send_request(command2)
        if "No available products" in response2.get("message"):
            print(response2.get("message"))
        else:
            products= response2.get("products")
            headers = products[0].keys()
            print(tabulate(products, headers="keys", tablefmt="grid"))
    else:
        print("\nLogin failed. Please try again.\n")


def add_product():
    print("\n--- Add Product ---")
    product_name = input("Enter product name: ")
    while True:
        description = input("Enter product description (max 20 characters): ")
        if len(description) > 20:
            print("You exceeded the description character limit (20)")
        else:
            break
    price = input("Enter product price: ")
    image_path = input("Enter image file path (leave blank if none): ").strip()

    command = {
        "action": "ADD_PRODUCT",
            "product_name": product_name,
            "description": description,
            "price": price,
            "image_path": image_path if image_path else None
        
    }
    
    response = send_request(command)
    print(response.get("message"))


def view_products():
    print("\n--- View Products ---")
    print("1. View Available Products")
    print("2. Search Products by Seller (username)")

    choice = input("Enter your choice (1 or 2): ")

    if choice == "1":
        command = {"action": "VIEW_ALL_PRODUCTS"}
        response =send_request(command)
        if "No available products" in response.get("message"):
            print(response.get("message"))
        else:
            products= response.get("products")
            headers = products[0].keys()
            print(tabulate(products, headers="keys", tablefmt="grid"))

    elif choice == "2":
        seller_username = input("Enter the seller's username: ")
        command = {
            "action": "SEARCH_PRODUCTS_BY_SELLER",
            "seller_username": seller_username
        }
        response = send_request(command)
        if "No products" in response.get("message"):
            print(response.get("message"))
        else:
            products= response.get("products")
            headers = products[0].keys()
            print(tabulate(products, headers="keys", tablefmt="grid"))

    else:
        print("Invalid choice. Returning to main menu.")


def purchase_product():
    print("\n--- Purchase Product ---")
    product_ids = []
    
    while True:
        product_id = input("Enter product ID to purchase (or type 'done' when finished): ")
        if product_id.lower() == 'done':
            break
        product_ids.append(product_id)
    
    command = {
        "action": "PURCHASE",
        "product_id": product_ids
    }
    response = send_request(command)
    print(response.get("message"))



def send_message():
    print("\n--- Send Message ---")
    print("1. Only if receiver is online")
    print("2. Regardless if online or offline")

    choice = input("Enter your choice (1 or 2): ")
    receiver_username = input("Enter the username of the receiver: ")    
    message_content = input("Enter your message: ")
    if choice == "2":
        command = {
            "action": "SEND_MESSAGE",
            
                "receiver_username": receiver_username,
                "message_content": message_content
            
        }
    else:
        command = {
            "action": "SEND_MESSAGE_ONLINE",
            
                "receiver_username": receiver_username,
                "message_content": message_content
            
        }
    

    print(send_request(command).get("message"))



def view_conversations():
    print("\n--- View Conversations ---")
    other_username = input("Enter the username of the person to view conversations: ")

    command = {
        "action": "VIEW_CONVERSATION",
        "other_username": other_username
    }

    response = send_request(command)
    if "No messages found." in response.get("message"):
        print(response.get("message")) 
    else:
        msg= response.get("results")
        headers = msg[0].keys()
        print(tabulate(msg, headers="keys", tablefmt="grid"))



def view_all_messages_received():
    print("\n--- View All Messages Received ---")
    
    user_id = current_user

    command = {
        "action": "VIEW_ALL_MESSAGES_RECEIVED",
        "user_id": user_id
    }

    response = send_request(command)
    if "No messages found." in response.get("message"):
        print(response.get("message"))
    else:
        msg = response.get("results")
        headers = msg[0].keys()
        print(tabulate(msg, headers="keys", tablefmt="grid"))



def view_users():
    print("\n--- Users List ---")
    command = {"action": "VIEW_USERS"}
    response= send_request(command)
    if "No users found." in response.get("message"):
        print(response.get("message"))
    else:
        users= response.get("users")
        headers = users[0].keys()
        print(tabulate(users, headers="keys", tablefmt="grid"))
        


def view_transactions():
    print("\n--- View Transactions ---")
    command = {"action": "VIEW_TRANSACTIONS"}
    response = send_request(command)
    if "No products sold." in response.get("sold_message"):
        print("No products sold yet.")
    else:
        print("Products sold\n")
        sold_transactions = response.get("sold_transactions")
        headers = sold_transactions[0].keys()
        print(tabulate(sold_transactions, headers="keys", tablefmt="grid"))
    if "No products bought" in response.get("bought_message"):
        print("No products bought yet.")
    else:
        print("Products bought\n")
        bought_transactions = response.get("bought_transactions")
        headers = bought_transactions[0].keys()
        print(tabulate(bought_transactions, headers="keys", tablefmt="grid"))    


def view_my_listings():
    print("\n--- My Listings ---")
    command = {"action": "VIEW_MY_LISTINGS"}
    response = send_request(command)
    if "You have no listings" in response.get("message"):
        print(response.get("message"))
    else:
        products= response.get("products")
        headers = products[0].keys()
        print(tabulate(products, headers="keys", tablefmt="grid"))


def view_product_image():
    print("\n--- View Product Image ---")
    product_id = input("Enter the product ID to view its image: ")
    command = {"action": "VIEW_IMAGE", "product_id": product_id}
    response = send_request(command)
    if "Data sent" in response.get("message"):
        image_size_data = client_socket.recv(4)
        image_size = int.from_bytes(image_size_data, 'big')

        image_data = b""
        while len(image_data) < image_size:
            chunk = client_socket.recv(4096)
            if not chunk:
                break
            image_data += chunk

        image = Image.open(io.BytesIO(image_data))
        image.show()
        print("Image for product ", product_id)
    else:
        print("No image found for this product.")
    

def cancel_listing():
    print("\n--- Cancel a Listing ---")
    product_id = input("Enter the product ID you want to cancel: ")

    command = {
        "action": "CANCEL_LISTING",
        "product_id": product_id
    }

    print(send_request(command).get("message"))


print("\nWelcome to AUBoutique Platform!\n")
authenticated = False

while True:
    if not authenticated:
        print("\nOptions:")
        print("1. Register")
        print("2. Login")
        print("3. Exit")

        choice = input("Enter your choice (Pick a number 1-3): ")

        if choice == "1":
            register()
        elif choice == "2":
            login()
        elif choice == "3":
            print("Exiting...")
            break
        else:
            print("Invalid choice. Please try again.")
    if authenticated:
        print(f"\n{current_user} - Options (Pick a number 1-12):")
        print("1. Add Product")
        print("2. View Products")
        print("3. Purchase Product")
        print("4. Send a Message")
        print("5. Conversation History")
        print("6. View all messages received")
        print("7. View Users List")
        print("8. View Transactions")
        print("9. View Product Image")
        print("10. View My Listings")
        print("11. Cancel a Listing")
        print("12. Logout")

        choice = input("Enter your choice: ")

        if choice == "1":
            add_product()
        elif choice == "2":
            view_products()
        elif choice == "3":
            purchase_product()
        elif choice == "4":
            send_message()
        elif choice == "5":
            view_conversations()
        elif choice =="6":
            view_all_messages_received()
        elif choice == "7":
            view_users()
        elif choice == "8":
            view_transactions()
        elif choice == "9":
            view_product_image()
        elif choice == "10":
            view_my_listings()
        elif choice == "11":
            cancel_listing()
        elif choice == "12":
            print("Logging out...")
            authenticated = False
            current_user = None
        else:
            print("Invalid choice. Please try again.")

client_socket.close()
