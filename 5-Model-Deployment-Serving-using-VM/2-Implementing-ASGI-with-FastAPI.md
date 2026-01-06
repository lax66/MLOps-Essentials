# 2. Implementing ASGI with FastAPI

# First, what problem are we even solving?

You wrote a Python program.

Now you want:

- Many users
- From browsers / curl / apps
- To send requests **at the same time**
- And get responses

Your Python code alone **cannot do this**.

So we need:

1. A way to **receive HTTP requests**
2. A way to **pass them to Python**
3. A way to **send responses back**

That’s where **WSGI / ASGI** come in.

---

# 1: Web app architecture (super important)

```
User
 ↓
Browser / Mobile / curl
 ↓
WebServer(Nginx)
 ↓
ApplicationServer(Gunicorn / Uvicorn)
 ↓
PythonApp(Flask / FastAPI)

```

👉 Your Python app **never talks directly to the browser**.

---

# 2: What is WSGI?

### 📌 WSGI = Web Server Gateway Interface

> WSGI is a rulebook that tells:
> 
> 
> “How a web server should talk to a Python app”
> 

### Important:

- WSGI is **not code you write**
- It is a **standard**
- Flask follows this standard

---

## How WSGI works (mentally)

```

```

```
Request comes
↓
One requestis processed fully
↓
Response returned
↓
Next request

```

This is called **blocking / synchronous**.

---

## Example (conceptual)

If user A is being processed:

```

```

```
UserB must WAIT

```

This is fine for:

- Simple websites
- Low traffic

---

# ⚠️ Limitation of WSGI

WSGI **cannot handle**:

- WebSockets
- Long connections
- Async background tasks
- Thousands of concurrent users efficiently

---

# 3. What is ASGI? (modern solution)

### 📌 ASGI = Asynchronous Server Gateway Interface

> ASGI is the next-generation rulebook for Python web apps.
> 

ASGI allows:

- Multiple requests at the same time
- Non-blocking I/O
- WebSockets
- Background tasks

---

## How ASGI works

```

```

```
RequestA starts
↓
Wait for DB / ML / network
↓
Meanwhile requestB starts
↓
Request C starts
↓
Responses return independently

```

🔥 This is **huge for performance**.

---

# 4: Sync vs Async

### Synchronous (WSGI)

```

```

```
Do task A → finish → do task B

```

### Asynchronous (ASGI)

```

```

```
Start task A → wait → do task B → come back to A

```

---

# Real-life analogy

### 🍳 Restaurant analogy

### WSGI (1 chef):

- Chef cooks one order fully
- Everyone else waits

### ASGI (1 chef + multitasking):

- Chef puts rice to boil
- While waiting → cuts vegetables
- While waiting → fries something else

Same chef, **more output**.

---

# 5: Flask vs FastAPI

| Feature | Flask | FastAPI |
| --- | --- | --- |
| Framework | Yes | Yes |
| Uses | WSGI | ASGI |
| Async support | ❌ No | ✅ Yes |
| Validation | Manual | Auto |
| Swagger docs | ❌ No | ✅ Yes |
| Performance | Medium | High |
| Modern APIs | ❌ | ✅ |

---

# 6: Why Flask + WSGI is older

Flask was designed when:

- Async Python didn’t exist
- WebSockets were rare
- APIs were simple

It’s **not wrong**, just **old design**.

---

# 7: Why FastAPI + ASGI is better for ML

ML APIs often:

- Handle JSON-heavy payloads
- Need concurrency
- May call DBs, S3, GPUs
- Serve dashboards

FastAPI + ASGI excels here.

---

# 8: Why NOT just run `python app.py`?

Because:

- Only 1 request at a time
- Crashes on multiple users
- No scaling
- No security
- No production readiness

---

# 9: Servers involved (important)

| Server | Used with | Interface |
| --- | --- | --- |
| Gunicorn | Flask | WSGI |
| Uvicorn | FastAPI | ASGI |

---

# Why should YOU prefer ASGI over WSGI?

### Prefer ASGI when:

✔ High traffic

✔ APIs (not HTML pages)

✔ ML inference

✔ Real-time apps

✔ Cloud / Kubernetes

### WSGI is okay when:

✔ Small internal tools

✔ Simple websites

---

# Summary

- Flask ≠ WSGI
- FastAPI ≠ ASGI
- Flask **uses** WSGI
- FastAPI **uses** ASGI
- ASGI handles concurrency better
- FastAPI is built for modern APIs

## In-short

WSGI is a synchronous interface used by older Python web frameworks like Flask, whereas ASGI is an asynchronous interface used by modern frameworks like FastAPI, enabling better concurrency, WebSocket support, and higher performance for API-based and ML workloads.

So, Next we will be implementing ASGI and FastAPI to server our model in cloud VM (EC2)