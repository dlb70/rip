#!/usr/bin/env python3

import socket

s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.bind(("127.0.0.1",10099))
s.sendto(bytes("hello",'utf-8'),("127.0.0.1",10012))
s.close()
