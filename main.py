import cv2
import numpy as np
import requests
import socket
import struct
import threading
import time
import json

# ----------Global Variable -------------
temp_array=np.zeros((1,76800), dtype=np.float32)

class NeuralNetwork:
    def __init__(self, size, file_location):
        self.model = cv2.ANN_MLP()
        self.model.create(np.int32(size))
        self.model.load(file_location)
    def predict(self, samples):
        ret, resp = self.model.predict(samples)
        return resp.argmax(-1)

class VideoHandling(threading.Thread):
    def __init__(self, tcp_addr, BUFFER_SIZE = 1024):
        threading.Thread.__init__(self)
        self.total_frames = 0
        self.BUFFER_SIZE = BUFFER_SIZE
        self.__state = True

        self.server_socket = socket.socket()
        self.server_socket.bind(tcp_addr)
        self.server_socket.listen(0)

        self.connection = self.server_socket.accept()[0].makefile('rb')

    def run(self):
        cv2.startWindowThread()
        cv2.namedWindow('Traffic', cv2.CV_WINDOW_AUTOSIZE)

        stream_byte = ''

        while self.__state:
            stream_byte+= self.connection.read(self.BUFFER_SIZE)
            first = stream_byte.find('\xff\xd8')
            last = stream_byte.find('\xff\xd9')
            if first != 1 and last != 1:
                jpg = stream_byte[first:last+2]
                stream_byte=stream_byte[last+2:]
                image = cv2.imdecode(np.fromstring(jpg, dtype=np.uint8), cv2.CV_LOAD_IMAGE_GRAYSCALE)
                cv2.imshow('Traffic', image)
                global temp_array
                temp_array = image.reshape(1, 76800).astype(np.float32)
                self.total_frames+=1

        cv2.destroyAllWindows()

    def stop_handling(self):
        self.__state = False

class RequestServerBluemix(threading.Thread):
    def __init__(self, url):
        threading.Thread.__init__(self)
        self.headers = {"Content-type": "application/json"}
        self.login={"username":"admin", "password":"18349275" }
        self.url = url
    def send_data(self, data):
        data = data.update(self.login)
        res = requests.post(self.url, json.dumps(data), headers=self.headers )
        return res.text

def send_request(url, data):
    headers = {"Content-type": "application/json" , 'Accept': 'text/plain'}
    login={"username":"admin", "password":"18349275" }
    data.update(login)
    res = requests.post(url, json.dumps(data), headers=headers )
    return res.text

class FileHandling(threading.Thread):
    def __init__(self,size, file_location):
        threading.Thread.__init__(self)
        self.cap = cv2.VideoCapture(file_location)
        self.cap.set(3, size[0])
        self.cap.set(4, size[1])
        self.__state = True
    def run(self):
        cv2.namedWindow("Traffic", cv2.CV_WINDOW_AUTOSIZE)
        state =True
        global temp_array
        try:
            while self.cap.isOpened() and self.__state:
                ret, frame = self.cap.read()
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                temp_array = gray.reshape(1, 76800).astype(np.float32)
                cv2.imshow("Traffic", frame)
                if cv2.waitKey(20) & 0xFF == ord('q'):
                    self.__state = False
        finally:
            self.cap.release()
            cv2.destroyAllWindows()
    def stop_handling(self):
        self.__state = False

if __name__ == "__main__":
    classifier = NeuralNetwork([76800, 64, 5], 'traffic_classifier.xml')
    #traffic_data = VideoHandling(('0.0.0.0', 6000))
    traffic_data = FileHandling((320,240), 'test.avi')
    traffic_data.setDaemon(True)
    traffic_data.start()
    while True:
        prediction = classifier.predict(temp_array)
	    #print prediction[0]
        print send_request('http://congestionmapping.mybluemix.net/data_stream', {"lat": 10.7500, "lng": 106.6667, "degree": prediction[0] + 1}
        time.sleep(5)
