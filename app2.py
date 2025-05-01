import cv2
import torch
import numpy as np
from kivy.app import App
from kivy.uix.image import Image
from kivy.graphics.texture import Texture
from kivy.clock import Clock

class ObjectDetectionApp(App):
    def build(self):
        self.img_widget = Image()
        self.model = torch.hub.load('ultralytics/yolov5', 'yolov5s', pretrained=True)
        self.capture = cv2.VideoCapture(0)
        Clock.schedule_interval(self.update, 1.0 / 30.0)
        return self.img_widget

    def update(self, dt):
        ret, frame = self.capture.read()
        if not ret:
            return

        # Run YOLOv5 object detection
        results = self.model(frame)

        # Render results on the frame
        result_frame = np.squeeze(results.render())

        # Convert color for Kivy
        buf = cv2.flip(result_frame, 0).tobytes()
        texture = Texture.create(size=(result_frame.shape[1], result_frame.shape[0]), colorfmt='bgr')
        texture.blit_buffer(buf, colorfmt='bgr', bufferfmt='ubyte')
        self.img_widget.texture = texture

    def on_stop(self):
        self.capture.release()

if __name__ == '__main__':
    ObjectDetectionApp().run()
