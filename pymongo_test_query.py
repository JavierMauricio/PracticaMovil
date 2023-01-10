# Get the database using the method we defined in pymongo_test_insert file
from pymongo_get_database import get_database
dbname = get_database()
 
# Create a new collection
collection_name = dbname["user_1_items"]
 
item_details = collection_name.find()
for item in item_details:
   # This does not give a very readable output
   print(item)
   print(item['item_name'], item['category'])

item_details = collection_name.find_one({'item_name':'Egg'},{'category':'food'})
print(item_details)

collection_name = dbname["usuario"]
users = collection_name.find()
for user in users:
   # This does not give a very readable output
   print(user)
   print(user['_id'], user['password'])
