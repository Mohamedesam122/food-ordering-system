import pyodbc
from decimal import Decimal
from datetime import datetime, timedelta

# --------- DATABASE CONNECTION ---------
conn = pyodbc.connect(
    r'DRIVER={ODBC Driver 17 for SQL Server};'
    r'SERVER=DESKTOP-S49VS97\SQLEXPRESS;'
    r'DATABASE=food_ordering_system;'
    r'Trusted_Connection=yes;'
)
cursor = conn.cursor()

# --------- FUNCTIONS ---------

def get_next_id(table, id_column):
    cursor.execute(f"SELECT MAX({id_column}) FROM {table}")
    result = cursor.fetchone()
    return 1 if result[0] is None else result[0] + 1

def insert_customer():
    fname = input("First Name: ")
    lname = input("Last Name: ")
    email = input("Email: ")
    password = input("Password: ")
    address = input("Address: ")
    new_id = get_next_id("CUSTOMER", "_CUSTOMERID")
    cursor.execute(
        "INSERT INTO CUSTOMER (_CUSTOMERID, FNAME, LNAME, EMAIL, PASSWORD, ADDRESS) VALUES (?, ?, ?, ?, ?, ?)",
        (new_id, fname, lname, email, password, address)
    )
    conn.commit()
    print(" Customer added successfully.")

def update_customer():
    customer_id = int(input("Customer ID to update: "))
    fname = input("New First Name: ")
    lname = input("New Last Name: ")
    email = input("New Email: ")
    address = input("New Address: ")
    cursor.execute("""
        UPDATE CUSTOMER
        SET FNAME = ?, LNAME = ?, EMAIL = ?, ADDRESS = ?
        WHERE _CUSTOMERID = ?
    """, (fname, lname, email, address, customer_id))
    conn.commit()
    print(" Customer updated successfully.")

def remove_customer():
    customer_id = int(input("Customer ID to remove: "))
    cursor.execute("DELETE FROM CUSTOMER WHERE _CUSTOMERID = ?", (customer_id,))
    conn.commit()
    print(" Customer removed.")

def insert_meal():
    name = input("Meal name: ")
    description = input("Description: ")
    price = float(input("Price: "))
    category_id = int(input("Category ID: "))
    new_id = get_next_id("MEAL", "MEALID")
    cursor.execute(
        "INSERT INTO MEAL (MEALID, CATEGORYID, NAME, DESCRIPTION, PRICE) VALUES (?, ?, ?, ?, ?)",
        (new_id, category_id, name, description, price)
    )
    conn.commit()
    print(" Meal added successfully.")

def delete_meal():
    meal_id = int(input("Meal ID to delete: "))
    cursor.execute("DELETE FROM MEAL WHERE MEALID = ?", (meal_id,))
    conn.commit()
    print(" Meal deleted.")

def update_meal():
    meal_id = int(input("Meal ID to update: "))
    name = input("New Meal Name: ")
    description = input("New Description: ")
    price = float(input("New Price: "))
    cursor.execute("""
        UPDATE MEAL
        SET NAME = ?, DESCRIPTION = ?, PRICE = ?
        WHERE MEALID = ?
    """, (name, description, price, meal_id))
    conn.commit()
    print(" Meal updated successfully.")

def show_menu_with_category():
    cursor.execute("""
        SELECT M.NAME, C.NAME
        FROM MEAL M
        JOIN CATEGORY C ON M.CATEGORYID = C.CATEGORYID
    """)
    print("\n--- Menu with Categories ---")
    for row in cursor.fetchall():
        print(f" {row[0]} - Category: {row[1]}")

