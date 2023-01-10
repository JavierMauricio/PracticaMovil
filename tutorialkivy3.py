from kivy.app import App
from kivy.uix.scatter import Scatter
from kivy.uix.label import Label
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.textinput import TextInput
from kivy.uix.boxlayout import BoxLayout
from random import random

class ScatterTextWidget(BoxLayout):
    def change_label_colour(self, *args):
        colour = [random() for i in range(3)] + [1]
        label = self.ids['my_label']
        label.color = colour

        label1 = self.ids.label1
        label2 = self.ids.label2

        label1.color = colour
        label2.color = colour       


class TutorialKivy3App(App):

    def build(self):       
        return ScatterTextWidget()

if __name__ == '__main__':
    TutorialKivy3App().run()