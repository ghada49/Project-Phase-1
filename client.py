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

#send_request take the data and transform it into json data. Then we receive a response from the server and transform it again
def send_request(data):
    json_data = json.dumps(data) # convert our data to json
    client_socket.sendall(json_data.encode('utf-8')) # we send the data to the client
    response = client_socket.recv(4096).decode('utf-8') # we receive our response from the server 
    
    try:
        response_data = json.loads(response) # we transform it again to return the data in our program
        return response_data
    except json.JSONDecodeError:
        print("Failed to decode JSON response from server.")
        return {}

# the user inputs name, email, username, password and we store it in a dictionary with the action (which is register) and the fields
# note the "action" field is important here, when we are sending our request to our server, the server will first check what "action" we are doing
def register():
    print("\n--- Registration ---")
    name = input("Enter your name: ") # input the fields required
    email = input("Enter your email: ")
    username = input("Enter a new username: ")
    password = input("Enter a new password: ")

    command = {
        "action": "REGISTER",
        
            "name": name,
            "email": email,
            "username": username,
            "password": password
        
    } # we store the data
    
    response = send_request(command) # we send the request using json using the fuction send_request
    if response.get("message"): # we receive the message 
        print(response["message"])

#login takes as inputs the username and password and send the data to the server which will check if these credentials are in the database and if it is correct
def login():
    global authenticated, current_user
    print("\n--- Login ---")
    username = input("Enter your username: ") # user input
    password = input("Enter your password: ")

    command = {
        "action": "LOGIN",
        
            "username": username,
            "password": password
        
    }  
    # we store the data

    response = send_request(command) # we send the request, here the server will see that the action is "login"

    if "Login successful" in response.get("message"): # remember that in the server code, we send responses in this format: return {message : something} 
        #(e.g it could be {"messages": "request completed"} or "not completed" so we check what message we received and according to that the client will tell the user if his request was completed or not and so on so forth
        authenticated = True # we keep track of it for later use (in the while loop which shows the different option) --> the user can view products, add products and all these action only if he is logged in so that's why we keep track of it
        current_user = username  # we store the username here for later use 
        print(response.get("message"))
        print("Welcome back!\nList of available prodcuts below: \n")
        command2 = {"action": "VIEW_ALL_PRODUCTS"} 
        # we want to show the products after login 
        response2 =send_request(command2) 
        # we send the request
        if "No available products" in response2.get("message"):
            print(response2.get("message"))
        else:
            products= response2.get("products")
            headers = products[0].keys()
            print(tabulate(products, headers="keys", tablefmt="grid")) # remember that we stored our information in results matrix and now we it will be represented in tabular form to the user
    else:
        print("\nLogin failed. Please try again.\n")

# adding products takes from the user input : the name, description, image path and the data is sent to the server who will add all of this information into the products database
def add_product():
    print("\n--- Add Product ---")
    product_name = input("Enter product name: ")
    while True:
        description = input("Enter product description (max 20 characters): ")
        if len(description) > 20: # we decided to make the description short but it could be adjusted 
            print("You exceeded the description character limit (20)")
        else:
            break
    price = input("Enter product price: ")
    image_path = input("Enter image file path (leave blank if none): ").strip() #the seller has the option to add an image or not

    command = { 
        "action": "ADD_PRODUCT",
            "product_name": product_name,
            "description": description,
            "price": price,
            "image_path": image_path if image_path else None # image path is set to None if the user has not entered anything
        
    } # we store the data in command
    
    response = send_request(command) #we send the request and get the response back from the server
    print(response.get("message")) 

# for view products, we have two choice, either to see all products from all sellers OR to see products from specific seller 
def view_products():
    print("\n--- View Products ---")
    print("1. View Available Products")
    print("2. Search Products by Seller (username)")

    choice = input("Enter your choice (1 or 2): ")

    if choice == "1":
        command = {"action": "VIEW_ALL_PRODUCTS"} # so here we make the request and the server will fetch all the products
        response =send_request(command)
        if "No available products" in response.get("message"):
            print(response.get("message"))
        else:
            products= response.get("products")
            headers = products[0].keys()
            print(tabulate(products, headers="keys", tablefmt="grid"))

    elif choice == "2":
        seller_username = input("Enter the seller's username: ") # if he wants to see from a specific seller, he should enter the username and the server will fetch the infos accordingly
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

# purchase product runs with a while loop that will prompt at each time the user to enter the product ID to purchase and it will stop when the user writes "done"
def purchase_product():
    print("\n--- Purchase Product ---")
    product_ids = [] # we will put here the ID's of the products to buy
    
    while True: # so we select all the products in one pass
        product_id = input("Enter product ID to purchase (or type 'done' when finished): ") # continuisly we add the product ID
        if product_id.lower() == 'done':
            break
        product_ids.append(product_id) # here we append to a list all the products ID 
    
    command = {
        "action": "PURCHASE",
        "product_id": product_ids
    }  # we send the list with the product IDS and the server from his side will loop over each product ID and do the necessary changes in the databases
    response = send_request(command)
    print(response.get("message"))


# to send a message to another user, the user will have to enter username of this other user and the content
# the user can choose to send the message only if the user is online or to send the message regardless if his online or not
# note this a preference of the user (this could be simulated to a situation where the customer wants a direct answer (so he wants to user to be online) or don't mind to have an answer later on
def send_message():
    print("\n--- Send Message ---")
    print("1. Only if receiver is online") 
    print("2. Regardless if online or offline")

    choice = input("Enter your choice (1 or 2): ")
    receiver_username = input("Enter the username of the receiver: ")    
    message_content = input("Enter your message: ")
    if choice == "2": # two different requests
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


