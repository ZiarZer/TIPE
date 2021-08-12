from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivymd.uix.label import MDLabel

class ScrollableLabel(ScrollView):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.layout = GridLayout(cols = 1, size_hint_y = None)
        self.add_widget(self.layout)

        self.historique_chat = MDLabel(size_hint_y = None, markup = True)

        self.layout.add_widget(self.historique_chat)

    def update_chat(self, message):
        self.historique_chat.text += '\n' + message

        self.layout.height = self.historique_chat.texture_size[1] + 15
        self.historique_chat.height = self.historique_chat.texture_size[1]
        self.historique_chat.text_size = (self.historique_chat.width*0.98, None)