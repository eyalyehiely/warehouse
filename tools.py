import random,sqlite3



def query(sql):
    with sqlite3.connect('users.db') as conn:
        cur = conn.cursor()
        rows = cur.execute(sql)
        return list(rows)
    

def create_request_number():
    request_number = None
    try:
        starter_number = '#'
        for i in range(10):
            number = random.randrange(1, 10)
            starter_number += str(number)
        request_number = starter_number
        return request_number
    except:
        if request_number == query(f"SELECT request_number FROM requests WHERE request_number='{request_number}'"):
            random.shuffle(request_number)
        return str(request_number)