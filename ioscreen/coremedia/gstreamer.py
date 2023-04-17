import logging
import struct
import threading
from time import sleep

import gi

from .CMFormatDescription import DescriptorConst
from .CMSampleBuffer import CMSampleBuffer
from .wav import get_wav_header

gi.require_version('Gst', '1.0')
gi.require_version('GstBase', '1.0')
gi.require_version('GstAudio', '1.0')
gi.require_version('GstVideo', '1.0')
gi.require_version('Gtk', '3.0')

from .consumer import startCode, Consumer
from gi.repository import Gst, Gtk

GST_PLUGIN_PATH = '/usr/local/lib/gstreamer-1.0'


def setup_live_playAudio(pipe):
    autoaudiosink = Gst.ElementFactory.make("autoaudiosink", "auto_audio_sink")
    autoaudiosink.set_property("sync", False)
    pipe.add(autoaudiosink)
    pipe.get_by_name("queue_audio_convert").link(autoaudiosink)


def setup_video_pipeline(pipe):
    src = Gst.ElementFactory.make("appsrc", "my-video_src")
    src.set_property("is-live", True)
    queue1 = Gst.ElementFactory.make("queue", "queue_h264parse")
    h264parse = Gst.ElementFactory.make("h264parse", "h264_parse")
    avdecH264 = Gst.ElementFactory.make("vtdec", "vt_dec")

    queue2 = Gst.ElementFactory.make("queue", "queue_video_convert")
    videoconvert = Gst.ElementFactory.make("videoconvert", "video_convert")

    queue3 = Gst.ElementFactory.make("queue", "queue_av")
    sink = Gst.ElementFactory.make("gtksink", "av_sink")
    sink.set_property("sync", False)

    sink_widget: Gtk.Widget = sink.get_property("widget")

    pipe.add(src)
    pipe.add(queue1)
    pipe.add(h264parse)
    pipe.add(avdecH264)
    pipe.add(queue2)
    pipe.add(videoconvert)
    pipe.add(queue3)
    pipe.add(sink)

    src.link(queue1)
    queue1.link(h264parse)
    h264parse.link(avdecH264)
    avdecH264.link(queue2)
    queue2.link(videoconvert)
    videoconvert.link(queue3)
    queue3.link(sink)
    return src, sink_widget


def setup_audio_pipeline(pipe):
    src = Gst.ElementFactory.make("appsrc", "my-audio-src")
    src.set_property("is-live", True)

    queue1 = Gst.ElementFactory.make("queue", "queue_wav_parse")
    wavparse = Gst.ElementFactory.make("wavparse", "wav_parse")
    wavparse.set_property("ignore-length", True)

    queue2 = Gst.ElementFactory.make("queue", "queue_audio_convert")
    audioconvert = Gst.ElementFactory.make("audioconvert", "audio_convert")

    pipe.add(src)
    pipe.add(queue1)
    pipe.add(wavparse)
    pipe.add(queue2)
    pipe.add(audioconvert)

    src.link(queue1)
    queue1.link(wavparse)
    wavparse.link(audioconvert)
    audioconvert.link(queue2)
    return src


class VideoPlayer(Gtk.Window):
    def __init__(self, pipe: Gst.Pipeline, sink: Gtk.Widget, stop_signal: threading.Event, title: str, width: int):
        Gtk.init()
        self.pipe: Gst.Pipeline = pipe
        self.sink: Gtk.Widget = sink
        self.stop_signal: threading.Event = stop_signal
        Gtk.Window.__init__(self, title=title)

        # Set up the window
        self.set_resizable(False)
        self.set_default_size(width, 942)
        self.connect("destroy", self.on_destroy)

        scrolled_window = Gtk.ScrolledWindow()
        scrolled_window.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.NEVER)
        scrolled_window.add(self.sink)
        self.add(scrolled_window)

        # Set the pipeline to play
        self.pipe.set_state(Gst.State.PLAYING)

        # Create a bus and connect it to the message signal
        self.bus: Gst.Bus = self.pipe.get_bus()
        self.bus.add_signal_watch()
        self.bus.connect("message", self.on_message)

    def on_destroy(self, widget):
        self.sink = None
        av_sink = self.pipe.get_by_name("av_sink")
        av_sink.set_state(Gst.State.NULL)
        self.stop_signal.set()

    def on_message(self, bus, message):
        if self.stop_signal.is_set():
            self.pipe.set_state(Gst.State.NULL)
            Gtk.main_quit()
        # Handle error messages
        t = message.type
        Gst.debug_bin_to_dot_file_with_ts(self.pipe, Gst.DebugGraphDetails.ALL, "test")
        if t == Gst.MessageType.ERROR:
            err, debug = message.parse_error()
            logging.error(f" {err}: {debug}")
            self.stop_signal.set()
            sleep(2)
            self.pipe.set_state(Gst.State.NULL)
            Gtk.main_quit()
        elif t == Gst.MessageType.EOS:
            logging.info("End-of-stream")
            self.pipe.set_state(Gst.State.NULL)
            Gtk.main_quit()

    def run(self):
        # Show the window and start the main loop
        self.show_all()
        Gtk.main()


