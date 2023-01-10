import kivy
kivy.require('2.1.0')

from datetime import datetime
import pandas as pd
import openpyxl
import pytz
from functools import partial
import io
import os
from kivy.core.window import Window
import requests
from PIL import Image
import gridfs
import smtplib, ssl
from pymongo import errors
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from kivy.factory import Factory
from kivymd.uix.bottomsheet import MDCustomBottomSheet
from kivy.metrics import dp
from kivy.uix.image import CoreImage
from kivy.uix.boxlayout import BoxLayout
from kivymd.uix.tab import MDTabsBase
from kivymd.uix.floatlayout import MDFloatLayout
from kivymd.uix.list import TwoLineAvatarListItem, ImageLeftWidget
from kivy.uix.recycleboxlayout import RecycleBoxLayout
from kivy.uix.behaviors import FocusBehavior
from kivy.uix.recycleview.layout import LayoutSelectionBehavior
from kivymd.uix.list import OneLineIconListItem
from kivymd.uix.pickers import MDDatePicker
from kivy.uix.recycleview.views import RecycleDataViewBehavior
from kivymd.uix.datatables import MDDataTable
from kivymd.uix.menu import MDDropdownMenu
from kivy.uix.popup import Popup
from kivymd.app import MDApp
from kivy.uix.button import Button
from kivymd.uix.filemanager import MDFileManager
from kivymd.toast import toast
from kivy.properties import ObjectProperty, StringProperty, NumericProperty, ListProperty
from kivy.clock import Clock
from pymongo_get_database import get_database

#Establece conexión a la base de datos
dbname = get_database()  
#Establece id de compañia y nombre
company_id = 1
company_name = 'Nutrición Mejorada para Animales de Compañia'
#imagen_id = None
#Establece id de usuario y lugar
user_id = ''
location_id = ''
categoria_id = ''
is_manager = False
account_name = ''
account_id = ''
#Establece conexión al servidor de correo
server =  "smtp.office365.com"
port = 587
sender_email = "ventassofting@hotmail.com"
#receiver_email = "softingjl@hotmail.com"
receiver_email = ['softingjl@hotmail.com']
password = "9Templarios"

message = MIMEMultipart("alternative")
message["Subject"] = "multipart test"
message["From"] = sender_email
message["To"] = receiver_email

#clase root
class Menu(BoxLayout):
    #Oculta menu item
    def hide_menu_item(self):
        #Display ids de Menu
        #for key, val in self.ids.items():
        #    print("key={0}, val={1}".format(key, val))

        #usuario socio oculta menu item cuenta user y transfer data
        if categoria_id == 'socio' or (categoria_id == 'local' and not is_manager):
            self.ids.content_nav_drawer.hide_menu_item()
            #bottoms enviar y entrega, screen analisis
            if categoria_id == 'socio':
                self.ids.consulta_orden.hide_bottom()

        #Set image app
        #self.ids.content_nav_drawer.set_image_app()

        return 'open'

#Confirmar salir de app
class ExitPopup(Popup):

    def __init__(self, **kwargs):
        super(ExitPopup, self).__init__(**kwargs)
        self.register_event_type('on_confirm')

    def on_confirm(self):
        pass

    def on_button_yes(self):
        self.dispatch('on_confirm')
###
#Contenido del Menu.
class ContentNavigationDrawer(BoxLayout):
    screen_manager = ObjectProperty()
    nav_drawer = ObjectProperty()

    def stop(self, *largs):
        # Open the popup you want to open and declare callback if user pressed `Yes`
        content = Button(text='Salir')
        popup = ExitPopup(title="Esta seguro?",
                          content=content,
                          size=(400, 400), size_hint=(None, None)
                          )
        content.bind(on_release=NavigationApp().stop)
        #popup.bind(on_confirm=partial(self.close_app, *largs))
        popup.open()

    #def close_app(self, *largs):
    #    super(NavigationApp(), self).stop(*largs)

    #Oculta menu
    def hide_menu_item(self):
        #cuenta de user
        self.ids.listitem_cuenta.width = 0
        self.ids.listitem_cuenta.height = 0
        self.ids.listitem_cuenta.opacity = 0
        #transfer data
        self.ids.listitem_transfer.width = 0
        self.ids.listitem_transfer.height = 0
        self.ids.listitem_transfer.opacity = 0

    #def set_image_app(self):

        #Set image avatar
        #Opcion 2. De una url
        #response = requests.get('https://github.com/JavierMauricio/PartnerOrders/blob/main/images/clip.png?raw=true')
        #img = Image.open(io.BytesIO(response.content))
        #imagen  = CoreImage(io.BytesIO(response.content), ext="png").texture

        #gfs = gridfs.GridFS(dbname)
        #id = gfs.get(imagen_id)
        #data = io.BytesIO(id.read())
        #imagen  = CoreImage(data, ext="png").texture
        #self.ids.avatar.source = 'https://github.com/JavierMauricio/PartnerOrders/blob/main/images/clip.png?raw=true'

        #print('image ok')

