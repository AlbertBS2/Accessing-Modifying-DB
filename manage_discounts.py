from time import sleep
import pymysql
from sshtunnel import SSHTunnelForwarder
from tabulate import tabulate 
from dotenv import dotenv_values
credentials = dotenv_values()

ssh_host = credentials['SSH_ADDRESS']
ssh_user = credentials['SSH_USER']
ssh_pass = credentials['SSH_PASS']

db_address = credentials['DB_ADDRESS']
db_user = credentials['DB_USER']
db_pass = credentials['DB_PASS']
db_name = credentials['DB_NAME']

def get_products(cursor):
    query = """
            SELECT Title
            FROM products
            """
    cursor.execute(query)
    products = [c for c in cursor]
    return products

def read_product_input(product_list):
    while True:
        try:
            product = input("Enter Product Title: ")
            assert (product,) in product_list
            break
        except AssertionError:
            print("This product doesn't exist in our database")
    return product

def get_product_by_title(title, cursor):
    query = """
            SELECT Title, Discount_Percent
            FROM products
            WHERE Title = %s
            """
    cursor.execute(query, (title,))
    product = cursor.fetchone()
    return product

def update_product_discount(title, discount, cursor):
    query = """
            UPDATE products
            SET Discount_Percent = %s
            WHERE Title = %s
            """
    cursor.execute(query, (discount, title))

def read_discount_input():
    discount = None
    while discount is None:
        try:
            discount = float(input("Enter Discount Percentage: "))
            assert 0 <= discount <= 100
        except ValueError:
            print("Please enter a valid number")
        except AssertionError:
            print("Discount percentage must be between 0 and 100")
    return discount

with SSHTunnelForwarder(
ssh_address_or_host=ssh_host,
    ssh_username = ssh_user, 
    ssh_password = ssh_pass,
    remote_bind_address=(db_address, 3306)
    ) as tunnel: 

    sleep(1)
    with pymysql.connect(
        host=db_address,
        user=db_user,
        password=db_pass,
        port=tunnel.local_bind_port,
        db = db_name
    ) as mydb:
        
        cursor = mydb.cursor ()

        product_list = get_products(cursor)
        print(product_list)
        print("\n", tabulate(product_list, headers=["Products"]), "\n")
        
        while True:
            try:

                product_title = read_product_input(product_list)
                product_details = get_product_by_title(product_title, cursor)
                print("\nProduct Details:")
                print(tabulate([product_details], headers=["Title", "Discount_Percent"]), "\n")

                update_discount = input("Do you want to update the discount for this product? (y/n): ")
                if update_discount.lower() == "y":
                    discount = read_discount_input()
                    update_product_discount(product_title, discount, cursor)
                    mydb.commit()
                    print("Discount updated successfully!")
                else:
                    print("No changes made to the discount.")
            except KeyboardInterrupt:
                break