class GstAdapter(Consumer):
    audioAppSrcTargetElementName = "audio_target"
    videoAppSrcTargetElementName = "video_target"
    MP3 = "mp3"
    OGG = "ogg"

    def __init__(self, videoAppSrc, audioAppSrc, firstAudioSample, loop=None, pipeline=None, stopSignal=None):
        self.videoAppSrc = videoAppSrc
        self.audioAppSrc = audioAppSrc
        self.firstAudioSample = firstAudioSample
        self.pipeline = pipeline
        self.loop = loop
        self.stopSignal = stopSignal

    @classmethod
    def new(cls, stopSignal, title: str, width: int):
        Gst.init(None)
        logging.info("Starting Gstreamer..")

        # fix Gst plugin path issue in brew:
        # https://gstreamer.freedesktop.org/documentation/gstreamer/gstregistry.html?gi-language=python#GstRegistry
        # default locations are: $XDG_DATA_HOME/gstreamer-$GST_API_VERSION/plugins/ and $prefix/libs
        # brew gstream installation $prefix=/usr/local/Cellar/gstreamer/1.20.3/lib
        # and installed plugins in /usr/local/lib/gstreamer-1.0
        registry = Gst.Registry.get()
        if not registry.find_plugin('app'):
            logging.warning("Gstreamer plugin not loaded... scan for %s", GST_PLUGIN_PATH)
            registry.scan_path(GST_PLUGIN_PATH)

        pipe: Gst.Pipeline = Gst.Pipeline.new("QT_Hack_Pipeline")
        (videoAppSrc, sink) = setup_video_pipeline(pipe)
        audioAppSrc = setup_audio_pipeline(pipe)
        setup_live_playAudio(pipe)
        loop = VideoPlayer(pipe, sink, stopSignal, title, width)
        # _thread.start_new_thread(run_main_loop, (pipe,))
        logging.info("Gstreamer is running!")
        return cls(videoAppSrc, audioAppSrc, True, loop)

    def consume(self, data: CMSampleBuffer):
        if data.MediaType == DescriptorConst.MediaTypeSound:
            if self.firstAudioSample:
                self.firstAudioSample = False
                self.send_wav_header()
            return self.send_audio_sample(data)

        if data.OutputPresentationTimestamp.CMTimeValue > 17446044073700192000:
            data.OutputPresentationTimestamp.CMTimeValue = 0

        if data.HasFormatDescription:
            data.OutputPresentationTimestamp.CMTimeValue = 0
            self.write_app_src(startCode + data.FormatDescription.PPS, data)
            self.write_app_src(startCode + data.FormatDescription.SPS, data)
        self.write_buffers(data)

    def write_buffers(self, data: CMSampleBuffer):
        buf = data.SampleData
        if buf:
            while len(buf) > 0:
                _length = struct.unpack('>I', buf[:4])[0]
                self.write_app_src(startCode + buf[4:_length + 4], data)
                buf = buf[_length + 4:]
        return True

    def write_app_src(self, buf, data: CMSampleBuffer):
        gstBuf = Gst.Buffer.new_allocate(None, len(buf), None)
        gstBuf.pts = data.OutputPresentationTimestamp.CMTimeValue
        gstBuf.dts = 0
        gstBuf.fill(0, buf)
        self.videoAppSrc.emit('push-buffer', gstBuf)

    def send_wav_header(self):
        wav_header = get_wav_header(100)
        gstBuf = Gst.Buffer.new_allocate(None, len(wav_header), None)
        gstBuf.pts = 0
        gstBuf.dts = 0
        gstBuf.fill(0, wav_header)
        self.audioAppSrc.emit('push-buffer', gstBuf)

    def send_audio_sample(self, data: CMSampleBuffer):
        gstBuf = Gst.Buffer.new_allocate(None, len(data.SampleData), None)
        gstBuf.pts = data.OutputPresentationTimestamp.CMTimeValue
        gstBuf.dts = 0
        gstBuf.fill(0, data.SampleData)
        self.audioAppSrc.emit('push-buffer', gstBuf)

    def stop(self):
        if self.audioAppSrc:
            self.audioAppSrc.send_event(Gst.Event.new_eos())
        if self.videoAppSrc:
            self.videoAppSrc.send_event(Gst.Event.new_eos())
        if not self.pipeline:
            return
