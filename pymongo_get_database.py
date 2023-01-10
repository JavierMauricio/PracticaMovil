
from pymongo import MongoClient
import certifi
import dns.resolver

def get_database():

    #Android: dnspython tries to open /etc/resolv.conf
    #Just adde this code to the top of your main code, and that should be sufficient to get you past this hurdle
    dns.resolver.default_resolver=dns.resolver.Resolver(configure=False)
    dns.resolver.default_resolver.nameservers=['8.8.8.8']

    # Provide the mongodb atlas url to connect python to mongodb using pymongo
    CONNECTION_STRING = "mongodb+srv://sumgr:F03ja@cluster0.fqaevxn.mongodb.net/?retryWrites=true&w=majority"
    #s = MongoClient("mongodb+srv://m220student:m220password@cluster0.maiqr.mongodb.net", tlsCAFile=certifi.where())

    # Create a connection using MongoClient. You can import MongoClient or use pymongo.MongoClient
    client = MongoClient(CONNECTION_STRING, tlsCAFile=certifi.where())

    # Create the database for our example (we will use the same database throughout the tutorial
    return client['customer_shopping']
  
# This is added so that many files can reuse the function get_database()
if __name__ == "__main__":   
  
   # Get the database
   dbname = get_database()

"""
from kivy.app import App
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout

# import the MongoClient class
from pymongo import MongoClient, errors
import certifi

# global variables for MongoDB host (default port is 27017)
CONNECTION_STRING = "mongodb+srv://sumgr:F03ja@cluster0.fqaevxn.mongodb.net/?retryWrites=true&w=majority"

# use a try-except indentation to catch MongoClient() errors
try:
    # try to instantiate a client instance
    client = MongoClient(CONNECTION_STRING, tlsCAFile=certifi.where())

    # print the version of MongoDB server if connection successful
    print ("server version:", client.server_info()["version"])

except errors.ServerSelectionTimeoutError as err:
    # set the client and db names to 'None' and [] if exception
    client = None

    # catch pymongo.errors.ServerSelectionTimeoutError
    print ("pymongo ERROR:", err)

# create a new class for the Kivy MongoDB app
class MongoApp(App):

    # define the build() function for the app
    def build(self):

        # change the app's attributes
        self.title = 'ObjectRocket MongoDB App'

        # concatenate the host's domain and port variables
        self.mongo_domain = CONNECTION_STRING

        # set the layout for the Kivy application
        self.layout = BoxLayout(orientation='vertical')

        # change font title labels
        db_label = Label(font_size=50)
        domain_label = Label(font_size=40)

        # add the labels to the layout
        self.layout.add_widget(db_label)
        self.layout.add_widget(domain_label)

        # eval connection to MongoDB with global client instance
        if client != None:
            domain_label.text = "Connected!\n" + self.mongo_domain
            db_label.text = "Select a MongoDB database"
        else:
            # inform the user if the connection to MongoDB failed
            domain_label.text = "Your client's host parameters are invalid,"
            domain_label.text += "\nor your MongoDB server isn't running."
            db_label.text = "ERROR: Not connected to MongoDB"

        # return the layout at end of App class
        return self.layout

# run the MongoDB Kivy app class
MongoApp().run()
"""