#Screen consulta orden
class ConsultaOrdenScreen(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        #Prepared file manager
        Window.bind(on_keyboard=self.events)
        self.manager_open = False
        self.file_manager = MDFileManager(
            exit_manager=self.exit_manager, select_path=self.select_path, background_color_selection_button="brown"
        )

        #Prepared head and content table
        self.thead_local = [("Id", dp(25), None, ""),("Nombre",dp(20), None, ""),("Lugar",dp(20), None, ""),("fecha",dp(18), None, ""),("Entrega",dp(18), None, "")]
        self.thead_foreign = [("Id", dp(25), None, ""),("fecha",dp(18), None, ""),("Entrega",dp(18), None, ""),("Comments",dp(20), None, "")]
        self.thead_product= [("Descripción", dp(30), None, ""),("Cantidad",dp(30), None, ""),("Precio",dp(30), None, "")]
        self.orden_content = []
        self.table = None
        
        #find order, no aplica pipe
        """
        pipe = [ { '$match' : { '_id.location_id' : location_id,
                                '_id.user_id' : user_id
                            }
                    },
                    {'$lookup': {
                        'from': "producto",
                        'localField': "producto.item_id",
                        'foreignField': "_id",
                        'as': "producto_order"
                        }
                    },
                    {'$sort': {'fecha_create': -1, '_id.order_id': 1}},
                    {'$limit': 10},
                    {'$project':{'producto_order.categoria':0, 
                                    'producto_order.clase':0, 
                                    'producto_order.precio':0, 
                                    'producto_order.imagen_id':0,
                                    'producto_order.fechaInsert':0, 
                                    'producto_order.fechaUpdate':0, 
                                    'producto_order.user_id':0, 
                                    'producto_order.fecha_create':0
                                }
                    } 
                ]
        """
        self.collection_user = dbname["usuario"]
        self.collection_product = dbname["producto"]
        self.collection_name = dbname["order"]
    #Oculta bottom
    def hide_bottom(self):
        #entrega y enviar
        self.ids.bottom_entrega.opacity = 0
        self.ids.bottom_entrega.disabled = True
        self.ids.bottom_enviar.opacity = 0
        self.ids.bottom_enviar.disabled = True
        #screen analisis
        #self.ids.screen_3.disabled = True
        self.ids['bottom_nav'].remove_widget(self.ids.screen_3)

    #File manager
    def file_manager_open(self):
        self.file_manager.show(os.path.expanduser("~"))  # output manager to the screen
        self.manager_open = True

    def select_path(self, path: str):
        '''
        It will be called when you click on the file name
        or the catalog selection button.

        :param path: path to the selected directory or file;
        '''
        order_list = []
        table_data = self.table.table_data
        
        for page, selected_cells in table_data.current_selection_check.items():
            for column_index in selected_cells:
                data_index = int(page * table_data.rows_num + column_index / table_data.total_col_headings)
                for order in self.order_producto:
                    if str(order['_id']['order_id']) == self.table.row_data[data_index][0] and order['_id']['location_id'] == self.table.row_data[data_index][2]:
                        #Get name user, para la orden
                        user = self.collection_user.find_one(
                            { 
                                '_id': 
                                    {
                                        'company_id': company_id,
                                        'user_id': order["_id"]["user_id"],
                                    }
                            }
                        )
                        if user != None:
                            id_user = user['id']
                        else:
                            id_user = 'NE'
                        for product in order['producto']:
                            orden = []
                            orden.append('S'+str(order['_id']['order_id']))
                            orden.append(id_user)
                            orden.append(datetime.now().strftime("%d/%m/%Y"))
                            orden.append(1)
                            orden.append(1)
                            orden.append(1)
                            orden.append(order['_id']['location_id']+': '+order['comment'])
                            orden.append('v')
                            orden.append(order['_id']['order_id'])
                            orden.append(datetime.now().strftime("%d/%m/%Y"))
                            orden.append(datetime.now().strftime("%d/%m/%Y"))
                            orden.append(product['precio'])
                            orden.append(0)
                            orden.append(0)
                            orden.append(0)
                            orden.append(0)
                            orden.append(1)
                            orden.append(product['item_id'])
                            orden.append(product['cantidad'])
                            orden.append(0)
                            orden.append(0)
                            orden.append(0)
                            orden.append(16)
                            orden.append(1)
                            orden.append('')
                            orden.append('')
                            orden.append('')
                           
                            order_list.append(orden)
                        break

                self.order_producto.rewind()
        df=pd.DataFrame(order_list,columns = ['Clave','Cliente', 'Fecha_Elaboracion', 'Almacen','Moneda','Tipo de cambio','Observaciones', 
        'Vendedor','Su pedido', 'Fecha de entrega','Fecha de vencimiento','Precio','Dec 1','Decs 2','Desc 3','Comisión','Esquema','Articulo','Cantidad',
        'Ieps','Impuesto 2','Impuesto 3','Iva','Almacen','Clave sat','Unidad','Observaciones'])
        
        df.to_excel(path+'/orden.xlsx', index=False)
        
        self.exit_manager()
        toast('Extracción realizada en '+path+'/orden.xlsx')

    def exit_manager(self, *args):
        '''Called when the user reaches the root of the directory tree.'''

        self.manager_open = False
        self.file_manager.close()

    def events(self, instance, keyboard, keycode, text, modifiers):
        '''Called when buttons are pressed on the mobile device.'''

        if keyboard in (1001, 27):
            if self.manager_open:
                self.file_manager.back()
        return True
    ###
    #Events Table order_product
    def on_row_press(self, instance_table, instance_row):
        '''Called when a table row is clicked.'''

        # get start, end index from selected row item range
        start_index, end_index = instance_row.table.recycle_data[instance_row.index]["range"]
        
        # loop over selected row items
        """
        for i in range(start_index, end_index):
            print(instance_row.table.recycle_data[i]["text"])
        """
        #Establece el número de orden
        self.ids.date_label_orden.text = f'{"Orden # "} - {instance_row.table.recycle_data[start_index]["text"]}'
        
        #prepared view product order
        self.ids['data_table_product_order'].clear_widgets()
        product_content = []
        cantidad = 0
        importe = 0
        for order in self.order_producto:
            if str(order['_id']['order_id']) == instance_row.table.recycle_data[start_index]["text"]:
                for product in order['producto']:
                    producto = self.collection_product.find_one(
                        {
                            '_id': {
                                'company_id': company_id,
                                'item_id': product['item_id']
                                }
                        }
                    )
                    product_content.append((producto['descripcion'], product['cantidad'], product['precio']))
                    cantidad += product['cantidad']
                    importe += product['cantidad'] * product['precio']
                self.ids.text_articulo.text = str(len(order['producto'])) + ' Art.'
                self.ids.text_cantidad.text = str(cantidad) + ' B'
                self.ids.text_importe.text = 'Total ' + '{0:.2f}'.format(importe)
                #Establece el comentario
                if "comment" in order:
                    comment = order["comment"]
                else:
                    comment = ""
                self.ids.text_comment.text = f'{comment}'
                break
        
        #create table
        self.table_product = MDDataTable(
            use_pagination = True,
            check = False,
            column_data = self.thead_product,
            row_data = product_content,
            sorted_on="Schedule",
            sorted_order="ASC",
            elevation=2,
        )
        #self.table.bind(on_row_press=self.on_row_press)
        #self.table.bind(on_check_press=self.on_check_press)
        self.ids['data_table_product_order'].add_widget(self.table_product)
        #rewind cursor
        self.order_producto.rewind()
        #switch tab productos por orden
        self.ids.bottom_nav.switch_tab('screen 2')

    def on_check_press(self, instance_table, current_row):
        '''Called when the check box in the table row is checked.'''
    ###
    #Display orders limit 10
    def get_data(self):
                   
        #prepara view
        self.ids['data_table'].clear_widgets()

        if categoria_id == 'socio':
            #self.order_producto = self.collection_name.aggregate(pipe)
            self.order_producto = self.collection_name.find(
                { 
                    '_id.company_id': company_id,
                    '_id.location_id' : location_id, 
                    '_id.user_id' : user_id
                }
            ).sort([('fecha_create', -1), ('_id.order_id', 1)]).limit(10)
        else:
            self.order_producto = self.collection_name.find(
                { 
                    '_id.company_id': company_id,
                }
            ).sort([('fecha_create', -1), ('_id.order_id', 1)]).limit(10)

        #agrega order
        self.orden_content = []
        for order in self.order_producto:
            if  "fecha_delivery" in order:
                fecha_delivery =  order["fecha_delivery"].strftime("%d/%m/%Y")
            else:
                fecha_delivery = ""
            
            """
            if "comment" in order:
                comment = order["comment"]
            else:
                comment = ""
            """
            #Get name user, para la orden
            user = self.collection_user.find_one(
                { 
                    '_id': 
                        {
                            'company_id': company_id,
                            'user_id': order["_id"]["user_id"],
                        }
                }
            )
            if user != None:
                name = user['nombre']
            else:
                name = 'NE'

            self.orden_content.append((str(order["_id"]["order_id"]), name, order["_id"]["location_id"], order["fecha_create"].strftime("%d/%m/%Y"), fecha_delivery))
       #create table
        self.table = MDDataTable(
            use_pagination = True,
            check = True,
            column_data = self.thead_local,
            row_data = self.orden_content,
            sorted_on="Schedule",
            sorted_order="ASC",
            elevation=2,
        )
        self.table.bind(on_row_press=self.on_row_press)
        self.table.bind(on_check_press=self.on_check_press)
        self.ids['data_table'].add_widget(self.table)
        #rewind cursor
        self.order_producto.rewind()
    ###
    # Click OK range
    def on_save_range(self, instance, value, date_range):
        #Establece rango de fecha
        self.ids.date_label.text = f'{date_range[0].strftime("%d/%m/%Y")} - {date_range[-1].strftime("%d/%m/%Y")}'
        #find order, segun rango de fecha, no aplica pipe
        """
        pipe = [ { '$match' : { '_id.location_id' : location_id,
                                '_id.user_id' : user_id,
                                'fecha_create': {'$gte': datetime(date_range[0].year, date_range[0].month, date_range[0].day, 0, 0, 0), '$lt': datetime(date_range[-1].year, date_range[-1].month, date_range[-1].day, 23, 59, 59)}
                            }
                    },
                    {'$lookup': {
                        'from': "producto",
                        'localField': "producto.item_id",
                        'foreignField': "_id",
                        'as': "producto_order"
                        }
                    },
                    {'$sort': {'fecha_create': 1, '_id.order_id': 1}},
                    {'$project':{'producto_order.categoria':0, 
                                    'producto_order.clase':0, 
                                    'producto_order.precio':0, 
                                    'producto_order.imagen_id':0,
                                    'producto_order.fechaInsert':0, 
                                    'producto_order.fechaUpdate':0, 
                                    'producto_order.user_id':0, 
                                    'producto_order.fecha_create':0
                                }
                    } 
                ]
        """
        #prepara view
        self.ids['data_table'].clear_widgets()
        self.orden_content = []
        if categoria_id == 'socio':
            #self.order_producto = self.collection_name.aggregate(pipe)
            self.order_producto = self.collection_name.find(
                                {
                                    '_id.company_id': company_id,
                                    '_id.location_id' : location_id,
                                    '_id.user_id' : user_id,
                                    'fecha_create': {'$gte': datetime(date_range[0].year, date_range[0].month, date_range[0].day, 0, 0, 0), '$lt': datetime(date_range[-1].year, date_range[-1].month, date_range[-1].day, 23, 59, 59)}
                                }).sort([('fecha_create', -1), ('_id.order_id', 1)])
        else:
            self.order_producto = self.collection_name.find(
                                {
                                    '_id.company_id': company_id,
                                    'fecha_create': {'$gte': datetime(date_range[0].year, date_range[0].month, date_range[0].day, 0, 0, 0), '$lt': datetime(date_range[-1].year, date_range[-1].month, date_range[-1].day, 23, 59, 59)}
                                }).sort([('fecha_create', -1), ('_id.order_id', 1)])
        
        #agrega order
        for order in self.order_producto:
            if  "fecha_delivery" in order:
                fecha_delivery =  order["fecha_delivery"].strftime("%d/%m/%Y")
            else:
                fecha_delivery = ""

            """
            if "comment" in order:
                comment = order["comment"]
            else:
                comment = ""
            """

            #Get name user, para la orden
            user = self.collection_user.find_one(
                { 
                    '_id': 
                        {
                            'company_id': company_id,
                            'user_id': order["_id"]["user_id"],
                        }
                }
            )
            if user != None:
                name = user['nombre']
            else:
                name = 'NE'
            
            self.orden_content.append((str(order["_id"]["order_id"]), name, order["_id"]["location_id"], order["fecha_create"].strftime("%d/%m/%Y"), fecha_delivery))
        #create table
        self.ids['data_table'].clear_widgets()
        self.table = MDDataTable(
            use_pagination = True,
            check = True,
            column_data = self.thead_local,
            row_data = self.orden_content,
            sorted_on="Schedule",
            sorted_order="ASC",
            elevation=2,
        )
        self.table.bind(on_row_press=self.on_row_press)
        self.table.bind(on_check_press=self.on_check_press)
        self.ids['data_table'].add_widget(self.table)
        #rewind cursor
        self.order_producto.rewind()

    # Click Cancel range
    def on_cancel_range(self, instance, value):
        self.ids.date_label.text = "You Clicked Cancel"
    ###
    # Click OK
    def on_save(self, instance, value, date_range):

        #self.my_selections = []
        table_data = self.table.table_data
        
        for page, selected_cells in table_data.current_selection_check.items():
            #print(page, selected_cells)
            for column_index in selected_cells:
                #print('ci ', column_index, ' rn ', table_data.rows_num, 'h ', table_data.total_col_headings)
                data_index = int(page * table_data.rows_num + column_index / table_data.total_col_headings)
                #print('di ', data_index)
                #self.my_selections.append(table_data.row_data[data_index][0])
                self.table.update_row(self.table.row_data[data_index],[table_data.row_data[data_index][0],table_data.row_data[data_index][1],table_data.row_data[data_index][2],table_data.row_data[data_index][3],value.strftime("%d/%m/%Y")])

        #print('sel ', self.my_selections)

        
    # Click Cancel
    def on_cancel(self, instance, value):
        self.ids.date_label.text = "You Clicked Cancel"
    ###
    # Click OK range
    def on_save_range_delivery(self, instance, value, date_range):
        #Establece rango de fecha
        self.ids.date_label.text = f'{date_range[0].strftime("%d/%m/%Y")} - {date_range[-1].strftime("%d/%m/%Y")}'
        
        #prepara view
        self.ids['data_table'].clear_widgets()
        self.orden_content = []
        if categoria_id == 'socio':
            #self.order_producto = self.collection_name.aggregate(pipe)
            self.order_producto = self.collection_name.find(
                                {
                                    '_id.company_id': company_id,
                                    '_id.location_id' : location_id,
                                    '_id.user_id' : user_id,
                                    'fecha_delivery': {'$gte': datetime(date_range[0].year, date_range[0].month, date_range[0].day, 0, 0, 0), '$lt': datetime(date_range[-1].year, date_range[-1].month, date_range[-1].day, 23, 59, 59)}
                                }).sort([('fecha_delivery', -1), ('_id.order_id', 1)])
        else:
            self.order_producto = self.collection_name.find(
                                {
                                    '_id.company_id': company_id,
                                    'fecha_delivery': {'$gte': datetime(date_range[0].year, date_range[0].month, date_range[0].day, 0, 0, 0), '$lt': datetime(date_range[-1].year, date_range[-1].month, date_range[-1].day, 23, 59, 59)}
                                }).sort([('fecha_delivery', -1), ('_id.order_id', 1)])
        
        #agrega order
        for order in self.order_producto:
            if  "fecha_delivery" in order:
                fecha_delivery =  order["fecha_delivery"].strftime("%d/%m/%Y")
            else:
                fecha_delivery = ""
            """
            if "comment" in order:
                comment = order["comment"]
            else:
                comment = ""
            """
            #Get name user, para la orden
            user = self.collection_user.find_one(
                { 
                    '_id': 
                        {
                            'company_id': company_id,
                            'user_id': order["_id"]["user_id"],
                        }
                }
            )
            if user != None:
                name = user['nombre']
            else:
                name = 'NE'

            self.orden_content.append((str(order["_id"]["order_id"]), name, order["_id"]["location_id"], order["fecha_create"].strftime("%d/%m/%Y"), fecha_delivery))
        #create table
        self.ids['data_table_entrega'].clear_widgets()
        self.table = MDDataTable(
            use_pagination = True,
            check = True,
            column_data = self.thead_local,
            row_data = self.orden_content,
            sorted_on="Schedule",
            sorted_order="ASC",
            elevation=2,
        )
        self.table.bind(on_row_press=self.on_row_press)
        self.table.bind(on_check_press=self.on_check_press)
        self.ids['data_table_entrega'].add_widget(self.table)
        #rewind cursor
        self.order_producto.rewind()

    # Click Cancel range
    def on_cancel_range_delivery(self, instance, value):
        self.ids.date_label.text = "You Clicked Cancel"
    ###
    #Display datepicker
    def show_date_picker(self, accion):
        #date_dialog = MDDatePicker(year=2000, month=2, day=14)
        if accion == 0: #ordenes en un rango de fechas
            date_dialog = MDDatePicker(mode="range")
            date_dialog.bind(on_save=self.on_save_range, on_cancel=self.on_cancel_range)
            date_dialog.open()
        elif accion == 1:#establece la fecha de entrega
            date_dialog = MDDatePicker()
            date_dialog.bind(on_save=self.on_save, on_cancel=self.on_cancel)
            date_dialog.open()
        elif accion == 2: #ordenes en un rango de fechas de entrega
            date_dialog = MDDatePicker(mode="range")
            date_dialog.bind(on_save=self.on_save_range_delivery, on_cancel=self.on_cancel_range_delivery)
            date_dialog.open()
    ###
    #Actualiza datos en mongodb y notifica por mail a compañia
    def send_data(self):

        #Verifica orders check and exist fecha entrega
        table_data = self.table.table_data
        orders_check = 0

        for page, selected_cells in table_data.current_selection_check.items():
            orders_check += len(selected_cells)
        
        if orders_check == 0:
            toast('No selecciono ordenes')
            return
        else:#exist entrega
            for page, selected_cells in table_data.current_selection_check.items():
                for column_index in selected_cells:
                    data_index = int(page * table_data.rows_num + column_index / table_data.total_col_headings)
                    #print('r ', self.table.row_data[data_index])
                    if self.table.row_data[data_index][4] == '':
                        toast('Entrega No definida en orden '+self.table.row_data[data_index][0])
                        return

        #Enviar si hay productos
        pacific = pytz.timezone('America/Monterrey')
        aware_datetime = pacific.localize(datetime.now())
        
        time = str(aware_datetime.hour) + ':' + str(aware_datetime.minute) + ':' + str(aware_datetime.second)    
        
        #crear lista de productos
        order_delivery = []
        for page, selected_cells in table_data.current_selection_check.items():
            for column_index in selected_cells:
                data_index = int(page * table_data.rows_num + column_index / table_data.total_col_headings)
                fecha_delivery = self.table.row_data[data_index][4] + ' ' + time
                #fecha_update = str(aware_datetime.day) + '/' + str(aware_datetime.month) + '/' + str(aware_datetime.year) + ' ' + time

                #Get id user, para la orden
                id_user = ''
                for order in self.order_producto:
                    if order['_id']['order_id'] == int(self.table.row_data[data_index][0]):
                        id_user = order['_id']['user_id']
                        break
                self.order_producto.rewind()
                
                result = self.collection_name.update_one(
                    {
                        '_id':
                            {
                                'company_id': company_id,
                                'order_id': int(self.table.row_data[data_index][0]), 
                                'location_id': self.table.row_data[data_index][2], 
                                'user_id': id_user
                            }
                    }, 
                    {
                        '$set':
                            {
                                'fecha_delivery':datetime.strptime(fecha_delivery, "%d/%m/%Y %H:%M:%S"), 'fecha_update': datetime.now()
                                
                            }
                    }, 
                    upsert=False
                )
                
                order_delivery.append({'orden':self.table.row_data[data_index][0], 
                    'nombre':self.table.row_data[data_index][1],
                    'lugar':self.table.row_data[data_index][2], 
                    'fecha_delivery':datetime.strptime(fecha_delivery, "%d/%m/%Y %H:%M:%S")})
   
        # Create the container (outer) email message.
        msg = MIMEMultipart("alternative")
        msg['Subject'] = 'Notificaciones de Orden por entregar'
        msg['From'] = sender_email
        msg['To'] = ", ".join(receiver_email) #receiver_email
        #msg.preamble = 'La orden ' + user_id + ' creo la orden ' + str(order_number)

        table_content = []
        for order in order_delivery:
            table_content.append(f'''\
                <tr style="background-color: aliceblue">
                    <td style="padding: 1rem">{order['orden']}</td>
                    <td style="padding: 1rem">{order['nombre']}</td>
                    <td style="padding: 1rem">{order['lugar']}</td>
                    <td style="padding: 1rem">{order["fecha_delivery"].strftime("%d/%m/%Y")}</td>
                </tr>
            ''')
        tc = '\n'.join(table_content)
        html = f'''\
            <html>
                <body>
                     <div class="section" style="background: rgb(241, 234, 227);">
                        <hr size="8" width="50%" color="#6CACE9"/>               
                        <h2 style="color:#20578b;text-align: center;">{company_name}</h2> 
                        <div class="row align-items-start">                                            
                            <div class="col-xs-7" style="background-color: white;width: 50%;margin: auto;padding: 10px;border-radius: 5px;">                        
                                <h2>Atención, Ordenes por Entregar,</h2>
                                <hr color=" #f6f6f6"/>
                                <table style="margin: 3px">
                                    <caption>Listado</caption>
                                    <tr style="background-color: #c3a97d">
                                        <th style="color: white">Id</th>
                                        <th style="color: white">Nombre</th>
                                        <th style="color: white">Lugar</th>
                                        <th style="color: white">Entrega</th>
                                    </tr>
                                    {tc}
                                </table>
                                <p>¡Gracias!</p>                      
                            </div>
                            <br>
                            <p style="width: 50%;margin: auto;padding: 10px;"><small>&#169; 2022 {company_name}</small></p>                
                        </div>
                    </div>
                </body>
            </html>
            '''
        part = MIMEText(html, "html")
        msg.attach(part)

        # Send the email via our own SMTP server.
        send = smtplib.SMTP(server, port)
        send.ehlo()
        send.starttls()
        send.login(sender_email, password)
        #Adding a newline before the body text fixes the missing message body
        send.sendmail(sender_email,receiver_email,msg.as_string())
        send.quit()

        #self.ids['data_table'].clear_widgets()
        #self.orden_content = []
        toast('Entregas de orden enviadas')
        
    ###

#Screen nueva orden
class NuevaOrdenScreen(BoxLayout):
    #CardTab
    value = NumericProperty(1)

    """
    def __init__(self, *args, **kwargs):
        super().__init__()"""

    #ProductoTab
    def get_data(self):
        """
        #Create an object of GridFs for the above database.
        gfs = gridfs.GridFS(dbname)

        #read one image
        id="ADB001"
        collection_name = dbname["producto"]
        producto = collection_name.find_one({'_id': id})
        imagen_id = gfs.get(producto['imagen_id'])
        base64_data = encode(imagen_id.read(), 'base64')
        imagen = base64_data.decode('utf-8')
        """
        self.ids.productotab.set_list_products()
        #self.ids.ordentab.set_list_products()
    ###   
    #No utilizada
    def create_data(self):
        #Create an object of GridFs for the above database.
        gfs = gridfs.GridFS(dbname)

        #define an image object with the location.
        file_imagen = "cart.png"

        #Open the image in read-only format.
        with open(file_imagen, 'rb') as file:
            contents = file.read()

        #Now store/put the image via GridFs object.
        imagen_id = gfs.put(contents, content_type='Imagen', filename=file.name)

        pacific = pytz.timezone('America/Monterrey')
        aware_datetime = pacific.localize(datetime.utcnow())
        document={
            '_id': 'ADB010',
            'descripcion': 'Copdi', 
            'categoria': 'Aplicación', 
            'clase': 'Programa',
            'precio': 670.0, 
            'imagen_id': imagen_id,
            'user_id':'sumgr',
            'fecha_create': aware_datetime,
        }

        # Create a new collection or document
        collection_name = dbname["producto"]
        resultado = collection_name.insert_one(document)
        """
        #counter
        document={
            '_id': {'id': 'order_id','location_id':'cdmx'},
            'secuencia': 0,
            'user_id':'sumgr',
            'fecha_create': aware_datetime,
        }

        # Create a new collection or document
        collection_name = dbname["counter"]
        resultado = collection_name.insert_one(document)

        document={
            '_id': {'id': 'order_id','location_id':'acap'},
            'secuencia': 0,
            'user_id':'sumgr',
            'fecha_create': aware_datetime,
        }

        # Create a new collection or document
        resultado = collection_name.insert_one(document)

        document={
            '_id': {'id': 'order_id','location_id':'taps'},
            'secuencia': 0,
            'user_id':'sumgr',
            'fecha_create': aware_datetime,
        }

        # Create a new collection or document
        resultado = collection_name.insert_one(document)
        """
    def delete_data(self):
        #Create an object of GridFs for the above database.
        gfs = gridfs.GridFS(dbname)

        #delete image
        collection_name = dbname["producto"]
        productos = collection_name.find(
            {
                '_id.company_id' : company_id
            }
        )
        for item in productos:
            if item != None:
                collection_name.delete_one({'_id':item['_id']})
                gfs.delete(item['imagen'])

    #OrdenTab
    #opcion simple
    def recibe_cantidad_emergente(self, item, cantidad, tarea):
        
        if tarea == 0:
            if self.ids.ordentab.searchsingle(item) is False:
                self.ids.ordentab.addsingle(item, cantidad)
                #self.ids.cardtab.addsingle(item, cantidad)
            else:
                #toast('El producto ' + item['descripcion'] + ' ya existe', background=[1,0,0,1])
                toast('El producto ' + item['descripcion'] + ' ya existe')
        else:
            self.ids.ordentab.updatesingle(item, cantidad)

    def set_cantidad_emergente(self, item):
        self.ids.ordentab.set_cantidad_emergente(item)

    def remove_producto(self, item):
        self.ids.ordentab.removesingle(item)
    ###
    #CardTab 
    def show_custom_bottom_sheet(self,item_id,image,price,rate, avg_rate, quantity, name, average_rating):
        bottom_sheet=Factory.ContentCustomSheet()
        bottom_sheet.item_id = item_id
        bottom_sheet.rate = rate
        bottom_sheet.avg_rate = avg_rate
        bottom_sheet.image = image
        bottom_sheet.price = price
        bottom_sheet.quantity = quantity
        self.value = int(quantity)
        bottom_sheet.name = name
        bottom_sheet.average_rating = average_rating
        bottom_sheet.ocultar = ''
        self.custom_sheet = MDCustomBottomSheet(screen=bottom_sheet)
        #select el rate activo
        if rate == '1':
            bottom_sheet.ids.check1.active = True
        if rate == '2':
            bottom_sheet.ids.check2.active = True
        if rate == '3':
            bottom_sheet.ids.check3.active = True
        if rate == '4':
            bottom_sheet.ids.check4.active = True
        if rate == '5':
            bottom_sheet.ids.check5.active = True
    
        self.custom_sheet.open()

    def plus(self):
        self.event = Clock.schedule_interval(lambda dt: setattr(self, 'value', self.value + 1), 1)
        self.value += 1

    def minus(self):
        self.event = Clock.schedule_interval(lambda dt: setattr(self, 'value', self.value - 1), 1)
        self.value -= 1
        if self.value <= 0:
            self.value = 1

    def stopupdate(self):
        self.event.cancel()

    def add_producto_card(self, item, cantidad, rate1, rate2, rate3, rate4, rate5):
        
        if self.ids.cardtab.searchsingle(item) is False:
            self.ids.cardtab.addsingle(item, cantidad, rate1, rate2, rate3, rate4, rate5)
            #self.ids.ordentab.addsingle(item, cantidad) #convertir cantidad s str
            self.value = 1
            #descartar
            self.ids.productotab.custom_sheet.dismiss()
        else:
            #toast('El producto ' + item['descripcion'] + ' ya existe', background=[1,0,0,1])
            toast('El producto ' + item['descripcion'] + ' ya existe')


    def update_producto_card(self, item_id, rate1, rate2, rate3, rate4, rate5):
        self.ids.cardtab.updatesingle(item_id, self.value, rate1, rate2, rate3, rate4, rate5)
        self.value = 1
        #descartar
        self.custom_sheet.dismiss()

    def remove_producto_card(self, item_id):
        self.ids.cardtab.removesingle(item_id)
        self.value = 1
        #descartar
        self.custom_sheet.dismiss()
        
    ###
#ventana emergnete del tab producto
class CantidadPopup(Popup):
    item = ObjectProperty()
    tarea = NumericProperty()#0: productos, 1: ordenes

#Tab de productos en ConsultaOrdenScreeen
class SelectableRecycleBoxLayout(FocusBehavior, LayoutSelectionBehavior, RecycleBoxLayout):
    ''' Adds selection and focus behaviour to the view. '''

class SelectableTwoLineAvatarListItem(RecycleDataViewBehavior, TwoLineAvatarListItem):
    source = ObjectProperty() 

class CardTab(BoxLayout, MDTabsBase):

    def __init__(self, **kwargs):
        super(CardTab, self).__init__(**kwargs)
        self.orden_content = []

    #Localiza item
    def searchsingle(self, item):
        
        existe_item = False
        
        for i in self.orden_content:
            if i['id'] == item['_id']['item_id']:
                existe_item = True
                break

        return existe_item

    def addsingle(self, item, cantidad, rate1, rate2, rate3, rate4, rate5):
        
        #prepara view
        self.ids['gl'].clear_widgets()

        #Rate
        rate = 0
        if rate1:
            rate = 1
        if rate2:
            rate = 2
        if rate3:
            rate = 3
        if rate4:
            rate = 4
        if rate5:
            rate = 5
        
        #agrega item
        if len(item["descripcion"]) > 20:
            descripcion = item["descripcion"][0:20]
        else:
            descripcion = item["descripcion"]

        #if item['product_rate']:
        #    for r in item['product_rate']:
        #        rate = r['rate']
        #else:
        #    rate = 0
        try:
            # do something with doc['properties.color'], e.g.:
            average_rating = item['average_rating']
        except KeyError:
            average_rating = 0
        
        self.orden_content.append({"id": item["_id"]["item_id"], "descripcion": item["descripcion"].title(), "cantidad": cantidad, "precio": item["precio"], "rate": rate, "imagen": item["imagen"], 'average_rating': average_rating})
        
        #contendo
        cantidad = 0
        importe = 0
        for i in self.orden_content:
            card = Factory.ElementCard(item_id=i['id'],image='images/'+i['imagen'], price='$ {0:.2f}'.format(i['precio']), rate=str(i['rate']), avg_rate='', quantity=str(i['cantidad']), name=i['descripcion'], average_rating=str(i['average_rating']))
            self.ids['gl'].add_widget(card)
            cantidad += float(str(i['cantidad']))
            importe += float(str(i['cantidad'])) * float(str(i['precio']))

        self.ids.text_articulo.text = str(len(self.orden_content))+' Art.'
        self.ids.text_cantidad.text = str(cantidad) + ' Pza'
        self.ids.text_importe.text = 'Total ' + '$ {0:.2f}'.format(importe)

    #Actualiza cantidad de item
    def updatesingle(self, item_id, cantidad, rate1, rate2, rate3, rate4, rate5):
        
        self.ids['gl'].clear_widgets()

        #Rate
        rate = 0
        if rate1:
            rate = 1
        if rate2:
            rate = 2
        if rate3:
            rate = 3
        if rate4:
            rate = 4
        if rate5:
            rate = 5

        #localiza item updated y actualizalo
        for i in self.orden_content:
            if i['id'] == item_id:
                self.orden_content[self.orden_content.index(i)]['cantidad'] = str(cantidad)
                self.orden_content[self.orden_content.index(i)]['rate'] = rate
                #try:
                #    # do something with doc['properties.color'], e.g.:
                #    average_rating = i['average_rating']
                #except KeyError:
                #    average_rating = 0
                break
        #Construye la view actulizada
        cantidad = 0
        importe = 0
        
        for i in self.orden_content:
            card = Factory.ElementCard(item_id=i['id'],image='images/'+i['imagen'], price='$ {0:.2f}'.format(i['precio']), rate=str(i['rate']), avg_rate='', quantity=str(i['cantidad']), name=i['descripcion'], average_rating=str(i['average_rating']))
            self.ids['gl'].add_widget(card)
            cantidad += float(str(i['cantidad']))
            importe += float(str(i['cantidad'])) * float(str(i['precio']))

        self.ids.text_articulo.text = str(len(self.orden_content))+' Art.'
        self.ids.text_cantidad.text = str(cantidad) + ' Pza'
        self.ids.text_importe.text = 'Total ' + '$ {0:.2f}'.format(importe)

    #Remueve item del carro
    def removesingle(self, item_id):

        self.ids['gl'].clear_widgets()

        # using del + loop 
        # to delete dictionary in list
        for i in range(len(self.orden_content)):
            if self.orden_content[i]['id'] == item_id:
                del self.orden_content[i]
                #try:
                #    # do something with doc['properties.color'], e.g.:
                #    average_rating = i['average_rating']
                #except KeyError:
                #    average_rating = 0
                break
        #Construir contenido del body
        cantidad = 0
        importe = 0
        
        for i in self.orden_content:
            card = Factory.ElementCard(item_id=i['id'],image='images/'+i['imagen'], price='$ {0:.2f}'.format(i['precio']), rate=str(i['rate']), avg_rate='', quantity=str(i['cantidad']), name=i['descripcion'], average_rating=str(i['average_rating']))
            self.ids['gl'].add_widget(card)
            cantidad += float(str(i['cantidad']))
            importe += float(str(i['cantidad'])) * float(str(i['precio']))

        self.ids.text_articulo.text = str(len(self.orden_content))+' Art.'
        self.ids.text_cantidad.text = str(cantidad) + ' Pza'
        self.ids.text_importe.text = 'Total ' + '$ {0:.2f}'.format(importe)

    #Envia datos a mongodb y notifica por mail a compañia
    def send_data(self):

        def get_order_id(id):

            self.collection_name = dbname["counter"]
            result = self.collection_name.find_one_and_update({'_id':{'company_id':company_id,'id':id,'location_id':location_id}}, {"$inc":{"secuencia":1}})
        
            return result['secuencia']
        #Enviar si hay productos
        if self.orden_content:
            #complete data dict
            order_number = get_order_id('order_id')
            
            pacific = pytz.timezone('America/Monterrey')
            aware_datetime = pacific.localize(datetime.now())

            self.collection_name = dbname["order"]
            #crear orden
            result = self.collection_name.insert_one(
                {'_id':
                        {
                            'company_id':company_id,
                            'order_id': order_number,
                            'location_id': location_id,
                            'user_id': user_id
                        },
                    'comment':self.ids.text_comment.text,
                    'producto':[],
                    'fecha_create': datetime.now()
                }
            )
            #crear lista de productos
            for item in self.orden_content:
                #result = self.collection_name.insert_one({'_id':{'order_id': order_number, 'location': location, 'user_id': user_id, 'item':item['id']}, 'cantidad':float(item['cantidad']), 'fecha_create': aware_datetime})
                result = self.collection_name.update_one(
                    {
                        '_id.company_id': company_id,
                        '_id.order_id': order_number,
                        '_id.location_id': location_id,
                        '_id.user_id': user_id
                    },
                    {
                        '$push':
                            {
                                'producto': 
                                    {
                                        'item_id': item['id'],
                                        'cantidad': float(item['cantidad']),
                                        'precio': float(item['precio'])
                                    }
                            }
                    }
                )
            #Update reviewrating
            list_products = []
            self.collection_name = dbname["reviewrating"]
            for item in self.orden_content:
                result = self.collection_name.update_one(
                    {
                        '_id': 
                            {
                                'company_id': company_id,
                                'user_id': user_id,
                                'product_id': item['id']
                            }
                    },
                    {
                        '$set':{
                            'rate': item['rate'], 
                            'fecha_update': datetime.now()
                        },
                        '$setOnInsert':{
                            '_id': 
                                {
                                    'company_id': company_id,
                                    'user_id': user_id,
                                    'product_id': item['id']
                                },
                            'fecha_create': datetime.now()
                        }
                    },
                    upsert=True
                )
                #append list
                list_products.append(item['id'])

            #Calcula Average rating, de los productos solicitados
            pipe = [ 
                        {
                            '$match' : 
                                {
                                    '$expr':
                                        { '$and':
                                            [
                                                { '$eq': [ "$_id.company_id",  company_id ] },
                                                { '$in': [ "$_id.product_id",  list_products ] },
                                            ]
                                        }
                                }
                        },
                        {
                            '$group' :
                                {
                                '_id' : {'company_id': '$_id.company_id', 'product_id':'$_id.product_id'},
                                'average_rating': {"$avg": { "$ifNull": ["$rate",0] } }
                                }
                        }
                    ]
            average_rating = self.collection_name.aggregate(pipe)
            list_products = []
            self.collection_name = dbname["producto"]

            #update average rating in products
            for avg in average_rating:
                result = self.collection_name.update_one(
                        {
                            '_id': 
                                {
                                    'company_id': avg['_id']['company_id'],
                                    'item_id': avg['_id']['product_id']
                                }
                        },
                        {
                            '$set':{
                                'average_rating':avg['average_rating']
                            }
                        }
                    )
                
            # Create the container (outer) email message.
            msg = MIMEMultipart("alternative")
            msg['Subject'] = 'Notificaciones de Nueva Orden'
            msg['From'] = sender_email
            msg['To'] = ", ".join(receiver_email) #receiver_email
            msg.preamble = 'El cliente ' + user_id + ' creo la orden ' + str(order_number)

            table_content = []
            cantidad = 0
            importe = 0
            for order in self.orden_content:
                cantidad += float(order['cantidad'])
                importe += float(order['cantidad']) * float(order['precio'])
                table_content.append(f'''\
                    <tr style="background-color: aliceblue">
                        <td style="padding: 1rem">{order['id']}</td>
                        <td style="padding: 1rem">{order['descripcion']}</td>
                        <td style="padding: 1rem">{order['cantidad']}</td>
                        <td style="padding: 1rem">{order['precio']}</td>
                    </tr>
                ''')
            tc = '\n'.join(table_content)
            html = f'''\
            <html>
                <body>
                     <div class="section" style="background: rgb(241, 234, 227);">
                        <hr size="8" width="50%" color="#6CACE9"/>               
                        <h2 style="color:#20578b;text-align: center;">{company_name}</h2> 
                        <div class="row align-items-start">                                            
                            <div class="col-xs-7" style="background-color: white;width: 50%;margin: auto;padding: 10px;border-radius: 5px;">                        
                                <h2>Solicitado por {account_name} de {location_id},</h2>
                                <hr color=" #f6f6f6"/>
                                <p>Nueva Orden:</p>
                                <p>Número: {str(order_number)}</p>
                                <p>Comentario: {self.ids.text_comment.text}</p> 
                                <table style="margin: 3px">
                                    <caption>Ordenes por entregar</caption>
                                    <tr style="background-color: #c3a97d">
                                        <th style="color: white">Id</th>
                                        <th style="color: white">Descripción</th>
                                        <th style="color: white">Cantidad</th>
                                        <th style="color: white">Precio</th>
                                    </tr>
                                    {tc}
                                <tfoot>
                                </tfoot>
                                    <tr>
                                        <th>Totales</th>
                                        <td>{str(len(self.orden_content))} Articulos</td>
                                        <td>{str(cantidad)}</td>
                                        <td>{'{0:.2f}'.format(importe)}</td>
                                    </tr>
                                </table>
                                <p>¡Gracias!</p>                      
                            </div>
                            <br>
                            <p style="width: 50%;margin: auto;padding: 10px;"><small>&#169; 2022 {company_name}</small></p>                
                        </div>
                    </div>
                </body>
            </html>
            '''
            part = MIMEText(html, "html")
            msg.attach(part)

            # Send the email via our own SMTP server.
            send = smtplib.SMTP(server, port)
            send.ehlo()
            send.starttls()
            send.login(sender_email, password)
            #Adding a newline before the body text fixes the missing message body
            send.sendmail(sender_email,receiver_email,msg.as_string())
            send.quit()

            self.ids['gl'].clear_widgets()
            self.orden_content = []
            self.ids.text_comment.text = ''
            self.ids.text_articulo.text = ''
            self.ids.text_cantidad.text = ''
            self.ids.text_importe.text = ''
            #NuevaOrdenScreen.value = 1
            
            toast('Tu número de orden es ' + str(order_number))

class ProductoTab(MDFloatLayout, MDTabsBase):
    label_text = StringProperty()
    content_text = StringProperty()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        #opción, find productos, sin rate
        self.collection_name = dbname["producto"]
        """
        self.productos = self.collection_name.find(
            {
                '_id.company_id' : company_id
            }
        ).sort('descripcion',1)
        self.total_count = self.collection_name.count_documents({})
        """       
        self.productos = []
        
    def set_list_products(self, text="",search=False):

        def add_item(item):
            #imagen_id = gfs.get(item['imagen_id'])
            #data = io.BytesIO(imagen_id.read())
            #imagen  = CoreImage(data, ext="png").texture
            imagen = 'images/'+item['imagen']
            #Opcion 2. De una url
            #response = requests.get('https://github.com/JavierMauricio/PartnerOrders/blob/main/images/cart.png?raw=true')
            #img = Image.open(io.BytesIO(response.content))
            #imagen  = CoreImage(io.BytesIO(response.content), ext="png").texture

            #widget = Image(source = 'cartt.png')
            #widget.texture = imagen
            self.ids.rv.data.append(
                {
                    "source": imagen,
                    "text": item['descripcion'].title(),
                    "secondary_text": 'Precio ' + f'$ {item["precio"]:,.2f}',
                    'on_release': partial(self.show_custom_bottom_sheet, item), #partial(self.set_cantidad_popup, item) forma tabla
                }
            )

        if not self.productos:
            #pipe, opción con rate
            pipe = [ 
                        {'$sort': {'descripcion': 1}},
                        {'$lookup': {
                                'from': "reviewrating",
                                'let': {'company_id': '$_id.company_id', 'product_id': '$_id.item_id'},
                                'pipeline': [
                                    { '$match':
                                        { '$expr':
                                            { '$and':
                                            [
                                                { '$eq': [ "$_id.company_id",  "$$company_id" ] },
                                                { '$eq': [ "$_id.user_id", user_id ] },
                                                { '$eq': [ "$_id.product_id",  "$$product_id" ] },
                                            ]
                                            }
                                        }
                                    },
                                    {'$project':
                                        {
                                            '_id': 0,
                                            'fecha_create': 0, 
                                            'fecha_update': 0,
                                        }
                                    }
                                ],
                                'as': "product_rate"
                            }
                        },
                    ]
            
            self.productos = list(self.collection_name.aggregate(pipe))
            #print('lista ',self.productos)
            #print('fin')
            #for i in self.productos:
            #    print(i)
        
        #Create an object of GridFs for the above database.
        #gfs = gridfs.GridFS(dbname)

        #loop productos
        self.ids.rv.data = []
        for item in self.productos:
            if item != None:
                if search:
                    if text.lower() in item['descripcion'].lower():
                        add_item(item)
                else:
                    add_item(item)

        #self.productos.rewind()

    #Establece la cantidad requerida en una ventana emergente
    def set_cantidad_popup(self, x):
        popup = CantidadPopup(item=x, tarea=0)
        popup.open()

    def show_custom_bottom_sheet(self,item):
        bottom_sheet=Factory.ContentCustomSheet()
        bottom_sheet.item_id = item['_id']['item_id']
        if item['product_rate']:
            for r in item['product_rate']:
                rate = r['rate']
        else:
            rate = 0
        bottom_sheet.rate = str(rate)
        bottom_sheet.avg_rate = '0'
        bottom_sheet.image = 'images/'+item['imagen']
        bottom_sheet.price = str(item['precio'])
        bottom_sheet.quantity = ''
        bottom_sheet.ocultar = '1'
        bottom_sheet.item = item
        try:
            # do something with doc['properties.color'], e.g.:
            average_rating = item['average_rating']
        except KeyError:
            average_rating = 0
        bottom_sheet.average_rating = str(average_rating)
        #self.value = int(quantity)
        bottom_sheet.name = item['descripcion']
        self.custom_sheet = MDCustomBottomSheet(screen=bottom_sheet)
        #select el rate activo
        if rate == 1:
            bottom_sheet.ids.check1.active = True
        if rate == 2:
            bottom_sheet.ids.check2.active = True
        if rate == 3:
            bottom_sheet.ids.check3.active = True
        if rate == 4:
            bottom_sheet.ids.check4.active = True
        if rate == 5:
            bottom_sheet.ids.check5.active = True

        self.custom_sheet.open()

    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        Clock.schedule_once(self.create_list)
    """   
    """
    def create_list(self, *args):   
        #Create an object of GridFs for the above database.
        gfs = gridfs.GridFS(dbname)

        #find productos
        collection_name = dbname["producto"]
        productos = collection_name.find()
        #loop productos
        for item in productos:
            if item != None:
                imagen_id = gfs.get(item['imagen_id'])
                data = io.BytesIO(imagen_id.read())
                imagen  = CoreImage(data, ext="png").texture
                
                #widget = Image(source = 'cartt.png')
                #widget.texture = imagen
                
                self.ids.container.add_widget(OneLineAvatarListItem(
                    ImageLeftWidget(source=imagen),
                    text=item['descripcion']
                    )
                )
        """
###
#Tab de ordenes en ConsultaOrdenScreeen
class Header(BoxLayout):
    text = StringProperty()

class Cell(BoxLayout):
    text = StringProperty()

class Accion(BoxLayout):
    trash = ObjectProperty()
    pencil = ObjectProperty()
    item = ObjectProperty()
    indice = NumericProperty()

class OrdenTab(BoxLayout, MDTabsBase):
    
    def __init__(self, **kwargs):
        super(OrdenTab, self).__init__(**kwargs)

        self.check = False
        self.cols = NumericProperty(1)
        self.orden_content = []
        self.thead = ListProperty()
        self.tbody = ListProperty()
        self.color = [128, 0, 2, 0.8]
        self.thead = ["Nombre","Cant","Precio","Acción"]
        Clock.schedule_once(self.create_header)
    #construye header
    def create_header(self, *args):
        self.ids.header.cols = len(self.thead)
        self.ids.body.cols = len(self.thead)

        for i in self.thead:
            head = Header(text=i)
            self.ids['header'].add_widget(head)
    #Localiza item
    def searchsingle(self, item):
        
        existe_item = False
        
        for i in self.orden_content:
            if i['id'] == item['_id']['item_id']:
                existe_item = True
                break

        return existe_item

    #Agregar item a la lista de ordenes
    def addsingle(self, item, cantidad):
        if cantidad:
            #prepara view
            self.ids['header'].clear_widgets()
            self.ids['body'].clear_widgets()
            #agrega item
            if len(item["descripcion"]) > 20:
                descripcion = item["descripcion"][0:20]
            else:
                descripcion = item["descripcion"]

            self.orden_content.append({"id": item["_id"]["item_id"], "descripcion": descripcion.title(), "cantidad": cantidad, "precio": item["precio"]})

            """
            for i in self.orden_content:
                self.thead =[]
                for j in i.keys():
                    self.thead.append(j)
            """
            #construye view:
            #self.thead=["ITEM","QUANTITY","UNIT PRICE","TAX"]
            self.ids['header'].cols = len(self.thead)
            self.ids['body'].cols = len(self.thead)
            #header
            for i in self.thead:
                head = Header(text=i)
                self.ids['header'].add_widget(head)
            #contendo
            cantidad = 0
            importe = 0
            for i in self.orden_content:
                for j in i.keys():
                    if j == 'id':#No considerar
                        continue
                    body = Cell(text=str(i[j]))
                    if j == 'cantidad':
                        cantidad += float(str(i[j]))
                        importe += float(str(i[j])) * float(str(i['precio']))
                    if j != 'precio':
                        self.ids['body'].add_widget(body)
                    else:
                        self.ids['body'].add_widget(body)
                        accion = Accion(pencil='pencil', trash='trash-can', item=i, indice=self.orden_content.index(i))
                        self.ids['body'].add_widget(accion)
            
            self.ids.text_articulo.text = str(len(self.orden_content))+' Art.'
            self.ids.text_cantidad.text = str(cantidad) + ' B'
            self.ids.text_importe.text = 'Total ' + '{0:.2f}'.format(importe)

    #Actualiza cantidad de item
    def updatesingle(self, item, cantidad):
        #localiza item updated y actualizalo
        if cantidad:
            for i in self.orden_content:
                if i['id'] == item['id']:
                    self.orden_content[self.orden_content.index(i)]['cantidad'] = cantidad
                    break
            #Construye la view actulizada
            cantidad = 0
            importe = 0
            self.ids['body'].clear_widgets()
            self.ids['body'].cols = len(self.thead)
            for i in self.orden_content:
                for j in i.keys():
                    if j == 'id':#No considerar
                        continue
                    body = Cell(text=str(i[j]))
                    if j == 'cantidad':
                        cantidad += float(str(i[j]))
                        importe += float(str(i[j])) * float(str(i['precio']))
                    if j != 'precio':
                        self.ids['body'].add_widget(body)
                    else:
                        self.ids['body'].add_widget(body)
                        accion = Accion(pencil='pencil', trash='trash-can', item=i, indice=self.orden_content.index(i))
                        self.ids['body'].add_widget(accion)

            self.ids.text_articulo.text = str(len(self.orden_content))+' Art.'
            self.ids.text_cantidad.text = str(cantidad) + ' B'
            self.ids.text_importe.text = 'Total ' + '{0:.2f}'.format(importe)

    #Remueve item de la lista de ordeenes
    def removesingle(self, item):

        self.ids['body'].clear_widgets()
        self.ids['body'].cols = len(self.thead)

        # using del + loop 
        # to delete dictionary in list
        for i in range(len(self.orden_content)):
            if self.orden_content[i]['id'] == item['id']:
                del self.orden_content[i]
                break
        #Construir contenido del body
        cantidad = 0
        importe = 0
        for i in self.orden_content:
            for j in i.keys():
                if j == 'id':#No considerar
                        continue
                body = Cell(text=str(i[j]))
                if j == 'cantidad':
                    cantidad += float(str(i[j]))
                    importe += float(str(i[j])) * float(str(i['precio']))
                if j != 'precio':
                    self.ids['body'].add_widget(body)
                else:
                    self.ids['body'].add_widget(body)
                    accion = Accion(pencil='pencil', trash='trash-can', item=i)
                    self.ids['body'].add_widget(accion)

        self.ids.text_articulo.text = str(len(self.orden_content))+' Art.'
        self.ids.text_cantidad.text = str(cantidad) + ' B'
        self.ids.text_importe.text = 'Total ' + '{0:.2f}'.format(importe)

    #Introduce cantidad para el item, tarea = 1 updated
    def set_cantidad_emergente(self, x):
        popup = CantidadPopup(item=x, tarea=1)
        popup.open()

    #Envia datos a mongodb y notifica por mail a compañia
    def send_data(self):

        def get_order_id(id):

            self.collection_name = dbname["counter"]
            result = self.collection_name.find_one_and_update({'_id':{'company_id':company_id,'id':id,'location_id':location_id}}, {"$inc":{"secuencia":1}})
        
            return result['secuencia']
        #Enviar si hay productos
        if self.orden_content:
            #complete data dict
            order_number = get_order_id('order_id')
            
            pacific = pytz.timezone('America/Monterrey')
            aware_datetime = pacific.localize(datetime.now())

            self.collection_name = dbname["order"]
            #crear orden
            result = self.collection_name.insert_one(
                {'_id':
                        {
                            'company_id':company_id,
                            'order_id': order_number,
                            'location_id': location_id,
                            'user_id': user_id
                        },
                    'comment':self.ids.text_comment.text,
                    'producto':[],
                    'fecha_create': datetime.now()
                }
            )
            #crear lista de productos
            for item in self.orden_content:
                #result = self.collection_name.insert_one({'_id':{'order_id': order_number, 'location': location, 'user_id': user_id, 'item':item['id']}, 'cantidad':float(item['cantidad']), 'fecha_create': aware_datetime})
                result = self.collection_name.update_one(
                    {
                        '_id.company_id': company_id,
                        '_id.order_id': order_number,
                        '_id.location_id': location_id,
                        '_id.user_id': user_id
                    },
                    {
                        '$push':
                            {
                                'producto': 
                                    {
                                        'item_id': item['id'],
                                        'cantidad': float(item['cantidad']),
                                        'precio': float(item['precio'])
                                    }
                            }
                    }
                )

            # Create the container (outer) email message.
            msg = MIMEMultipart("alternative")
            msg['Subject'] = 'Notificaciones de Nueva Orden'
            msg['From'] = sender_email
            msg['To'] = ", ".join(receiver_email) #receiver_email
            msg.preamble = 'El cliente ' + user_id + ' creo la orden ' + str(order_number)

            table_content = []
            cantidad = 0
            importe = 0
            for order in self.orden_content:
                cantidad += float(order['cantidad'])
                importe += float(order['cantidad']) * float(order['precio'])
                table_content.append(f'''\
                    <tr style="background-color: aliceblue">
                        <td style="padding: 1rem">{order['id']}</td>
                        <td style="padding: 1rem">{order['descripcion']}</td>
                        <td style="padding: 1rem">{order['cantidad']}</td>
                        <td style="padding: 1rem">{order['precio']}</td>
                    </tr>
                ''')
            tc = '\n'.join(table_content)
            html = f'''\
            <html>
                <body>
                     <div class="section" style="background: rgb(241, 234, 227);">
                        <hr size="8" width="50%" color="#6CACE9"/>               
                        <h2 style="color:#20578b;text-align: center;">{company_name}</h2> 
                        <div class="row align-items-start">                                            
                            <div class="col-xs-7" style="background-color: white;width: 50%;margin: auto;padding: 10px;border-radius: 5px;">                        
                                <h2>Solicitado por {account_name} de {location_id},</h2>
                                <hr color=" #f6f6f6"/>
                                <p>Nueva Orden:</p>
                                <p>Número: {str(order_number)}</p>
                                <p>Comentario: {self.ids.text_comment.text}</p> 
                                <table style="margin: 3px">
                                    <caption>Ordenes por entregar</caption>
                                    <tr style="background-color: #c3a97d">
                                        <th style="color: white">Id</th>
                                        <th style="color: white">Descripción</th>
                                        <th style="color: white">Cantidad</th>
                                        <th style="color: white">Precio</th>
                                    </tr>
                                    {tc}
                                <tfoot>
                                </tfoot>
                                    <tr>
                                        <th>Totales</th>
                                        <td>{str(len(self.orden_content))} Articulos</td>
                                        <td>{str(cantidad)}</td>
                                        <td>{'{0:.2f}'.format(importe)}</td>
                                    </tr>
                                </table>
                                <p>¡Gracias!</p>                      
                            </div>
                            <br>
                            <p style="width: 50%;margin: auto;padding: 10px;"><small>&#169; 2022 {company_name}</small></p>                
                        </div>
                    </div>
                </body>
            </html>
            '''
            part = MIMEText(html, "html")
            msg.attach(part)

            # Send the email via our own SMTP server.
            send = smtplib.SMTP(server, port)
            send.ehlo()
            send.starttls()
            send.login(sender_email, password)
            #Adding a newline before the body text fixes the missing message body
            send.sendmail(sender_email,receiver_email,msg.as_string())
            send.quit()

            self.ids['body'].clear_widgets()
            self.orden_content = []
            self.ids.text_comment.text = ''
            self.ids.text_articulo.text = ''
            self.ids.text_cantidad.text = ''
            self.ids.text_importe.text = ''
            toast('Tu número de orden es ' + str(order_number))
###
#Screen cuenta user
class IconListItem(OneLineIconListItem):
    icon = StringProperty()

class AccionAccount(BoxLayout):
    trash = ObjectProperty()
    pencil = ObjectProperty()
    item = ObjectProperty()
    indice = NumericProperty()

class CuentaUserScreen(BoxLayout):

    def __init__(self, **kwargs):
        super(CuentaUserScreen, self).__init__(**kwargs)

        self.check = False
        self.cols = NumericProperty(1)
        self.account_content = []
        self.thead = ListProperty()
        self.tbody = ListProperty()
        self.color = [128, 0, 2, 0.8]
        self.thead = ["Usurio","Ubicación","Categoria","Acción"]
        #find account user
        self.collection_name = dbname["usuario"]
        self.cuenta_user = self.collection_name.find(
            {
                '_id.company_id': company_id,
                '_id.user_id': {'$ne' : 'sumgr'}
            }
        )
        self.total_count = self.collection_name.count_documents({})
        Clock.schedule_once(self.create_header)
    #construye header
    def create_header(self, *args):
        self.ids.header.cols = len(self.thead)
        self.ids.body.cols = len(self.thead)
        #Llena dropdownitem location
        self.menu_items_loc = [
            {
                "viewclass": "IconListItem",
                "icon": "git",
                "text": f"{i}",
                "height": dp(56),
                "on_release": lambda x=f"{i}": self.set_item_location(x),
            } for i in ['cdmxA','cdmxB','cdmx','acap','tmps']
        ]
        self.menu_location = MDDropdownMenu(
            caller=self.ids.dropdown_location,
            items=self.menu_items_loc,
            position="center",
            width_mult=4,
        )
        self.menu_location.bind()

        #Llena dropdownitem categoria
        self.menu_items_cat = [
            {
                "viewclass": "IconListItem",
                "icon": "git",
                "text": f"{i}",
                "height": dp(56),
                "on_release": lambda x=f"{i}": self.set_item_categoria(x),
            } for i in ['local','socio']
        ]
        self.menu_categoria = MDDropdownMenu(
            caller=self.ids.dropdown_categoria,
            items=self.menu_items_cat,
            position="center",
            width_mult=4,
        )
        self.menu_categoria.bind()

        #Llena dropdownitem manager
        self.menu_items_man = [
            {
                "viewclass": "IconListItem",
                "icon": "git",
                "text": f"{i}",
                "height": dp(56),
                "on_release": lambda x=f"{i}": self.set_item_manager(x),
            } for i in ['No','Si']
        ]
        self.menu_manager = MDDropdownMenu(
            caller=self.ids.dropdown_manager,
            items=self.menu_items_man,
            position="center",
            width_mult=4,
        )
        self.menu_manager.bind()

        #establece titulos del head
        for i in self.thead:
            head = Header(text=i)
            self.ids['header'].add_widget(head)

    #establece nuevo item de location
    def set_item_location(self, text_item):
        self.ids.dropdown_location.set_item(text_item)
        self.menu_location.dismiss()

    #establece nuevo item de categoria
    def set_item_categoria(self, text_item):
        self.ids.dropdown_categoria.set_item(text_item)
        self.menu_categoria.dismiss()

    #establece nuevo item de manager
    def set_item_manager(self, text_item):
        self.ids.dropdown_manager.set_item(text_item)
        self.menu_manager.dismiss()

    #Check password
    def check_password(self):

        if self.ids.text_password.text != self.ids.text_password2.text:
            self.ids.label_password.text = 'Password no coincide, verifique'
            return False
        else:
            self.ids.label_password.text = ''
            return True

    #Recupera account
    def get_data(self):

        #prepara view
        self.account_content = []
        self.ids['body'].clear_widgets()
        self.ids.text_name.text = ''
        self.ids.text_email.text = ''
        self.ids.text_id.text = ''
        self.ids.text_user.text = ''
        self.ids.text_password.text = ''
        self.ids.text_password2.text = ''

        #agrega account
        self.cuenta_user.rewind()
        
        for account in self.cuenta_user:
            self.account_content.append({"usuario": account["_id"]['user_id'], "location": account["location"], "categoria": account["categoria"]})

        #construye view:
        self.ids['body'].cols = len(self.thead)

        #contendo
        for i in self.account_content:
            for j in i.keys():
                body = Cell(text=str(i[j]))
                if j != 'categoria':
                    self.ids['body'].add_widget(body)
                else:
                    self.ids['body'].add_widget(body)
                    accion = AccionAccount(pencil='pencil', trash='trash-can', item=i, indice=self.account_content.index(i))
                    self.ids['body'].add_widget(accion)
        
        #switch MDBottomNavigationItem user
        self.ids.bottom_nav_user.switch_tab('screen 1')

        #Set readonly True
        self.ids.text_user.readonly = False

    #Display account de user selected
    def set_cuenta(self, item):
        #localiza item updated y actualizalo
        #rewind cursor
        self.cuenta_user.rewind()

        for account in self.cuenta_user:
            if account['_id']['user_id'] == item['usuario']:
                self.ids.text_name.text = account['nombre']
                self.ids.dropdown_location.text = account['location']
                self.ids.dropdown_location.current_item = account['location']
                self.ids.text_email.text = account['email']
                self.ids.dropdown_categoria.text = account['categoria']
                self.ids.dropdown_categoria.current_item = account['categoria']
                self.ids.text_id.text = account['id']
                self.ids.dropdown_manager.text = account['manager']
                self.ids.dropdown_manager.current_item = account['manager']
                self.ids.text_user.text = account['_id']['user_id']
                self.ids.text_password.text = account['password']
                self.ids.text_password2.text = account['password']
                #Set readonly True
                self.ids.text_user.readonly = True
                break
        
        #switch MDBottomNavigationItem user
        self.ids.bottom_nav_user.switch_tab('screen 1')

    #Remueve item de la lista de account user
    def remove_cuenta(self, item):

        self.ids['body'].clear_widgets()
        self.ids['body'].cols = len(self.thead)

        # using del + loop 
        # to delete dictionary in list
        for i in range(len(self.account_content)):
            if self.account_content[i]['usuario'] == item['usuario']:
                #delete document mongodb
                result = self.collection_name.delete_one(
                    {
                        '_id': 
                            {
                                'company_id': company_id,
                                'user_id': item['usuario']
                            }
                    }
                )
                if result.deleted_count > 0:
                    del self.account_content[i]
                    toast('La cuenta de ' + item['usuario'] + ' fue eliminada')

                break
        #Construir contenido del body
        for i in self.account_content:
            for j in i.keys():
                body = Cell(text=str(i[j]))
                if j != 'categoria':
                    self.ids['body'].add_widget(body)
                else:
                    self.ids['body'].add_widget(body)
                    accion = AccionAccount(pencil='pencil', trash='trash-can', item=i)
                    self.ids['body'].add_widget(accion)
    
    #Envia datos a mongodb y notifica por mail a user
    def send_data(self):
        
        #Comprobar existencia de todos los datos
        if self.ids.text_name.text and self.ids.text_email.text and self.ids.text_id.text and self.ids.text_user.text and self.ids.text_password.text:
            #Valid location, categoria, simanager
            if self.ids.dropdown_location.current_item == '':
                location = 'cdmxA'
            else:
                location = self.ids.dropdown_location.current_item

            if self.ids.dropdown_categoria.current_item == '':
                categoria = 'local'
            else:
                categoria = self.ids.dropdown_categoria.current_item

            if self.ids.dropdown_manager.current_item == '':
                manager = 'No'
            else:
                manager = self.ids.dropdown_manager.current_item

            pacific = pytz.timezone('America/Monterrey')
            aware_datetime = pacific.localize(datetime.now())
            
            self.collection_name = dbname["usuario"]
            #crear account
            result = self.collection_name.update_one(
                {
                    '_id': 
                        {
                            'company_id': company_id,
                            'user_id': self.ids.text_user.text
                        }
                },
                {
                    '$set':{
                        'nombre':self.ids.text_name.text, 
                        'location': location,
                        'email': self.ids.text_email.text,
                        'categoria': categoria,
                        'password': self.ids.text_password.text,
                        'id': self.ids.text_id.text,
                        'manager': manager,
                        'fecha_update': datetime.now()
                    },
                    '$setOnInsert':{
                        '_id':
                            {
                                'company_id': company_id,
                                'user_id': self.ids.text_user.text
                            },
                        'fecha_create': datetime.now()
                    }
                },
                upsert=True
            )
            #append mail user
            receiver_email.append(self.ids.text_email.text)

            # Create the container (outer) email message.
            msg = MIMEMultipart("alternative")
            msg['Subject'] = 'Notificaciones de Cuenta en App Gestión Ordenes'
            msg['From'] = sender_email
            msg['To'] = ", ".join(receiver_email) #receiver_email
            msg.preamble = 'El usuario ' + self.ids.text_name.text + ' creo la cuenta ' + self.ids.text_user.text
            html = """\
            <html>
                <body>
                    <div class="section" style="background: rgb(241, 234, 227);">
                        <hr size="8" width="50%" color="#6CACE9"/>               
                        <h2 style="color:#20578b;text-align: center;">"""+company_name+"""</h2>      
                        <div class="row align-items-start">                                            
                            <div class="col-xs-7" style="background-color: white;width: 50%;margin: auto;padding: 10px;border-radius: 5px;">                        
                                    <h2>Hola """+self.ids.text_name.text+""",</h2>
                                    <hr color=" #f6f6f6"/>
                                    <p>Tus datos de acceso a la App son:</p>
                                    <p>Usuario:  """+self.ids.text_user.text+"""</p>
                                    <p>Password: """+self.ids.text_password.text+"""</p>
                                    <p>¡Gracias!</p>                      
                            </div>
                            <br>
                            <p style="width: 50%;margin: auto;padding: 10px;"><small>&#169; 2022 """+company_name+"""</small></p>                
                        </div>
                    </div>
                </body>
            </html>
            """
            part = MIMEText(html, "html")
            msg.attach(part)

            # Send the email via our own SMTP server.
            send = smtplib.SMTP(server, port)
            send.ehlo()
            send.starttls()
            send.login(sender_email, password)
            #Adding a newline before the body text fixes the missing message body
            send.sendmail(sender_email,receiver_email,msg.as_string())
            send.quit()

            #self.ids['body'].clear_widgets()
            #self.account_content = []
            
            self.ids.text_email.text = ''
            self.ids.text_id.text = ''
            self.ids.text_password.text = ''
            self.ids.text_password2.text = ''

            #agrega a la lista
            self.account_content.append({"usuario": self.ids.text_user.text, "location": self.ids.dropdown_location.text, "categoria": self.ids.dropdown_categoria.text})

            toast('La cuenta de ' + self.ids.text_name.text + ' se envio')

            self.ids.text_user.text = ''
            self.ids.text_name.text = ''

        else:
            toast('Existen datos obligatorios que No se definierón verifique')

    # Click OK range
    def on_save(self, instance, value, date_range):
        
        #Establece rango de fecha
        self.ids.date_label.text = f'{date_range[0].strftime("%d/%m/%Y")} - {date_range[-1].strftime("%d/%m/%Y")}'
        
        #prepara view
        self.ids['body'].clear_widgets()
        #construye view:
        self.ids['body'].cols = len(self.thead)
        self.account_content = []
        
        self.cuenta_user = self.collection_name.find(
                {
                    '_id.company_id': company_id,
                    '_id.user_id': {'$ne' : 'sumgr'}, 
                    'fecha_create': 
                        {
                            '$gte': datetime(date_range[0].year, date_range[0].month, date_range[0].day, 0, 0, 0), 
                            '$lt': datetime(date_range[-1].year, date_range[-1].month, date_range[-1].day, 23, 59, 59)
                        }
                }
            ).sort([('fecha_create', 1), ('_id', 1)])
        
        #agrega account
        for account in self.cuenta_user:
            self.account_content.append({"usuario": account["_id"]['user_id'], "location": account["location"], "categoria": account["categoria"]})

        #contendo
        for i in self.account_content:
            for j in i.keys():
                body = Cell(text=str(i[j]))
                if j != 'categoria':
                    self.ids['body'].add_widget(body)
                else:
                    self.ids['body'].add_widget(body)
                    accion = AccionAccount(pencil='pencil', trash='trash-can', item=i, indice=self.account_content.index(i))
                    self.ids['body'].add_widget(accion)

    # Click Cancel range
    def on_cancel(self, instance, value):
        self.ids.date_label.text = "You Clicked Cancel"

    #Display datepicker
    def show_date_picker(self):
        #date_dialog = MDDatePicker(year=2000, month=2, day=14)
        date_dialog = MDDatePicker(mode="range")
        date_dialog.bind(on_save=self.on_save, on_cancel=self.on_cancel)
        date_dialog.open()

###
#Transfer Screen
class TransferDataScreen(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        #Prepared file manager
        Window.bind(on_keyboard=self.events)
        self.manager_open = False
        self.file_manager = MDFileManager(
            exit_manager=self.exit_manager, select_path=self.select_path
        )
        self.collection_name = dbname["producto"]

    #File manager
    def file_manager_open(self):
        self.file_manager.show(os.path.expanduser("~"))  # output manager to the screen
        self.manager_open = True

    def select_path(self, path: str):
        '''
        It will be called when you click on the file name
        or the catalog selection button.

        :param path: path to the selected directory or file;
        '''
        self.ids.label_data.text = path

        self.exit_manager()

    def exit_manager(self, *args):
        '''Called when the user reaches the root of the directory tree.'''

        self.manager_open = False
        self.file_manager.close()

    def events(self, instance, keyboard, keycode, text, modifiers):
        '''Called when buttons are pressed on the mobile device.'''

        if keyboard in (1001, 27):
            if self.manager_open:
                self.file_manager.back()
        return True
    
    def transfer_data(self):

        if self.ids.label_data.text:
            df = pd.read_csv(self.ids.label_data.text,header=None)
            
            for i in range(len(df)):
                #Saltamos encabezados
                if i == 0:
                    continue
                #Check item_id
                if df.values[i][0]:
                    #Check conversión a float
                    try:
                        precio = float(df.values[i][4])
                    except ValueError:
                        precio = 0
                    #Update mongodb
                    result = self.collection_name.update_one(
                        {
                            '_id': 
                                {
                                    'company_id': company_id,
                                    'item_id': df.values[i][0]
                                }
                        },
                        {
                            '$set':{
                                'descripcion':df.values[i][1], 
                                'categoria': df.values[i][2],
                                'clase': df.values[i][3],
                                'precio': precio,
                                'imagen': df.values[i][5],
                                'fecha_update': datetime.now()
                            },
                            '$setOnInsert':{
                                '_id': 
                                    {
                                        'company_id': company_id,
                                        'item_id': df.values[i][0]
                                    },
                                'fecha_create': datetime.now()
                            }
                        },
                        upsert=True
                    )
            

            self.ids.label_data.text = 'Productos actualizados '+ str(len(df)-1)
            toast('Transfer finalizada')
        else:
            toast('Seleecione un archivo Csv')

###
#Login Screen
class LoginScreen(BoxLayout):
    text = StringProperty()
    hint_text = StringProperty()

    def login_data(self):
        #Indicamos las variables globales
        #para poder modificarlas
        global user_id
        global location_id
        global categoria_id
        global is_manager
        global account_name
        global account_id

        user_id = self.ids.text_usuario.text
        password = self.ids.text_password.text
        estado = False
        data = None
        try:
            
            # Create a new collection
            collection_name = dbname["usuario"]
            
            data = collection_name.find_one(
                {
                    '$and':[{'_id':{'company_id':company_id,'user_id':user_id}},{'password':password}]
                }
            )
            
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
            #Data user
            location_id = data['location']
            account_name = data['nombre']
            account_id = data['_id']['user_id']
            categoria_id = data['categoria']
            if data['manager'] == 'Si':
                is_manager = True
            else:
                is_manager = False
        else:
            self.ids.label_login.text = mensaje
        
        return estado
###
#App principal
class NavigationApp(MDApp):

    def build(self):
        self.theme_cls.primary_palette = "Teal"
        self.title = "Customer Shopping"
        return Menu()

    def on_start(self):
        global company_name
        #global imagen_id
        global server
        global port
        global sender_email
        global receiver_email
        global password

        collection_name = dbname["company"]
        total_count = collection_name.count_documents({})

        #No existe la colección: crear user sumgr
        if total_count == 0:
            #crear company
            #Create an object of GridFs for the above database.
            #gfs = gridfs.GridFS(dbname)

            #response = requests.get('https://github.com/JavierMauricio/PartnerOrders/blob/main/images/clip.png?raw=true')

            #Now store/put the image via GridFs object.
            #imagen_id = gfs.put(response.content, content_type='Imagen', filename='Logo app')
            
            result = collection_name.insert_one(
                {
                    '_id': 1,
                    'nombre':'Nutrición Mejorada para Animales de Compañia',
                    'servermail': {
                        'server': 'smtp.office365.com',
                        'port': 587,
                        'sender_email': "ventassofting@hotmail.com",
                        'receiver_email': ['softingjl@hotmail.com'],
                        'password': "9Templarios"
                    },
                    'fecha_create': datetime.now()
                }
            )
            #crear account
            collection_name = dbname["usuario"]
            total_count = collection_name.count_documents({})
            result = collection_name.insert_one(
                {
                    '_id': {'company_id': 1,'user_id':'sumgr'},
                    'nombre':'Super manager', 
                    'location': 'cdmx',
                    'email': 'softingjl@hotmail.com',
                    'id': 'na',
                    'manager': 'Si',
                    'categoria': 'local',
                    'password': 'F03ja!',
                    'fecha_create': datetime.now()
                }
            )
            #crear counter
            collection_name = dbname["counter"]
            result = collection_name.insert_one(
                {
                    '_id': {'company_id': 1,'id': 'order_id','location_id':'cdmx'},
                    'secuencia': 0,
                    'user_id':'sumgr',
                    'fecha_create': datetime.now(),
                }
            )
            result = collection_name.insert_one(
                {
                    '_id': {'company_id': 1,'id': 'order_id','location_id':'acap'},
                    'secuencia': 0,
                    'user_id':'sumgr',
                    'fecha_create': datetime.now(),
                }
            )
            result = collection_name.insert_one(
                {
                    '_id': {'company_id': 1,'id': 'order_id','location_id':'tmps'},
                    'secuencia': 0,
                    'user_id':'sumgr',
                    'fecha_create': datetime.now(),
                }
            )
        else:
            #Get data company
            company = collection_name.find_one(
                {
                    '_id': company_id
                }
            )
            company_name = company['nombre']
            #imagen_id = company['imagen_id']
            server =  company['servermail']['server']
            port = company['servermail']['port']
            sender_email = company['servermail']['sender_email']
            receiver_email = company['servermail']['receiver_email']
            password = company['servermail']['password']
        
        #Login user
        self.root.ids.main_screen_manager.current = "login_screen"

        #if user_id:
        #    self.root.ids.main_screen_manager.current = "dashboard_screen"
        #else:
        #    print('no logeado')

if __name__ == '__main__':
    NavigationApp().run()
