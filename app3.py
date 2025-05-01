from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button

from sklearn.datasets import load_iris
from sklearn.ensemble import RandomForestClassifier
import numpy as np


class MLApp(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation='vertical', **kwargs)

        self.model = self.train_model()

        self.inputs = []
        for feature in ['Sepal Length', 'Sepal Width', 'Petal Length', 'Petal Width']:
            self.add_widget(Label(text=feature))
            input_box = TextInput(multiline=False, input_filter='float')
            self.inputs.append(input_box)
            self.add_widget(input_box)

        self.predict_button = Button(text='Predict Species')
        self.predict_button.bind(on_press=self.predict)
        self.add_widget(self.predict_button)

        self.result_label = Label(text='Result will appear here')
        self.add_widget(self.result_label)

    def train_model(self):
        iris = load_iris()
        X, y = iris.data, iris.target
        clf = RandomForestClassifier()
        clf.fit(X, y)
        self.target_names = iris.target_names
        return clf

    def predict(self, instance):
        try:
            values = [float(inp.text) for inp in self.inputs]
            prediction = self.model.predict([values])[0]
            species = self.target_names[prediction]
            self.result_label.text = f'Predicted Species: {species}'
        except ValueError:
            self.result_label.text = 'Please enter valid numbers!'


class IrisMLApp(App):
    def build(self):
        return MLApp()


if __name__ == '__main__':
    IrisMLApp().run()
