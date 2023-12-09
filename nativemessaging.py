#!/usr/bin/env python
import time
import _thread
import subprocess
import json
import sys
import struct
from time import sleep


# from https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/Native_messaging
def get_message():
    raw_length = sys.stdin.buffer.read(4)
    if len(raw_length) == 0:
        sys.exit(0)
    message_length = struct.unpack("@I", raw_length)[0]
    message = sys.stdin.buffer.read(message_length).decode("utf-8")
    return json.loads(message)


# Encode a message for transmission, given its content.
def encode_message(message_content):
    encoded_content = json.dumps(message_content).encode("utf-8")
    encoded_length = struct.pack("@I", len(encoded_content))
    return {"length": encoded_length, "content": encoded_content}


# Send an encoded message to stdout.
def send_message(encoded_message):
    sys.stdout.buffer.write(encoded_message["length"])
    sys.stdout.buffer.write(encoded_message["content"])
    sys.stdout.buffer.flush()


def run():
    global can_break

    args = ["C:\\Program Files\\Avast Software\\SecureLine VPN\\VpnNM.exe",
            '"C:\\Program Files\\Avast Software\\SecureLine VPN\\VpnNM_chrome.json"', '"chrome-extension://dmfdacibleoapmpfdgonigdfinmekhgp/"']
    shell = False

    count = 0
    popen = subprocess.Popen(args, shell=shell, stdout=subprocess.PIPE)

    def get_message():
        raw_length = popen.stdin.read(4)
        if len(raw_length) == 0:
            popen.kill()
        message_length = struct.unpack("@I", raw_length)[0]
        message = popen.stdin.buffer.read(message_length).decode("utf-8")
        return json.loads(message)
    while True:
        line = popen.stdout.readline()
        print(line)


def do_something_with(line):
    print('>>> This is it:', line)


_thread.start_new_thread(run, tuple())

can_break = False
while not can_break:
    print('Wait')
    time.sleep(1)
print('Okay!')

# if message == "hello":
#     nativemessaging.send_message(nativemessaging.encode_message("world"))
