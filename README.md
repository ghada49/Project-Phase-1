LIBRARIES TO INSTALL:

To run the code make sure that you install those libraries :
- pip install pillow
- Note that the following libraries below should be built-in in your Python so by default there is NO NEED to install them, but I will mention them here again if your version of python are do not have them and if you get an error:
          pip install email  
          pip install json   
          pip install socket 
          pip install threading  
          pip install sqlite3  
          pip install datetime 
          pip install smtplib  
          pip install io
          pip install tabulate

  But again, in principle, those are built in and no need to install them. Please, first, try to run the code without them and if does not work, download the missing library.


  HOW TO RUN THE CODE:

  Use the cd command to change directories. For example, if your file is in C:\Users\YourUsername\Documents do cd C:\Users\YourUsername\Documents
  Then, run the server (python server.py)
  Then open another command and do the same with the directories. Run client.py (you can open different commands to run multiple clients)

When you first run the client code you will have 3 options :
1. Register
2. Login
3. Exit

The program will prompt you to choose and write the corresponding number of the task that you want to do (e.g. if you want to login, you enter 2 in the command line)

At the beginning you need to register and the command line will ask you to provide your name, username, email, password and you have to write them on the command, as input fields.
When you finish to register, you login. The command will prompt you to write your username and password (choosen above)
Note that one you register, you can login whenever you want no need to register again except if you want to create a new user.
The exit will just terminate the program and close the client socket. So you do it when you are done.

When you login, the products available in the market will be shown in a tabular form.
Then you will have 12 options to choose from : 
    "1. Add Product",
    "2. View Products",
    "3. Purchase Product",
    "4. Send a Message",
    "5. Conversation History",
    "6. View all messages received",
    "7. View Users List",
    "8. View Transactions",
    "9. View Product Image",
    "10. View My Listings",
    "11. Cancel a Listing",
    "12. Logout"
Again here, you have to write the number corresponding to your next. So if you want to purchase product, you write 3 on the command line where the program prompts you to do it.

ADD PRODUCT :
If you choose add product, you will be prompted to write the name of your product, a description of your product (small description no more than 20 characters), the price (don't write units next to the price, it is in dollars by default) and a path to your image of the product if you have one. Note that you should not put "" when entering the file so "C\Desktop\image.jpg" will give an error for example, you have to write it without the "".
So as I said, you just need to input those values in the command line

VIEW PRODUCT :
It will prompt you to either view all products from all seller (Option 1) or products of 1 seller (Option 2)
So here again you have to make sure to write the number of the task you want to do.
Option 1 will give you all the products of all sellers in a tabular form directly
Option 2 will prompt you to write the username of the seller to see his products.
and then it will show his product also in  a tabular form.

PURCHASE PRODUCT:
Before purchasing product, you need to view them (as mentionned above) and take their ID number from the table.
The purchase function will prompt you to write the IDs of all the product that you want meaning that you enter them 1 by 1 in a same loop. When you are done, you enter done.
Like this :
Enter the ID of the product or type 'done' when finished: 1 (you enter 1 for example)
Enter the ID of the product or type 'done' when finished: 7
Enter the ID of the product or type 'done' when finished: 10
Enter the ID of the product or type 'done' when finished: done

SO here I bought products of ID 1,7,10.
At the end you will receive a message on the cmd and also a mail to your email (so make sure you use a valid email to see it) that indicates pickup date.

SEND MESSAGE :
This will prompt to you to two options : 
either to message the user only if he is online
or to message him regardless
In both cases, the program will reprompt you to write the username of the receiver. Note you can see the usernames of the user in the "VIEW USERS" OPTION.

VIEW CONVERSATION:
So, this function will show the conversation between you and another user that you should precise. You will see all messages received and sent.
The program will prompt you to write the username of this other user and it will show you the messages exchanged in a tabular form.

VIEW ALL MESSAGES RECEIVED:
So, in contrast to view conversation, here we do not have to precise the other user. We will see all the messages that we received from all users. ONLY RECEIVED MESSAGES. It acts like an inbox.
It will also appear in a Tabular form.

VIEW USERS LIST:
As mentionned above, it will show the username and infos, of each user in AUBoutique. Also in a tabular form

VIEW TRANSACTIONS :
So, this function will show you all the products you bought or sold. For the products you bought, you have a table of these products and infos about its corresponding transactions details and for the products sold also another seperate table.

VIEW PRODUCT IMAGE:
In this function, the user is prompted to write the ID of the product to see its image (again you need to VIEW PRODUCTS to get the ID of it).
Then, it will show him the image after he enters the ID of the product.

View and Cancel listing: View listing allows the current user to check all listings (products) he has added so far to check what has been sold (or is still available). 
Cancel listing allows the client (seller) to remove a listing (product) he has already added to the marketplace (if they want to remove it) 

At the end, when you finish everything, you can logout and then exit.




  

  
          
