import argparse
try:
    from http.server import BaseHTTPRequestHandler, HTTPServer
except ImportError:
    from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
import threading
import socket
import os
from socketserver import ThreadingMixIn
import mimetypes

import pychromecast
import readchar


def get_internal_ip(dst_ip):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect((dst_ip, 0))
    return s.getsockname()[0]


mimetypes.add_type("text/vtt", ".vtt")


class RequestHandler(BaseHTTPRequestHandler):
    chunk_size = 1024

    """ Handle HTTP requests for files which do not need transcoding """

    def parse_range(self, file_size):
        start = self.headers["range"].split("=")[1].split("-")[0]
        end = file_size - 1
        return int(start), int(end)

    def do_GET(self):
        self.protocol_version = "HTTP/1.1"
        content_type = mimetypes.guess_type(self.path)

        with open(self.path, "rb") as f:
            f.seek(0, 2)
            file_size = f.tell()

            if "range" in self.headers:
                self.send_response(206)
                start_range, end_range = self.parse_range(file_size)
                self.send_header('Content-Range', 'bytes {START}-{END}/{TOTAL}'.format(
                    START=start_range, END=end_range, TOTAL=file_size))
                self.send_header('Accept-Ranges', 'bytes')
            else:
                self.send_response(200)
                start_range, end_range = 0, file_size
            self.send_header('Content-Length', end_range - start_range + 1)
            self.send_header("Content-type", content_type[0])
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()

            f.seek(start_range)

            curr = start_range

            while True:
                if curr + self.chunk_size > end_range:
                    read_size = end_range - curr
                else:
                    read_size = self.chunk_size
                curr += read_size
                data = f.read(read_size)
                self.wfile.write(data)
                if curr == end_range:
                    break

    def handle_one_request(self):
        try:
            return BaseHTTPRequestHandler.handle_one_request(self)
        except socket.error:
            pass


class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    pass


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
        elif key == readchar.key.RIGHT:
            mc.update_status(blocking=True)
            mc.seek(mc.status.current_time + 30)
        elif key == readchar.key.LEFT:
            mc.update_status(blocking=True)
            mc.seek(mc.status.current_time - 30)
        elif key == "m":
            if dev.status.volume_muted:
                dev.set_volume_muted(False)
            else:
                dev.set_volume_muted(True)


def get_args():
    parser = argparse.ArgumentParser(description='Caster - cast media to chromecast')
    parser.add_argument('file', help='The file to play')
    parser.add_argument('--device', help='The chromecast device to use.'
                                         ' When not given first one found is used.',
                        default=None)
    parser.add_argument('--subtitles', help='subtitles', default=None)
    parser.add_argument('--seek', help='media starting position in seconds', default=0)
    return parser.parse_args()


def main():
    args = get_args()

    file_path = args.file
    device_name = args.device
    subs = args.subtitles
    seek = args.seek

    if device_name:
        dev = pychromecast.get_chromecasts_as_dict()[device_name]
    else:
        _, dev = pychromecast.get_chromecasts_as_dict().popitem()

    dev.wait()

    try:
        server_ip = get_internal_ip(dev.host)
    except Exception:
        # See https://github.com/palaviv/caster/issues/1
        server_ip = "0.0.0.0"

    server = ThreadedHTTPServer((server_ip, 0), RequestHandler)
    server_thread = threading.Thread(target=server.serve_forever)
    server_thread.start()

    mc = dev.media_controller

    if subs:
        subtitles_url = "http://{IP}:{PORT}/{URI}".format(IP=server_ip, PORT=server.server_port, URI=subs)
    else:
        subtitles_url = None
    media_url = "http://{IP}:{PORT}/{URI}".format(IP=server_ip, PORT=server.server_port, URI=file_path)
    mc.play_media(media_url, 'video/mp4', title=os.path.basename(file_path), subtitles=subtitles_url,
                  current_time=seek)
    mc.update_status(blocking=True)
    mc.enable_subtitle(1)

    handle_input(server_thread, dev, mc)

    server.shutdown()
    server_thread.join()
    server.server_close()

if __name__ == "__main__":
    main()