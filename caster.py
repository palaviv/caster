import argparse
try:
    from http.server import BaseHTTPRequestHandler, HTTPServer
except ImportError:
    from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
import threading
import socket
import os

from six import b
import pychromecast
import readchar


def get_internal_ip(dst_ip):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect((dst_ip, 0))
    return s.getsockname()[0]


class RequestHandler(BaseHTTPRequestHandler):
    content_type = "video/mp4"

    """ Handle HTTP requests for files which do not need transcoding """

    def do_GET(self):
        self.protocol_version = "HTTP/1.1"
        self.send_response(200)
        self.send_header("Content-type", self.content_type)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header("Transfer-Encoding", "chunked")
        self.end_headers()

        with open(self.path, "rb") as f:
            while True:
                data = f.read(1024)
                if len(data) == 0:
                    break

                chunk_size = "%0.2X" % len(data)
                self.wfile.write(b(chunk_size))
                self.wfile.write(b("\r\n"))
                self.wfile.write(data)
                self.wfile.write(b("\r\n"))

        self.wfile.write(b("0"))
        self.wfile.write(b("\r\n\r\n"))


class SubRequestHandler(RequestHandler):
    content_type = "text/vtt"


def handle_input(server_thread, dev, mc):
    while server_thread.is_alive():
        key = readchar.readkey()
        if key in [readchar.key.CTRL_C, "s"]:
            mc.stop()
            return
        elif key == readchar.key.SPACE:
            if mc.status.player_is_playing:
                mc.pause()
            else:
                mc.play()
        elif key == readchar.key.UP:
            dev.volume_up()
        elif key == readchar.key.DOWN:
            dev.volume_down()


def get_args():
    parser = argparse.ArgumentParser(description='Caster - cast media to chromecast')
    parser.add_argument('file', help='The file to play')
    parser.add_argument('--device', help='The chromecast device to use.'
                                         ' When not given first one found is used.',
                        default=None)
    parser.add_argument('--subtitles', help='subtitles', default=None)
    return parser.parse_args()


def main():
    args = get_args()

    file_path = args.file

    device_name = args.device

    subs = args.subtitles

    if device_name:
        dev = pychromecast.get_chromecasts_as_dict()[device_name]
    else:
        _, dev = pychromecast.get_chromecasts_as_dict().popitem()

    dev.wait()

    server_ip = get_internal_ip(dev.host)

    server = HTTPServer((server_ip, 0), RequestHandler)
    server_thread = threading.Thread(target=server.handle_request)
    server_thread.start()

    if subs:
        sub_server = HTTPServer((server_ip, 0), SubRequestHandler)
        sub_server_thread = threading.Thread(target=sub_server.handle_request)
        sub_server_thread.start()
        subtitles_url = "http://{IP}:{PORT}/{URI}".format(IP=server_ip, PORT=sub_server.server_port, URI=subs)
    else:
        subtitles_url = None

    mc = dev.media_controller

    media_url = "http://{IP}:{PORT}/{URI}".format(IP=server_ip, PORT=server.server_port, URI=file_path)
    mc.play_media(media_url, 'video/mp4', title=os.path.basename(file_path), subtitles=subtitles_url)
    mc.update_status(blocking=True)
    mc.enable_subtitle(1)

    handle_input(server_thread, dev, mc)

    server_thread.join()
    server.server_close()

    if subs:
        sub_server_thread.join()
        sub_server.close()

if __name__ == "__main__":
    main()