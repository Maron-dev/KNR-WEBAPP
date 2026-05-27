from sensor_msgs.msg import CompressedImage

latest_image_bytes = None
import threading
import time
# ROS2 imports
import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32, String, Int32

# Słownik na dane telemetryczne
status_data = {
    "altitude": 0.0,
    "speed": 0.0,
    "battery_percent": "100%",
    "battery_voltage": "0V",
    "gps_global": "0.0,0.0",
    "gps_relative": "0.0,0.0",
    "mission_time": "00:00:00",
    "flight_mode": "INIT",
    "water_temp": "--",
    "last_update": "-",
}

# ROS2 node do subskrypcji topiców
class StatusNode(Node):
    def __init__(self):
        super().__init__('status_node')
        self.create_subscription(Float32, 'altitude', self.altitude_callback, 10)
        self.create_subscription(Float32, 'speed', self.speed_callback, 10)
        self.create_subscription(Int32, 'battery_percent', self.battery_percent_callback, 10)
        self.create_subscription(Float32, 'battery_voltage', self.battery_voltage_callback, 10)
        self.create_subscription(String, 'gps_global', self.gps_global_callback, 10)
        self.create_subscription(String, 'gps_relative', self.gps_relative_callback, 10)
        self.create_subscription(String, 'mission_time', self.mission_time_callback, 10)
        self.create_subscription(String, 'flight_mode', self.flight_mode_callback, 10)
        self.create_subscription(Float32, 'water_temp', self.water_temp_callback, 10)
        self.create_subscription(CompressedImage, 'drone_image', self.image_callback, 10)

    def image_callback(self, msg):
        global latest_image_bytes
        latest_image_bytes = msg.data

    def altitude_callback(self, msg):
        print("ALTITUDE:", msg.data)
        status_data["altitude"] = round(msg.data, 1)
        status_data["last_update"] = time.strftime("%Y-%m-%d %H:%M:%S")

    def speed_callback(self, msg):
        status_data["speed"] = round(msg.data, 1)
        status_data["last_update"] = time.strftime("%Y-%m-%d %H:%M:%S")

    def battery_percent_callback(self, msg):
        status_data["battery_percent"] = f"{msg.data}%"
        status_data["last_update"] = time.strftime("%Y-%m-%d %H:%M:%S")

    def battery_voltage_callback(self, msg):
        status_data["battery_voltage"] = f"{msg.data:.2f}V"
        status_data["last_update"] = time.strftime("%Y-%m-%d %H:%M:%S")

    def gps_global_callback(self, msg):
        status_data["gps_global"] = msg.data
        status_data["last_update"] = time.strftime("%Y-%m-%d %H:%M:%S")

    def gps_relative_callback(self, msg):
        status_data["gps_relative"] = msg.data
        status_data["last_update"] = time.strftime("%Y-%m-%d %H:%M:%S")

    def mission_time_callback(self, msg):
        status_data["mission_time"] = msg.data
        status_data["last_update"] = time.strftime("%Y-%m-%d %H:%M:%S")

    def flight_mode_callback(self, msg):
        status_data["flight_mode"] = msg.data
        status_data["last_update"] = time.strftime("%Y-%m-%d %H:%M:%S")

    def water_temp_callback(self, msg):
        status_data["water_temp"] = f"{msg.data:.1f} °C"
        status_data["last_update"] = time.strftime("%Y-%m-%d %H:%M:%S")

def ros_spin():
    rclpy.init()
    node = StatusNode()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()
import argparse
import asyncio
import json
import logging
import os
import platform
import ssl
from typing import Optional

from aiohttp import web
from aiortc import (
    MediaStreamTrack,
    RTCPeerConnection,
    RTCRtpSender,
    RTCSessionDescription,
)
from aiortc.contrib.media import MediaPlayer, MediaRelay

ROOT = os.path.dirname(__file__)

pcs = set()
relay = None
webcam = None


def create_local_tracks(
    play_from: str, decode: bool
) -> tuple[Optional[MediaStreamTrack], Optional[MediaStreamTrack]]:
    global relay, webcam

    if play_from:
        # If a file name was given, play from that file.
        player = MediaPlayer(play_from, decode=decode)
        return player.audio, player.video
    else:
        # Otherwise, play from the system's default webcam.
        #
        # In order to serve the same webcam to multiple users we make use of
        # a `MediaRelay`. The webcam will stay open, so it is our responsability
        # to stop the webcam when the application shuts down in `on_shutdown`.
        options = {"framerate": "30", "video_size": "640x480"}
        if relay is None:
            if platform.system() == "Darwin":
                webcam = MediaPlayer(
                    "default:none", format="avfoundation", options=options
                )
            elif platform.system() == "Windows":
                webcam = MediaPlayer(
                    "video=Integrated Camera", format="dshow", options=options
                )
            else:
                webcam = MediaPlayer("/dev/video0", format="v4l2", options=options)
            relay = MediaRelay()
        return None, relay.subscribe(webcam.video)