def place_order():
    customer_id = int(input("Customer ID: "))
    cursor.execute("SELECT 1 FROM CUSTOMER WHERE _CUSTOMERID = ?", (customer_id,))
    if cursor.fetchone() is None:
        print(" Customer ID not found. Please add the customer first.")
        return

    vat = Decimal(input("VAT amount: "))
    payment_method = input("Payment Method: ")
    discount_code = input("Discount Code (or press Enter): ") or None
    order_id = get_next_id("[ORDER]", "ORDERID")
    order_date = input("Order date (YYYY-MM-DD): ")

    cursor.execute("""
        INSERT INTO [ORDER] 
        (ORDERID, _CUSTOMERID, TOTALPRICE, ORDERDATE, VAT, PAYMENTMETHOD, DISCOUNTCODE) 
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (order_id, customer_id, Decimal('0.0'), order_date, vat, payment_method, discount_code))

    total_price = Decimal('0.0')
    while True:
        meal_id = int(input("Meal ID: "))
        quantity = int(input("Quantity: "))
        cursor.execute("SELECT PRICE FROM MEAL WHERE MEALID = ?", (meal_id,))
        result = cursor.fetchone()
        if result:
            price_unit = Decimal(str(result[0]))
            total_price += price_unit * quantity
            cursor.execute("""
                INSERT INTO ORDERDETAILS 
                (ORDERID, MEALID, QUANTITY, PRICE_UNIT) 
                VALUES (?, ?, ?, ?)
            """, (order_id, meal_id, quantity, price_unit))
        else:
            print(" Meal ID not found.")
        more = input("Add more meals? (y/n): ").lower()
        if more != 'y':
            break

    cursor.execute("UPDATE [ORDER] SET TOTALPRICE = ? WHERE ORDERID = ?", (total_price, order_id))
    conn.commit()
    print(f" Order #{order_id} placed. Total: {total_price}")

def cancel_order():
    order_id = int(input("Order ID to cancel: "))
    cursor.execute("DELETE FROM ORDERDETAILS WHERE ORDERID = ?", (order_id,))
    cursor.execute("DELETE FROM [ORDER] WHERE ORDERID = ?", (order_id,))
    conn.commit()
    print(" Order cancelled.")

def show_all_meals():
    cursor.execute("SELECT MEALID, NAME, DESCRIPTION, PRICE FROM MEAL")
    print("\n--- Menu ---")
    for row in cursor.fetchall():
        print(f"ID: {row[0]} | {row[1]} - {row[2]} | Price: {row[3]}")

def show_customer_orders():
    customer_id = int(input("Customer ID: "))
    cursor.execute("SELECT ORDERID, ORDERDATE, TOTALPRICE FROM [ORDER] WHERE _CUSTOMERID = ?", (customer_id,))
    orders = cursor.fetchall()
    if not orders:
        print(" No orders found.")
        return
    for order in orders:
        print(f"\n Order ID: {order[0]}, Date: {order[1]}, Total: {order[2]}")
        cursor.execute("SELECT MEALID, QUANTITY, PRICE_UNIT FROM ORDERDETAILS WHERE ORDERID = ?", (order[0],))
        for item in cursor.fetchall():
            print(f"    Meal ID: {item[0]} | Qty: {item[1]} | Unit Price: {item[2]}")

def search_meal_by_name():
    name = input("Enter meal name keyword: ")
    cursor.execute("SELECT * FROM MEAL WHERE NAME LIKE ?", ('%' + name + '%',))
    for row in cursor.fetchall():
        print(row)

def search_meal_by_category():
    category = input("Enter category name: ")
    cursor.execute("""
        SELECT M.* FROM MEAL M
        JOIN CATEGORY C ON M.CATEGORYID = C.CATEGORYID
        WHERE C.NAME LIKE ?
    """, ('%' + category + '%',))
    for row in cursor.fetchall():
        print(row)

def search_meal_by_price():
    max_price = float(input("Enter maximum price: "))
    cursor.execute("SELECT * FROM MEAL WHERE PRICE <= ?", (max_price,))
    for row in cursor.fetchall():
        print(row)

def add_feedback():
    feedback_id = get_next_id("FEEDBACK", "FEEDBACKID")
    meal_id = int(input("Meal ID: "))
    customer_id = int(input("Customer ID: "))
    rating = int(input("Rating (1-5): "))
    comment = input("Comment: ")
    cursor.execute("""
        INSERT INTO FEEDBACK (FEEDBACKID, MEALID, _CUSTOMERID, RATING, COMMENT)
        VALUES (?, ?, ?, ?, ?)
    """, (feedback_id, meal_id, customer_id, rating, comment))
    conn.commit()
    print(" Feedback added.")

def modify_feedback():
    feedback_id = int(input("Feedback ID to update: "))
    rating = int(input("New Rating: "))
    comment = input("New Comment: ")
    cursor.execute("""
        UPDATE FEEDBACK
        SET RATING = ?, COMMENT = ?
        WHERE FEEDBACKID = ?
    """, (rating, comment, feedback_id))
    conn.commit()
    print(" Feedback updated.")

def delete_feedback():
    feedback_id = int(input("Feedback ID to delete: "))
    cursor.execute("DELETE FROM FEEDBACK WHERE FEEDBACKID = ?", (feedback_id,))
    conn.commit()
    print(" Feedback deleted.")

def show_all_feedback():
    cursor.execute("SELECT * FROM FEEDBACK")
    rows = cursor.fetchall()
    if not rows:
        print(" No feedback available.")
        return
    print("\n--- All Feedback ---")
    for row in rows:
        print(f"ID: {row[0]} | Meal ID: {row[1]} | Customer ID: {row[2]} | Rating: {row[3]} | Comment: {row[4]}")

def most_ordered_meal():
    cursor.execute("""
        SELECT TOP 1 M.NAME, SUM(OD.QUANTITY) AS Total
        FROM ORDERDETAILS OD
        JOIN MEAL M ON OD.MEALID = M.MEALID
        GROUP BY M.NAME
        ORDER BY Total DESC
    """)
    row = cursor.fetchone()
    print(f"Most Ordered Meal: {row[0]} - {row[1]} orders" if row else "No data.")

def order_prices_last_three_months():
    cursor.execute("""
        SELECT C._CUSTOMERID, C.FNAME, SUM(O.TOTALPRICE)
        FROM CUSTOMER C
        JOIN [ORDER] O ON C._CUSTOMERID = O._CUSTOMERID
        WHERE O.ORDERDATE >= DATEADD(MONTH, -3, GETDATE())
        GROUP BY C._CUSTOMERID, C.FNAME
    """)
    for row in cursor.fetchall():
        print(f"Customer {row[1]} (ID {row[0]}) spent: {row[2]}")

def meals_not_ordered():
    cursor.execute("""
        SELECT M.NAME FROM MEAL M
        LEFT JOIN ORDERDETAILS OD ON M.MEALID = OD.MEALID
        WHERE OD.MEALID IS NULL
    """)
    for row in cursor.fetchall():
        print(f"Not Ordered: {row[0]}")

def customer_highest_order_this_month():
    cursor.execute("""
        SELECT TOP 1 C.FNAME, SUM(O.TOTALPRICE)
        FROM CUSTOMER C
        JOIN [ORDER] O ON C._CUSTOMERID = O._CUSTOMERID
        WHERE MONTH(O.ORDERDATE) = MONTH(GETDATE()) AND YEAR(O.ORDERDATE) = YEAR(GETDATE())
        GROUP BY C.FNAME
        ORDER BY SUM(O.TOTALPRICE) DESC
    """)
    row = cursor.fetchone()
    print(f"Top Customer This Month: {row[0]} - Total: {row[1]}" if row else "No data.")

def meals_ordered_more_than_five_last_two_months():
    cursor.execute("""
        SELECT M.NAME, SUM(OD.QUANTITY)
        FROM ORDERDETAILS OD
        JOIN MEAL M ON OD.MEALID = M.MEALID
        JOIN [ORDER] O ON O.ORDERID = OD.ORDERID
        WHERE O.ORDERDATE >= DATEADD(MONTH, -2, GETDATE())
        GROUP BY M.NAME
        HAVING SUM(OD.QUANTITY) > 5
    """)
    for row in cursor.fetchall():
        print(f"{row[0]} - {row[1]} orders")

def customer_info_and_order_count():
    cursor.execute("""
        SELECT C._CUSTOMERID, C.FNAME, C.LNAME, C.EMAIL, COUNT(O.ORDERID)
        FROM CUSTOMER C
        LEFT JOIN [ORDER] O ON C._CUSTOMERID = O._CUSTOMERID
        GROUP BY C._CUSTOMERID, C.FNAME, C.LNAME, C.EMAIL
    """)
    for row in cursor.fetchall():
        print(f"ID: {row[0]}, Name: {row[1]} {row[2]}, Email: {row[3]}, Orders: {row[4]}")

# --------- MAIN MENU ---------
def main():
    while True:
        print("\n--- Food Ordering System ---")
        print("1. Add New Customer")
        print("2. Add New Meal")
        print("3. Place New Order")
        print("4. Show All Meals")
        print("5. Show Customer Orders")
        print("6. Update Customer")
        print("7. Remove Customer")
        print("8. Delete Meal")
        print("9. Update Meal")
        print("10. Show Menu with Category")
        print("11. Cancel Order")
        print("12. Search Meal by Name")
        print("13. Search Meal by Category")
        print("14. Search Meal by Price")
        print("15. Add Feedback")
        print("16. Modify Feedback")
        print("17. Delete Feedback")
        print("18. Most Ordered Meal")
        print("19. Order Prices Last 3 Months")
        print("20. Meals Not Ordered")
        print("21. Customer Highest Order This Month")
        print("22. Meals Ordered > 5 Times Last 2 Months")
        print("23. Customer Info and Order Count")
        print("24. Show All Feedback")
        print("25. Exit")

        choice = input("Choose an option: ")
        if choice == '1': insert_customer()
        elif choice == '2': insert_meal()
        elif choice == '3': place_order()
        elif choice == '4': show_all_meals()
        elif choice == '5': show_customer_orders()
        elif choice == '6': update_customer()
        elif choice == '7': remove_customer()
        elif choice == '8': delete_meal()
        elif choice == '9': update_meal()
        elif choice == '10': show_menu_with_category()
        elif choice == '11': cancel_order()
        elif choice == '12': search_meal_by_name()
        elif choice == '13': search_meal_by_category()
        elif choice == '14': search_meal_by_price()
        elif choice == '15': add_feedback()
        elif choice == '16': modify_feedback()
        elif choice == '17': delete_feedback()
        elif choice == '18': most_ordered_meal()
        elif choice == '19': order_prices_last_three_months()
        elif choice == '20': meals_not_ordered()
        elif choice == '21': customer_highest_order_this_month()
        elif choice == '22': meals_ordered_more_than_five_last_two_months()
        elif choice == '23': customer_info_and_order_count()
        elif choice == '24': show_all_feedback()
        elif choice == '25':
            print(" Goodbye!")
            break
        else:
            print(" Invalid option, try again.")

if __name__ == "__main__":
    main()
