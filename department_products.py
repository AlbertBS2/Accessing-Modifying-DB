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

def read_department_input(department_list):
    while True:
        try:
            department = input("Enter Department: ")
            assert (department,) in department_list
            break
        except AssertionError:
            print("This department doesn't exist in our database")
    return department

def get_departments(cursor):
    query = """
            SELECT Title
            FROM departments
            WHERE Title <> 'Homepage'
            """
    cursor.execute(query)
    department = [c for c in cursor]
    return department

def get_department_children(department, cursor):
    query = f"""
            SELECT Title
            FROM departments
            WHERE Parent_Department = '{department}';
            """
    cursor.execute(query)
    children = [c for c in cursor]
    return children

def get_department_products(department, cursor):
    query = f"""
            SELECT  Title, ROUND(Price_Wo_Tax + Price_Wo_Tax * (Tax_Percent/100), 2) AS Retail_Price 
            FROM  products P  
            WHERE Department = '{department}';
            """
    cursor.execute(query)
    products = [c for c in cursor]
    return products


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
        
        department_list = get_departments(cursor)

        print("\n","List of Departments:")
        print(tabulate(department_list, headers=['Departments']))
        print('\n')

        while True:
            try:
                department = read_department_input(department_list)
                children = get_department_children(department, cursor)

                # Checks if the department entered is a parent or a child based 
                if children:
                    print('\n',tabulate(children, headers=['Sub Departments']),'\n')
                else:
                    products = get_department_products(department, cursor)
                    print('\n', tabulate(products, headers=['title', 'retail price']),'\n')
            except KeyboardInterrupt:
                break
