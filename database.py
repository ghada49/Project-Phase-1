import sqlite3

db= sqlite3.connect('Boutique.db')
db.execute("PRAGMA foreign_keys=on")

cursor = db.cursor()



cursor.execute("CREATE TABLE if not exists Users(user_id INTEGER PRIMARY KEY AUTOINCREMENT,name TEXT, username TEXT UNIQUE, email TEXT UNIQUE, password TEXT,status TEXT CHECK(status IN ('Online', 'Offline')))")



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


db.commit()


