import sqlite3

db= sqlite3.connect('Boutique.db')
db.execute("PRAGMA foreign_keys=on")

cursor = db.cursor()



cursor.execute("CREATE TABLE if not exists Users(user_id INTEGER PRIMARY KEY AUTOINCREMENT,name TEXT, username TEXT UNIQUE, email TEXT UNIQUE, password TEXT,status TEXT CHECK(status IN ('Online', 'Offline')))")

'''
1)	The Users table stores information about sellers and buyers, namely: [username, name, email, password] that are chosen by the user himself along with a [user id] assigned by the code (auto incrementing integer) and [status] which is also set by the codes. The status is online when the client logs in and offline otherwise. 
Note: the username is unique and two different users can not have the same username. If a user tries to register (sign up) with a username already taken, the program will prompt them to choose another username. Additionally, a mail can be used only once, meaning that after a user registered with a mail, this mail cannot be used again for another account.
'''

cursor.execute('''
    CREATE TABLE IF NOT EXISTS Products (
        product_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        product_name TEXT,
        description TEXT,
        price REAL,
        image BLOB,
        status TEXT CHECK(status IN ('Available', 'Sold', 'Cancelled')),
        FOREIGN KEY(user_id) REFERENCES Users(user_id) ON DELETE CASCADE
    )
    ''')
'''
2)	The Products table stores information about products added into the AUBoutique, namely: [product name, description of the product, price, image of the product] which are set by the sellers along with [product id] and [status] which are assigned by the program. 
Note: The product id is an auto incrementing integer which is unique for each product added. The unique ID prevents confusion between products with the same name and we do not need to provide too many details when buying one product. Instead, we only provide the ID of the object instead. For the status, it indicates if the object is sold or available. 
'''

cursor.execute('''
    CREATE TABLE IF NOT EXISTS Transactions (
        transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
        buyer_id INTEGER,
        product_id INTEGER,
        transaction_date TEXT,
        FOREIGN KEY(buyer_id) REFERENCES Users(user_id),
        FOREIGN KEY(product_id) REFERENCES Products(product_id)
    )
    ''')
'''
3)	The Transactions table which records all transactions between users. It includes the transaction id, buyer id (which is the user id of the buyer), product id, transaction date.
'''

cursor.execute('''
    CREATE TABLE IF NOT EXISTS Messages (
        message_id INTEGER PRIMARY KEY AUTOINCREMENT,
        sender_id INTEGER,
        receiver_id INTEGER,
        content TEXT,
        message_date TEXT,
        FOREIGN KEY(sender_id) REFERENCES Users(user_id),
        FOREIGN KEY(receiver_id) REFERENCES Users(user_id)
               )
               ''')
'''
4)	The Messages table which stores messages exchanged between users. It includes the sender id (which is the user id of the sender of a message), receiver id (similarly), the message date, the message id number (set by the code), content.

'''


db.commit()
