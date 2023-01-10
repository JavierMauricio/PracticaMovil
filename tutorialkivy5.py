from kivy.app import App
from kivy.uix.scatter import Scatter
from kivy.uix.label import Label
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.textinput import TextInput
from kivy.uix.boxlayout import BoxLayout
from kivy.properties import ListProperty
from kivy.graphics.vertex_instructions import (Rectangle,
                                                Ellipse,
                                                Line)
from kivy.graphics.context_instructions import Color

from random import random

class ScatterTextWidget(BoxLayout):
    text_colour = ListProperty([1, 0, 0, 1])

    def __init__(self, **kwargs):
        super(ScatterTextWidget, self).__init__(**kwargs)

        with self.canvas:
            Color(0, 1, 0, 1)
            Rectangle(pos=(0, 100), size=(300, 100))
            Ellipse(pos=(0, 400), size=(300, 100))
            Line(points=[0 , 0, 500 ,600, 400, 300],
                close=True,
                width=3)

    def change_label_colour(self, *args):
        colour = [random() for i in range(3)] + [1]
        self.text_colour = colour


class TutorialKivy5App(App):

    def build(self):       
        return ScatterTextWidget()

if __name__ == '__main__':
    TutorialKivy5App().run()