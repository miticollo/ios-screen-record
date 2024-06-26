import _thread
import array
import logging
import multiprocessing
import signal
import struct
import sys
import threading
from time import sleep, time

import libusb_package
import usb
from usb.core import Device

from .coremedia.consumer import AVFileWriter, SocketUDP, Consumer
from .iphone_models import iPhoneModels
from .meaasge import MessageProcessor

logger = logging.getLogger("ioscreen")


class iOSDevice:
    def __init__(self, SerialNumber, ProductName, UsbMuxConfigInde, QTConfigIndex, VID, PID, UsbInfo):
        self.SerialNumber = SerialNumber
        self.ProductName = ProductName
        self.UsbMuxConfigInde = UsbMuxConfigInde
        self.QTConfigIndex = QTConfigIndex
        self.VID = VID
        self.PID = PID
        self.UsbInfo = UsbInfo


def find_ios_device(udid=None):
    class find_class(object):
        def __init__(self, class_):
            self._class = class_

        def __call__(self, device):
            if device.bDeviceClass == self._class:
                return True
            for cfg in device:
                intf = usb.util.find_descriptor(
                    cfg,
                    bInterfaceSubClass=self._class
                )
                if intf is not None:
                    return True
            return False

    devices = libusb_package.find(find_all=True, custom_match=find_class(0xfe))
    _device = None
    if not udid:
        try:
            _device = next(devices)
        except StopIteration:
            logger.warning('未找到 iOS 连接设备')
            sys.exit()
    else:
        for device in devices:
            if udid in device.serial_number:
                logger.info(f'Find Device UDID: {device.serial_number}')
                _device = device
                break
    if not _device:
        raise Exception(f'not find {udid}')

    return _device


def get_device_info(device: usb.Device):
    identifier: str = f"iPhone{hex(device.bcdDevice >> 8)[2:]},{hex(device.bcdDevice)[-1]}"
    udid: str = str(device.serial_number).rstrip('\x00')
    return f'{iPhoneModels.get_model(identifier)} ({udid})', iPhoneModels.get_width(identifier)


def enable_qt_config(device, stopSignal):
    """ 开启 qt 配置选项
    :param device:
    :return:
    """
    logger.info('Enabling hidden QT config')
    val = device.ctrl_transfer(0x40, 0x52, 0, 2, b'')
    sleep(1)
    if val:
        raise Exception(f'Enable QTConfig Error {val} ')
    for _ in range(5):
        try:
            device = find_ios_device(device.serial_number)
            break
        except Exception as E:
            logger.error(E)
    else:
        stopSignal.set()
    return device


def disable_qt_config(device):
    """ 关闭 qt 配置选项
    :param device:
    :return:
    """
    logger.info('Disabling hidden QT config')
    val = device.ctrl_transfer(0x40, 0x52, 0, 0, b'')
    if val:
        logger.warning('Failed sending control transfer for enabling hidden QT config')


class ByteStream:
    # mutex = threading.Lock()

    def __init__(self):
        self._byte = bytearray()

    def put(self, _byte: array):
        self._byte.extend(_byte)
        return True

    def get(self, num: int, timeout=5):
        t1 = time()
        while num > len(self._byte):
            sleep(0.01)
            if timeout < t1 - time():
                break
        _byte = self._byte[:num]
        self._byte = self._byte[num:]
        return _byte


def register_signal(stopSignal):
    def shutdown(num, frame):
        stopSignal.set()

    for sig in [signal.SIGINT, signal.SIGHUP, signal.SIGTERM]:
        signal.signal(sig, shutdown)


def record_wav(device, h264FilePath, wavFilePath, audio_only=False):
    consumer = AVFileWriter(h264FilePath=h264FilePath, wavFilePath=wavFilePath, audioOnly=audio_only)
    stopSignal = threading.Event()
    register_signal(stopSignal)
    start_reading(consumer, device, stopSignal)


def record_udp(device, audio_only=False):
    consumer = SocketUDP(audioOnly=audio_only)
    stopSignal = threading.Event()
    register_signal(stopSignal)
    start_reading(consumer, device, stopSignal)


def record_gstreamer(device, event: multiprocessing.Event):
    from .coremedia.gstreamer import GstAdapter
    stopSignal = threading.Event()
    register_signal(stopSignal)
    model, width = get_device_info(device)
    consumer = GstAdapter.new(stopSignal, model, width)
    _thread.start_new_thread(start_reading, (consumer, device, stopSignal, event,))
    consumer.loop.run()


def init_logger(verbosity: bool):
    ch = logging.StreamHandler()
    ch.setFormatter(logging.Formatter('%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s: %(message)s'))
    logging.root.handlers.clear()
    logger.addHandler(ch)
    if verbosity:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)


def start_reading(consumer: Consumer, device: Device, stopSignal: threading.Event = None,
                  event: multiprocessing.Event = None):
    stopSignal = stopSignal or threading.Event()
    disable_qt_config(device)
    device.set_configuration()
    logger.info("enable_qt_config..")
    device = enable_qt_config(device, stopSignal)
    qt_config = None
    for _config in device.configurations():
        qt_config = usb.util.find_descriptor(_config, bInterfaceSubClass=0x2A)
        if qt_config:
            device.set_configuration(_config.bConfigurationValue)
            break
    device.ctrl_transfer(0x02, 0x01, 0, 0x86, b'')
    device.ctrl_transfer(0x02, 0x01, 0, 0x05, b'')
    if not qt_config:
        raise Exception('Find QTConfig Error')
    inEndpoint = outEndpoint = None
    for i in qt_config:
        if usb.util.endpoint_direction(i.bEndpointAddress) == usb.util.ENDPOINT_IN:
            inEndpoint = i  # 入口端点
        if usb.util.endpoint_direction(i.bEndpointAddress) == usb.util.ENDPOINT_OUT:
            outEndpoint = i  # 出口端点
    if not inEndpoint or not outEndpoint:
        raise Exception('could not get InEndpoint or outEndpoint')
    logger.info("USB connection ready, waiting for ping..")

    message = MessageProcessor(device, inEndpoint=inEndpoint, outEndpoint=outEndpoint, stopSignal=stopSignal,
                               cmSampleBufConsumer=consumer)
    byteStream = ByteStream()

    def writeStream():
        """ 异步写入线程
        :return:
        """
        while True:
            try:
                data = device.read(inEndpoint, 1024 * 1024, 3000)
                byteStream.put(data)
            except Exception as E:
                logger.warning(E)
                message.outEndpoint = None
                message.inEndpoint = None
                stopSignal.set()
                break

    def readStream():
        """ 异步读取流数据
        :return:
        """
        while True:
            lengthBuffer = byteStream.get(4)
            _length = struct.unpack('<I', lengthBuffer)[0] - 4
            buffer = byteStream.get(_length)
            message.receive_data(buffer, event)

    _thread.start_new_thread(writeStream, ())
    _thread.start_new_thread(readStream, ())

    while not stopSignal.wait(1):
        pass
    message.close_session()
    disable_qt_config(device)
    consumer.stop()
