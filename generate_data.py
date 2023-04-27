from faker import Faker
import random
import sqlite3

fake = Faker()


def generate_data():
    conn = sqlite3.connect('company.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS employees
                 (id INTEGER PRIMARY KEY, name TEXT, salary REAL)''')

    for i in range(10000):
        name = fake.name()
        salary = random.uniform(1000, 10000)
        c.execute("INSERT INTO employees (id, name, salary) VALUES (?, ?, ?)",
                  (i+1, name, salary))

    conn.commit()
    conn.close()
