# COMP 2322 - Multi-Threaded Web Server

**Author      :** Pearly RICHELL  
**Student ID  :** 24114139D

---

## Project Description

A multi-threaded HTTP/1.1 web server built in Python using raw sockets. No HTTPServer class or third-party libraries were used.

## Files

```
project/
├── server.py       # the web server (run this)
├── client.py       # test client to verify all features
├── server.log      # auto-generated request log
├── README.md       # this file
└── www/            # folder where served files are stored
    ├── index.html
    ├── hello.txt
    ├── image.jpg
    └── secret/     # directory used to test 403 response
```

## Requirements

- Python 3.8 or above
- No extra libraries needed — standard library only

## How to Run

### 1. Start the server

```bash
python3 src/server.py
```

You should see:
```
Server running at http://127.0.0.1:8080
Files served from: /your/path/www
Press Ctrl+C to stop
```

### 2. Open in browser

```
http://127.0.0.1:8080/index.html
http://127.0.0.1:8080/image.jpg
http://127.0.0.1:8080/hello.txt
```

### 3. Run the test client

Open a second terminal while the server is running:

```bash
python3 client.py
```

This tests all features automatically and prints the result of each request.

### 4. Stop the server

Press `Ctrl+C` in the server terminal.

---

## What It Supports

| Feature | Details |
|---|---|
| GET | Serves text files and image files |
| HEAD | Returns headers only, no body |
| 200 OK | File found and returned |
| 304 Not Modified | File not changed since If-Modified-Since date |
| 400 Bad Request | Malformed or unsupported request |
| 403 Forbidden | Directory access or path traversal attempt |
| 404 Not Found | File does not exist |
| keep-alive | Connection stays open for multiple requests |
| close | Connection closes after one response |
| Logging | Every request is written to server.log |

---

## Configuration

Edit these values at the top of `server.py` if needed:

| Variable | Default | Description |
|---|---|---|
| `HOST` | `127.0.0.1` | Server address |
| `PORT` | `8080` | Port number |
| `SERVER_ROOT` | `./www` | Folder to serve files from |
| `LOGFILE` | `server.log` | Log output file |
| `TIMEOUT` | `10` | Keep-alive timeout in seconds |
| `MAX_REQUESTS` | `100` | Max requests per connection |
