import pygame
import pygame.camera
import socket

PORT = 14243


class NxtCam(object):

    def __init__(self):
        pygame.camera.init()
        self.camlist = pygame.camera.list_cameras()
        self.cam_path = self.camlist[0]
        self.cam = pygame.camera.Camera(self.cam_path, (640, 480), "RGB")
        self.cam.start()
        self.img = pygame.Surface((640, 480))
        print('Cam initialized')

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.bind(("", PORT))
        self.sock.listen(10)
        print('Socket bound. Listening for clients on %s' % PORT)

    def run(self):
        while True:
            connection, address = self.sock.accept()
            print('CONNECTED')
            self.cam.get_image(self.img)
            data = pygame.image.tostring(self.img, "RGB")
            connection.sendall(data)
            connection.close()


if __name__ == '__main__':
    cam = NxtCam()
    cam.run()
