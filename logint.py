from kivy.app import App
from kivymd.app import MDApp
from kivy.uix.screenmanager import ScreenManager, Screen

class LoginScreen(Screen):
    pass

class LogintApp(MDApp):
    title = ''
    def build(self): 
        return LoginScreen()
        
if __name__ == '__main__':
    LogintApp().run()