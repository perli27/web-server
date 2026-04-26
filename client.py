"""
========================================================================
COMP 2322 - Computer Networking
Test Client for Multi-Threaded Web Server
========================================================================

Author      : Pearly RICHELL
Student ID  : 24114139D

How to use:
- Make sure server.py is running first
- Run: python3 client.py
- Check the printed results and server.log
========================================================================
"""

import socket
import time

HOST = "127.0.0.1"
PORT = 8080

def send_request(raw, label):
  sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  sock.connect((HOST, PORT))
  sock.sendall(raw.encode())
  response = b""
  sock.settimeout(3)
  try:
    while True:
      chunk = sock.recv(4096)
      if not chunk:
        break
      response += chunk
  except:
    pass
  sock.close()
  status = response.decode("utf-8", errors="replace").split("\r\n")[0] if response else "(no response)"
  print(f"[{label}] => {status}")

def test_keepalive():
  print("\n-- Persistent Connection Test --")
  sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  sock.connect((HOST, PORT))
  sock.settimeout(5)
  
  # send two requests on same connection
  sock.sendall(b"GET /index.html HTTP/1.1\r\nHost: localhost\r\nConnection: keep-alive\r\n\r\n")
  time.sleep(0.3)
  sock.sendall(b"GET /hello.txt HTTP/1.1\r\nHost: localhost\r\nConnection: close\r\n\r\n")

  response = b""
  try:
    while True:
      chunk = sock.recv(4096)
      if not chunk:
        break
      response += chunk
  except:
    pass
  sock.close()
  lines = [l for l in response.decode("utf-8", errors="replace").split("\r\n") if l.startswith("HTTP/")]
  for l in lines:
    print(f" => {l}")

def main():
  print(f"Sending test requests to {HOST}:{PORT}\n")

  # GET text file
  send_request(
    "GET /index.html HTTP/1.1\r\nHost: localhost\r\nConnection: close\r\n\r\n",
    "GET /index.html (expect 200)"
  )
  
  # GET image file
  send_request(
    "GET /image.jpg HTTP/1.1\r\nHost: localhost\r\nConnection: close\r\n\r\n",
    "GET /image.jpg (expect 200)"
  )
  
  # HEAD request
  send_request(
    "HEAD /index.html HTTP/1.1\r\nHost: localhost\r\nConnection: close\r\n\r\n",
    "HEAD /index.html (expect 200)"
  )

  # 404 Not Found
  send_request(
    "GET /missing.html HTTP/1.1\r\nHost: localhost\r\nConnection: close\r\n\r\n",
    "GET /missing.html (expect 404)"
  )

  # 400 Bad Request
  send_request(
    "BADREQUEST\r\n\r\n",
    "Bad request line (expect 400)"
  )

  # 403 Forbidden - directory
  send_request(
    "GET /secret/ HTTP/1.1\r\nHost: localhost\r\nConnection: close\r\n\r\n",
    "GET /secret/ (expect 403)"
  )

  # 304 Not Modified
  send_request(
    "GET /index.html HTTP/1.1\r\nHost: localhost\r\nIf-Modified-Since: Tue, 01 Jan 2030 00:00:00 GMT\r\nConnection: close\r\n\r\n",
    "GET with future If-Modified-Since (expect 304)"
  )

  # persistent connection
  test_keepalive()
  print("\nDone. Please check server.log for the full request history.")

if __name__ == "__main__":
  main()









