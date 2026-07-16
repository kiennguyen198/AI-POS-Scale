import sqlite3
# Mở kết nối tới database fruits.db
def connect_database():
    conn=sqlite3.connect('database/fruits.db')
    return conn

# Tạo cursor để gửi câu lệnh SQL tới database
# conn chỉ là kết nối, còn cursor mới là đối tượng thực thi SQL
def create_cursor(conn):
    cursor=conn.cursor()
    return cursor

# Tìm đơn giá của một loại trái cây
def get_price(cursor, fruit_name):
    sql = "SELECT price FROM Fruits WHERE name = ?"
    cursor.execute(sql, (fruit_name,))
    result = cursor.fetchone()
    if result is None:
        return None
    return result[0]