# to view the conversations with another user, the user have to give as input the username of this other person
def view_conversations():
    print("\n--- View Conversations ---")
    other_username = input("Enter the username of the person to view conversations: ") # so here is the input which has the username of the other person

    command = {
        "action": "VIEW_CONVERSATION",
        "other_username": other_username
    } 

    response = send_request(command) #send request to server who will fetch the infos in the database in the Messages table
    if "No messages found." in response.get("message"):
        print(response.get("message")) 
    else:
        msg= response.get("results")
        headers = msg[0].keys()
        print(tabulate(msg, headers="keys", tablefmt="grid")) #tabulate form representation


#view all messages received : note here, we do not take any input. We have the username of the current user and we send it to the server and the server will fetch in the database and will check messages send to the suer (who is the receiver)
#this function lets the user check if he has recieved any messages (like if he has new notifications in order to reply to them accordingly)
def view_all_messages_received():
    print("\n--- View All Messages Received ---")
    
    user_id = current_user

    command = {
        "action": "VIEW_ALL_MESSAGES_RECEIVED",
        "user_id": user_id
    } #send request

    response = send_request(command)
    if "No messages found." in response.get("message"):
        print(response.get("message"))
    else:
        msg = response.get("results")
        headers = msg[0].keys()
        print(tabulate(msg, headers="keys", tablefmt="grid"))


# view users will show all the users of AUBoutique
# It's purpose is to allow the users to check the online/offline status of other users (if they want to send a message for example)
def view_users():
    print("\n--- Users List ---")
    command = {"action": "VIEW_USERS"} # request to view users
    response= send_request(command)
    if "No users found." in response.get("message"):
        print(response.get("message"))
    else:
        users= response.get("users")
        headers = users[0].keys()
        print(tabulate(users, headers="keys", tablefmt="grid"))
        

#transactions show all products bought or sold by the user
def view_transactions():
    print("\n--- View Transactions ---")
    command = {"action": "VIEW_TRANSACTIONS"}
    response = send_request(command)
    if "No products sold." in response.get("sold_message"): # we check if there are products sold or not 
        print("No products sold yet.") 
    else:
        print("Products sold\n")
        sold_transactions = response.get("sold_transactions")
        headers = sold_transactions[0].keys()
        print(tabulate(sold_transactions, headers="keys", tablefmt="grid")) # print table if there is
    if "No products bought" in response.get("bought_message"): # same here but for products bought
        print("No products bought yet.")
    else:
        print("Products bought\n")
        bought_transactions = response.get("bought_transactions")
        headers = bought_transactions[0].keys()
        print(tabulate(bought_transactions, headers="keys", tablefmt="grid"))  # print table if there is  

# view listings helps to see the status of products added by the user
def view_my_listings():
    print("\n--- My Listings ---")
    command = {"action": "VIEW_MY_LISTINGS"}
    response = send_request(command) # send request
    if "You have no listings" in response.get("message"):
        print(response.get("message"))
    else:
        products= response.get("products")
        headers = products[0].keys()
        print(tabulate(products, headers="keys", tablefmt="grid"))

#view image : the user write the ID of the products he want to see and the client will act according to the response of the server
def view_product_image():
    print("\n--- View Product Image ---")
    product_id = input("Enter the product ID to view its image: ") # so the user gives the product id 
    command = {"action": "VIEW_IMAGE", "product_id": product_id} # here, when the server receives, it fetch in the products table and if it finds the image path, it will send data to the client and the client will be able to open the photo
    response = send_request(command)
    if "Data sent" in response.get("message"): # so we check if the message tells us that the data is sent
        image_size_data = client_socket.recv(4) # we receive the zise of image
        image_size = int.from_bytes(image_size_data, 'big')

        image_data = b""
        while len(image_data) < image_size: # we receive the data in chuncks as the size of image is usually large
            chunk = client_socket.recv(4096)
            if not chunk:
                break
            image_data += chunk

        image = Image.open(io.BytesIO(image_data)) 
        image.show()
        print("Image for product ", product_id)
    else:
        print("No image found for this product.")
    
# to cancel a listing, the user provides the ID of the product and the server will fetch in the product table and will remove it
def cancel_listing():
    print("\n--- Cancel a Listing ---")
    product_id = input("Enter the product ID you want to cancel: ") # id input 

    command = {
        "action": "CANCEL_LISTING",
        "product_id": product_id
    }

    print(send_request(command).get("message")) # send request

''' 
def logout():
    print("Logging out...")
    command = {
        "action": "LOGOUT",
    }

    print(send_request(command).get("message"))


print("\nWelcome to AUBoutique Platform!\n")
authenticated = False
'''

# so here we give the users the option to first register, login, exit. Then when they login, we give them the other options.
while True:
    if not authenticated:
        print("\nOptions:")
        print("1. Register")
        print("2. Login")
        print("3. Exit")

        choice = input("Enter your choice (Pick a number 1-3): ")

        if choice == "1": # it calls the function above 
            register() 
        elif choice == "2":
            login()
        elif choice == "3":
            print("Exiting...")
            break
        else:
            print("Invalid choice. Please try again.")
    if authenticated: # if he has logged in, we give the other options (meaning that he is authenticated now)
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
        # for each choice, we call the function of the client side and then the user will be prompted to give inputs and so on so forth (more detailed above)
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
            authenticated = False
            current_user = None
            print("bye")
        else:
            print("Invalid choice. Please try again.")

client_socket.close() # we close the client socket at the end
