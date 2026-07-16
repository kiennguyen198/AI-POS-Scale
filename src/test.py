import database

conn = database.connect_database()
cursor = database.create_cursor(conn)

price = database.get_price(cursor, "apple")

print(price)
print(type(price))