def force_codec(pc: RTCPeerConnection, sender: RTCRtpSender, forced_codec: str) -> None:
    kind = forced_codec.split("/")[0]
    codecs = RTCRtpSender.getCapabilities(kind).codecs
    transceiver = next(t for t in pc.getTransceivers() if t.sender == sender)
    transceiver.setCodecPreferences(
        [codec for codec in codecs if codec.mimeType == forced_codec]
    )


async def index(request: web.Request) -> web.Response:
    content = open(os.path.join(ROOT, "index.html"), "r").read()
    return web.Response(content_type="text/html", text=content)


async def javascript(request: web.Request) -> web.Response:
    content = open(os.path.join(ROOT, "client.js"), "r").read()
    return web.Response(content_type="application/javascript", text=content)


# Endpoint /latest_image zwracający najnowszy obraz JPEG
async def latest_image(request):
    from aiohttp import web
    if latest_image_bytes is not None:
        return web.Response(body=latest_image_bytes, content_type='image/jpeg')
    else:
        return web.Response(status=404)


# Endpoint /status zwracający dane telemetryczne
async def status(request):
    return web.json_response(status_data)


async def offer(request: web.Request) -> web.Response:
    params = await request.json()
    offer = RTCSessionDescription(sdp=params["sdp"], type=params["type"])

    pc = RTCPeerConnection()
    pcs.add(pc)

    @pc.on("connectionstatechange")
    async def on_connectionstatechange() -> None:
        print("Connection state is %s" % pc.connectionState)
        if pc.connectionState == "failed":
            await pc.close()
            pcs.discard(pc)

    # open media source
    audio, video = create_local_tracks(
        args.play_from, decode=not args.play_without_decoding
    )

    if audio:
        audio_sender = pc.addTrack(audio)
        if args.audio_codec:
            force_codec(pc, audio_sender, args.audio_codec)
        elif args.play_without_decoding:
            raise Exception("You must specify the audio codec using --audio-codec")

    if video:
        video_sender = pc.addTrack(video)
        if args.video_codec:
            force_codec(pc, video_sender, args.video_codec)
        elif args.play_without_decoding:
            raise Exception("You must specify the video codec using --video-codec")

    await pc.setRemoteDescription(offer)

    answer = await pc.createAnswer()
    await pc.setLocalDescription(answer)

    return web.Response(
        content_type="application/json",
        text=json.dumps(
            {"sdp": pc.localDescription.sdp, "type": pc.localDescription.type}
        ),
    )


async def on_shutdown(app: web.Application) -> None:
    # Close peer connections.
    coros = [pc.close() for pc in pcs]
    await asyncio.gather(*coros)
    pcs.clear()

    # If a shared webcam was opened, stop it.
    if webcam is not None:
        webcam.video.stop()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="WebRTC webcam demo")
    parser.add_argument("--cert-file", help="SSL certificate file (for HTTPS)")
    parser.add_argument("--key-file", help="SSL key file (for HTTPS)")
    parser.add_argument("--play-from", help="Read the media from a file and sent it.")
    parser.add_argument(
        "--play-without-decoding",
        help=(
            "Read the media without decoding it (experimental). "
            "For now it only works with an MPEGTS container with only H.264 video."
        ),
        action="store_true",
    )
    parser.add_argument(
        "--host", default="0.0.0.0", help="Host for HTTP server (default: 0.0.0.0)"
    )
    parser.add_argument(
        "--port", type=int, default=8080, help="Port for HTTP server (default: 8080)"
    )
    parser.add_argument("--verbose", "-v", action="count")
    parser.add_argument(
        "--audio-codec", help="Force a specific audio codec (e.g. audio/opus)"
    )
    parser.add_argument(
        "--video-codec", help="Force a specific video codec (e.g. video/H264)"
    )

    args = parser.parse_args()

    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    if args.cert_file:
        ssl_context = ssl.SSLContext()
        ssl_context.load_cert_chain(args.cert_file, args.key_file)
    else:
        ssl_context = None

    # Uruchom node ROS2 w osobnym wątku
    t = threading.Thread(target=ros_spin, daemon=True)
    t.start()

    app = web.Application()
    app.on_shutdown.append(on_shutdown)
    app.router.add_get("/", index)
    app.router.add_get("/client.js", javascript)
    app.router.add_post("/offer", offer)
    app.router.add_get("/status", status)
    app.router.add_get("/latest_image", latest_image)
    web.run_app(app, host="0.0.0.0", port=8080)
