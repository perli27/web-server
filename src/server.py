"""
========================================================================
COMP 2322 - Computer Networking
Project: Multi-Threaded Web Server
========================================================================

Author      : Pearly RICHELL
Student ID  : 24114139D

Project Description:
A multi-threaded HTTP/1.1 web server built from using Python's socket and threading modules. 
No high-level HTTP frameworks were used.

Features:
- Multi-threading: one thread per TCP connection
- Methods: GET (text + image files), HEAD
- Status Codes: 200, 304, 400, 403, 404
- Persistent Connections (Connection: keep-alive)
- Non-persistent Connections (Connection: close)
- Conditional GET via If-Modified-Since / Last-Modified
- Request logging to server.log

How to use:
- Run python3 server.py
- Open http://127.0.0.1:8080 in your browser.
========================================================================
"""
import socket
import threading
import os
import mimetypes
import logging
import datetime
import email.utils

# Server Configuration
HOST = "127.0.0.1"
PORT = 8080
SERVER_ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "test_files")
LOGFILE = "server.log"
BUFFER_SIZE = 4096
TIMEOUT = 10      # seconds before a persistent connection is closed
MAX_REQUESTS = 100         # maximum requests per persistent connection

#Logging Setup
logging.basicConfig(filename=LOGFILE, level=logging.INFO, format="%(message)s")

def write_log(ip, method, filename, status):
  now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
  line = f"[{now}] IP: {ip} | {method} {filename} | {status}"
  logging.info(line)
  print(line)

def get_status_text(code):
  statuses = {
    200: "OK",
    304: "Not Modified",
    400: "Bad Request",
    403: "Forbidden",
    404: "Not Found"
  }
  return statuses.get(code, "Unknown")

def make_headers(code, ctype=None, length=None, last_mod=None, conn="close"):
  reason = get_status_text(code)
  date = email.utils.formatdate(usegmt=True)
  h = f"HTTP/1.1 {code} {reason}\r\n"
  h += f"Date: {date}\r\n"
  h += "Server: MyServer/1.0\r\n"
  
  if ctype:
    h += f"Content-Type: {ctype}\r\n"
  if length is not None:
    h += f"Content-Length: {length}\r\n"
  if last_mod:
    h += f"Last-Modified: {last_mod}\r\n"

  h += f"Connection: {conn}\r\n"
  h += "\r\n"
  return h

def send_error(conn, code, ip, conn_val="close"):
  body = f"<html><body><h1>{code} {get_status_text(code)}</h1></body></html>"
  body = body.encode()
  headers = make_headers(code, ctype="text/html", length=len(body), conn=conn_val)
  try:
    conn.sendall(headers.encode() + body)
  except:
    pass
  write_log(ip, "ERR", "-", code)

def parse_request(data):
  try:
    text = data.decode("utf-8", errors="replace")
    lines = text.split("\r\n")
    parts = lines[0].split()

    if len(parts)!=3:
      return None

    method, uri, version = parts
    headers = {}

    for line in lines[1:]:
      if not line:
        break
      if ":" in line:
        k, _, v=line.partition(":")
        headers[k.strip().lower()] = v.strip()

    return method.upper(), uri, version, headers
  except:
    return None

def get_filepath(uri):
  path = uri.split("?")[0]    # remove query string
  if path == "/":
    path = "/index.html"

  full = os.path.realpath(os.path.join(SERVER_ROOT, path.lstrip("/")))
  if not full.startswith(os.path.realpath(SERVER_ROOT)):   # make sure stay inside www folder
    return None
  
  return full

def handle(conn, ip, raw):
  parsed = parse_request(raw)
  if parsed is None:
    send_error(conn, 400, ip)
    return False

  method, uri, version, headers = parsed
  # figure out if connection should stay open
  conn_header = headers.get("connection", "").lower()
  if version == "HTTP/1.1":
    keep = conn_header != "close"
  else:
    keep = conn_header == "keep-alive"
  conn_val = "keep-alive" if keep else "close"

  # only allow GET and HEAD methods
  if method not in ("GET", "HEAD"):
    send_error(conn, 400, ip, conn_val)
    return keep
  
  filepath = get_filepath(uri)
  if filepath is None:
    send_error(conn, 403, ip, conn_val)
    write_log(ip, method, uri, 403)
    return keep
  
  if not os.path.exists(filepath):
    send_error(conn, 404, ip, conn_val)
    write_log(ip, method, uri, 404)
    return keep
  
  if os.path.isdir(filepath):
    send_error(conn, 403, ip, conn_val)
    write_log(ip, method, uri, 403)
    return keep

  # get content type from file extension
  ctype, _ = mimetypes.guess_type(filepath)
  if ctype is None:
    ctype = "application/octet-stream"

  # get last modified time
  mtime = os.path.getmtime(filepath)
  last_mod = email.utils.formatdate(mtime, usegmt=True)

  # check if-modified-since
  ims = headers.get("if-modified-since", "")
  if ims:
    try:
      ims_time = email.utils.parsedate_to_datetime(ims).timestamp()
      if mtime <= ims_time:
        h = make_headers(304, last_mod=last_mod, conn=conn_val)
        conn.sendall(h.encode())
        write_log(ip, method, uri, 304)
        return keep
    except:     # ignore if bad date format
      pass
 
  # read the file
  try:
    with open(filepath, "rb") as f:
      body = f.read()
  except PermissionError:
    send_error(conn, 403, ip, conn_val)
    write_log(ip, method, uri, 403)
    return keep

  headers_str = make_headers(200, ctype=ctype, length=len(body), last_mod=last_mod, conn=conn_val)
  try:
    conn.sendall(headers_str.encode())
    if method == "GET":
      conn.sendall(body)
  except:
    return False
  
  write_log(ip, method, uri, 200)
  return keep

def client_thread(conn, addr):
  ip = addr[0]
  conn.settimeout(TIMEOUT)
  buf = b""
  count = 0
  try:
    while True:
      # keep reading until get full headers
      try:
        while b"\r\n\r\n" not in buf:
          chunk = conn.recv(BUFFER_SIZE)
          if not chunk:
            return
          buf += chunk
      except socket.timeout:
        return
      
      # split off the request
      end = buf.index(b"\r\n\r\n") + 4
      request = buf[:end]
      buf = buf[end:]
      count += 1

      # close connection if too many requests
      if count >= MAX_REQUESTS:
        handle(conn, ip, request)
        return

      keep = handle(conn, ip, request)
      if not keep:
        return
  finally:
    conn.close()

def main():
  os.makedirs(SERVER_ROOT, exist_ok=True)
  s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
  s.bind((HOST, PORT))
  s.listen(5)

  print(f"Server running at http://{HOST}:{PORT}")
  print(f"Files served from: {SERVER_ROOT}")
  print("Press Ctrl+C to stop\n")
  
  try:
    while True:
      conn, addr = s.accept()
      t = threading.Thread(target=client_thread, args=(conn, addr), daemon=True)
      t.start()
  except KeyboardInterrupt:
    print("Server stopped.")
  finally:
    s.close()

if __name__ == "__main__":
  main()
