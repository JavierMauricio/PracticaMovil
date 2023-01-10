from kivy.clock import Clock
from kivy.core.window import Window
from kivy.lang.builder import Builder
from kivy.uix.image import Image
from kivy.graphics import PushMatrix, PopMatrix, Rotate
from kivymd.app import MDApp
from kivymd.uix.filemanager import MDFileManager
from kivymd.toast import toast
from kivymd.uix.swiper import MDSwiperItem
import os


class PyGallery(MDApp):

    def __init__(self, **kwargs):  # todo: OK
        super(PyGallery, self).__init__(**kwargs)
        Window.bind(on_keyboard=self.events)
        self.manager_open = False
        self.file_manager = MDFileManager(
            exit_manager=self.exit_manager,
            select_path=self.select_path,
            # preview=True,
        )
        self.theme_cls.primary_palette = 'Blue'
        self.theme_cls.theme_style = "Light"
        self.cont = 0
        self.global_path = ''
        self.files = []
        self.bucle = Clock.schedule_interval(self.on_play, 3)

    def file_manager_open(self):  # todo: OK
        self.file_manager.show('/')  # output manager to the screen
        self.manager_open = True

    def select_path(self, path):  # todo: OK
        self.exit_manager()
        self.global_path = path
        self.add_photos(self.global_path)
        toast(self.global_path)

    def exit_manager(self, *args):  # todo: OK
        self.manager_open = False
        self.file_manager.close()

    def events(self, instance, keyboard, keycode, text, modifiers):  # todo: OK
        if keyboard in (1001, 27):
            if self.manager_open:
                self.file_manager.back()
        return True

    def change_palette(self):  # todo: OK
        palette = ['Red', 'Pink', 'Purple', 'DeepPurple', 'Indigo', 'Blue', 'LightBlue', 'Cyan', 'Teal', 'Green',
                   'LightGreen', 'Lime', 'Yellow', 'Amber', 'Orange', 'DeepOrange', 'Brown', 'Gray', 'BlueGray']
        self.theme_cls.primary_palette = palette[self.cont]
        if self.cont < 18:
            self.cont += 1
        else:
            self.cont = 0

    def change_theme_style(self):  # todo: OK
        if self.theme_cls.theme_style == 'Light':
            self.theme_cls.theme_style = "Dark"
        else:
            self.theme_cls.theme_style = "Light"

    def move_right(self):  # todo: OK
        if len(self.root.ids.swiper.get_items()) > 1:
            self.root.ids.swiper.swipe_right()
        else:
            toast('No hay imágenes suficientes')

    def move_left(self):  # todo: OK
        if len(self.root.ids.swiper.get_items()) > 1:
            self.root.ids.swiper.swipe_left()
        else:
            toast('No hay imágenes suficientes')

    def on_play(self, *largs):  # todo: OK
        cant = len(self.root.ids.swiper.get_items())
        current = self.root.ids.swiper.get_current_index()
        if cant == 1:
            toast('No hay imágenes suficientes')
            self.stop()
        if cant > 1:
            self.root.ids.bar.icon = 'stop'
            current += 1
            if current < cant:
                self.root.ids.swiper.set_current(current)
            else:
                self.stop()
        if cant == 0:
            toast('Encuentre las imágenes ha mostrar')
            self.stop()

    def play(self):  # todo: OK
        if self.root.ids.bar.icon == 'play':
            self.bucle()
        else:
            self.stop()

    def stop(self, *largs):  # todo: OK
        self.root.ids.bar.icon = 'play'
        self.bucle.cancel()

    def zoom(self, param):  # todo: OK
        if len(self.root.ids.swiper.get_items()) >= 1:
            current_size_hint = self.root.ids.swiper.get_current_item().children[0].size_hint[0]
            if param == "minus":
                if current_size_hint > 0.20:
                    current_size_hint -= 0.10
                else:
                    toast('Tamaño mínimo!!!')
            else:
                if current_size_hint < 1:
                    current_size_hint += 0.10
                else:
                    toast('Tamaño máximo!!!')
            self.root.ids.swiper.get_current_item().children[0].size_hint = (current_size_hint, current_size_hint)
        else:
            toast('No hay existencia de imagen')

    def rotate(self, param):  # todo: OK
        if len(self.root.ids.swiper.get_items()) >= 1:
            img = self.root.ids.swiper.get_current_item().children[0]
            if param == "left":
                angle = 90
            else:
                angle = -90
            with img.canvas.before:
                PushMatrix()
                rotate = Rotate(origin=img.center,angle=angle, axis = (0, 0, 1))
                img.bind(center=lambda _, value: setattr(rotate, "origin", value))
            with img.canvas.after:
                PopMatrix()
        else:
                toast('No hay existencia de imagen')

    def add_photos(self, path):  # todo: OK
        formats = ['jpg', 'png', 'JPG', 'PNG', 'gif', 'GIF', 'tif', 'TIF', 'svg', 'SVG', 'bmp', 'BMP', 'pcx', 'PCX',
                   'tga', 'TGA']
        if self.global_path[-4] != '.':
            with os.scandir(self.global_path) as self.files:
                self.files = [f.name for f in self.files if f.is_file() and f.name[-3:] in formats]
            self.show_photos()
        else:
            self.show_photos()

    def show_photos(self):  # todo: OK
        # self.root.ids.swiper.clear_widgets()
        if len(self.files) == 0:
            item = MDSwiperItem()
            item.add_widget(Image(source=self.global_path, size_hint=(1, 1), pos_hint={'center_x': .5, 'center_y': .5}))
            self.root.ids.swiper.add_widget(item)
        else:
            for i in self.files:
                item = MDSwiperItem()
                item.add_widget(Image(source=self.global_path+'/'+i, size_hint=(1, 1),
                                      pos_hint={'center_x': .5, 'center_y': .5}))
                self.root.ids.swiper.add_widget(item)

    def build(self):  # todo: OK
        return Builder.load_file("""PyGallery.kv""")

if __name__ == "__main__":
    PyGallery().run()
