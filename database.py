from peewee import PostgresqlDatabase

db = PostgresqlDatabase(
    "template1", host="localhost", port=5432,
    user="", password="",
)
