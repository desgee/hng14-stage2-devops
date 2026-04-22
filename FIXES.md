1. at line 1 and 2 of app/.env   
Problem — The .env file contains plaintext credentials and was commited to github.
What I did - added the .env file to .gitignore and .dockerignore.

2. Redis has no authentication
Problem: app/main.py & Worker/worker.py — Both connect to Redis without a password, yet the .env defines REDIS_PASSWORD at line 1. The password is never actually used.

Fix:  defined redis credentials in the .env file and called properly in the application.

r = redis.Redis(
    host=os.getenv("REDIS_HOST", "localhost"),
    port=int(os.getenv("REDIS_PORT", 6379)),
    password=os.getenv("REDIS_PASSWORD"),
    decode_responses=True  
)

3. Problem: Worker has no graceful shutdown

Fix:  Add graceful shutdown


running = True

def handle_signal(sig, frame):
    global running
    print("Shutting down gracefully...")
    running = False

signal.signal(signal.SIGTERM, handle_signal)
signal.signal(signal.SIGINT, handle_signal)

while running:
    job = r.brpop("job", timeout=5)
    if job:
        _, job_id = job
        process_job(job_id.decode())


4. Problem: Route /jobs/{job_id} in main.py file returns 200 on "not found".

Fix: correct the status code to 404.

from fastapi import FastAPI, HTTPException

@app.get("/jobs/{job_id}")
def get_job(job_id: str):
    status = r.hget(f"job:{job_id}", "status")
    if not status:
        raise HTTPException(status_code=404, detail="Job not found")
    return {"job_id": job_id, "status": status.decode()}


5.  No input validation on job_id

Problem: The app/main.py job_id path parameter is accepted as a raw string and passed directly into Redis keys with no validation.

Fix:Validate it

import re
from fastapi import HTTPException

UUID_RE = re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$')

@app.get("/jobs/{job_id}")
def get_job(job_id: str):
    if not UUID_RE.match(job_id):
        raise HTTPException(status_code=400, detail="Invalid job ID")
    ...


6.  Missing python-dotenv — .env is never loaded

Fix: Add python-dotenv to requirements.txt and then import into main.py and worker.py

# requirements.txt — add:
python-dotenv

# top of main.py and worker.py:
from dotenv import load_dotenv
load_dotenv()

7. No Content-Type or CORS headers on the API

Fix:  Import and add the middleware










