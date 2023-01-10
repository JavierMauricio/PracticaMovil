import kivy
kivy.require('2.1.0')

from kivymd.app import MDApp
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.properties import StringProperty
from pymongo import errors
from pymongo_get_database import get_database

dbname = get_database()  

class ScreenLogin(Screen):
    text = StringProperty()
    hint_text = StringProperty()

    def login_data(self):
        usuario = self.ids.text_usuario.text
        password = self.ids.text_password.text
        estado = False

        try:
            data = None
            # Create a new collection
            collection_name = dbname["usuario"]
            
            data = collection_name.find_one({'$and':[{'_id':{'company_id': 1, 'user_id': usuario}},{'password':password}]})
            mensaje = 'Usuario o Password incorrecto'
            #print('usu ', usuario, 'pass ', password, ' data ', data)
        except errors.ServerSelectionTimeoutError as err:
            mensaje = 'Los parámetros de host de su cliente no son válidos,\no su servidor MongoDB no se está ejecutando.\n'+str(err)
        except errors.OperationFailure as err:
            mensaje = str(err)

        if data != None:
            estado = True
            self.ids.label_login.text = 'Sesión Exitosa'
            self.ids.text_usuario.text = ''
            self.ids.text_password.text = ''
        else:
            self.ids.label_login.text = mensaje

        return estado

class ScreenOrder(Screen):
    pass

class LoginApp(MDApp):
    title = ''
    def build(self): 
        sm = ScreenManager()
        sm.add_widget(ScreenLogin(name='login'))
        sm.add_widget(ScreenOrder(name='orders'))

        self.theme_cls.primary_palette = 'Teal'    
        return sm
        
if __name__ == '__main__':
    LoginApp().run()

"""
rom kivy.app import App
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout

# import the MongoClient class
from pymongo import MongoClient, errors

# global variables for MongoDB host (default port is 27017)
DOMAIN = 'localhost:'
PORT = 27017

# use a try-except indentation to catch MongoClient() errors
try:
    # try to instantiate a client instance
    client = MongoClient(
        host = [ str(DOMAIN) + str(PORT) ],
        serverSelectionTimeoutMS = 3000 # 3 second timeout
    )

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
        self.mongo_domain = str(DOMAIN) + str(PORT)

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
            domain_label.text = "Connected!\n" + str(self.mongo_domain)
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