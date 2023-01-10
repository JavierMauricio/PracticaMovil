class ImageAndTitle(MDBoxLayout, ButtonBehavior):
    source = StringProperty()
    title = StringProperty()

class TestBox(BoxLayout):
    txt = ListProperty()
    images2 = ListProperty()
    records = ListProperty()

    def __init__(self, **kwargs):
        super(TestBox, self).__init__(**kwargs)
        self.get_cat()

    def get_cat(self):
        connection = pymysql.connect(user="*****", password="*******", database="******")
        cursor = connection.cursor()
        query1 =("SELECT service_img,servicename_ku,servicename FROM service_cat ORDER BY service_id")
        cursor.execute(query1)
        records = cursor.fetchall()
        file1 = BytesIO(records[0][0])
        img1 = PIL.Image.open(file1)
        self.images2.append(img1)
        print(type(records[0]))
        for field in records:
            tex = field[1]
            img = field[0]
            print(type(img))
            print(tex)
            self.txt.append(tex)