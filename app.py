import cv2
import torch
import numpy as np
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.image import Image
from kivy.uix.button import Button
from kivy.uix.spinner import Spinner
from kivy.graphics.texture import Texture
from kivy.clock import Clock
from datetime import datetime

class ObjectDetectionLayout(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation='vertical', **kwargs)

        self.model = torch.hub.load('ultralytics/yolov5', 'yolov5s', pretrained=True)
        self.capture = cv2.VideoCapture(0)
        self.filter_label = None  # No filter at start

        # Image widget
        self.img_widget = Image()
        self.add_widget(self.img_widget)

        # Bottom bar with dropdown + save
        bottom_bar = BoxLayout(size_hint_y=0.1)

        self.spinner = Spinner(
            text='All',
            values=('All', 'person', 'car', 'bottle', 'dog', 'cat', 'cell phone'),
            size_hint=(0.5, 1)
        )
        self.spinner.bind(text=self.set_filter)
        bottom_bar.add_widget(self.spinner)

        self.save_button = Button(text="Save Frame", size_hint=(0.5, 1))
        self.save_button.bind(on_press=self.save_frame)
        bottom_bar.add_widget(self.save_button)

        self.add_widget(bottom_bar)

        Clock.schedule_interval(self.update, 1.0 / 30.0)
        self.last_frame = None

    def set_filter(self, spinner, text):
        self.filter_label = None if text == 'All' else text

    def update(self, dt):
        ret, frame = self.capture.read()
        if not ret:
            return

        results = self.model(frame)
        detections = results.pandas().xyxy[0]

        # Filter detections if needed
        if self.filter_label:
            detections = detections[detections['name'] == self.filter_label]

        for _, row in detections.iterrows():
            xmin, ymin, xmax, ymax = map(int, [row['xmin'], row['ymin'], row['xmax'], row['ymax']])
            label = row['name']
            confidence = row['confidence']
            cv2.rectangle(frame, (xmin, ymin), (xmax, ymax), (255, 0, 0), 2)
            cv2.putText(frame, f'{label} {confidence:.2f}', (xmin, ymin - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)

        self.last_frame = frame.copy()  # Save the current frame

        buf = cv2.flip(frame, 0).tobytes()
        texture = Texture.create(size=(frame.shape[1], frame.shape[0]), colorfmt='bgr')
        texture.blit_buffer(buf, colorfmt='bgr', bufferfmt='ubyte')
        self.img_widget.texture = texture

    def save_frame(self, instance):
        if self.last_frame is not None:
            filename = f"frame_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
            cv2.imwrite(filename, self.last_frame)
            print(f"Frame saved as {filename}")

    def on_stop(self):
        self.capture.release()


class ObjectDetectionApp(App):
    def build(self):
        return ObjectDetectionLayout()


if __name__ == '__main__':
    ObjectDetectionApp().run()
