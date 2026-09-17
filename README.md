# Online Document Editing Service

A self-hosted online document editing service built with **FastAPI**, **ONLYOFFICE Document Server**, **MinIO**, and **Redis**.

The service allows users to:

* Upload DOCX documents.
* Store documents in MinIO/S3.
* Store document metadata in Redis.
* Open documents in ONLYOFFICE.
* Edit documents online.
* Save edited documents back to MinIO.
* Synchronize the latest document content without document versioning.
* Download the current document.

---

## 1. Architecture

```text
                         Browser
                            |
             +--------------+--------------+
             |                             |
             v                             v
       FastAPI :8000                 ONLYOFFICE :8080
             |                             |
       +-----+------+                      |
       |            |                      |
       v            v                      |
    Redis         MinIO <------------------+
   :6379          :9000
       |
   Metadata
```

### Docker architecture

```text
+------------------------------------------------------+
|                    Docker Compose                    |
|                                                      |
|  +-------------+      +---------------------------+  |
|  | document-api|----->| document-redis            |  |
|  | FastAPI     |      | Redis                     |  |
|  | :8000       |      | :6379                     |  |
|  +------+------+      +---------------------------+  |
|         |                                            |
|         |                                            |
|         v                                            |
|  +-------------+                                    |
|  | document-   |                                    |
|  | minio       |                                    |
|  | MinIO       |                                    |
|  | :9000       |                                    |
|  +-------------+                                    |
|         ^                                            |
|         |                                            |
|  +------+----------------+                           |
|  | document-onlyoffice   |                           |
|  | ONLYOFFICE            |                           |
|  | :8080                 |                           |
|  +-----------------------+                           |
|                                                      |
+------------------------------------------------------+
```

---

# 2. Technology Stack

| Component        | Technology                 | Purpose                          |
| ---------------- | -------------------------- | -------------------------------- |
| Backend          | FastAPI                    | REST API and ONLYOFFICE callback |
| Document Editor  | ONLYOFFICE Document Server | Online document editing          |
| Object Storage   | MinIO                      | DOCX/S3 document storage         |
| Metadata Store   | Redis                      | Document metadata                |
| Containerization | Docker                     | Deployment                       |
| Orchestration    | Docker Compose             | Local/test deployment            |
| Frontend         | HTML + JavaScript          | Document upload/edit UI          |

---

# 3. Main Workflow

## Upload

```text
Browser
   |
   | POST /documents
   v
FastAPI
   |
   +-----> MinIO
   |        document_id/file.docx
   |
   +-----> Redis
            document metadata
```

## Edit

```text
Browser
   |
   | GET /documents/{id}/edit
   v
FastAPI
   |
   | ONLYOFFICE configuration
   v
Browser
   |
   v
ONLYOFFICE Editor
```

## Save

When the user saves the document, ONLYOFFICE calls:

```text
POST /onlyoffice/callback/{document_id}
```

The callback contains a temporary URL to the updated DOCX.

The backend:

```text
ONLYOFFICE
     |
     | callback
     v
FastAPI
     |
     | download updated DOCX
     v
ONLYOFFICE
     |
     | DOCX bytes
     v
FastAPI
     |
     | overwrite
     v
MinIO
     |
     | update metadata
     v
Redis
```

No document versioning is used.

The same MinIO object is overwritten.

---

# 4. Project Structure

```text
document-editor/
│
├── app/
│   ├── main.py
│   ├── config.py
│   │
│   ├── api/
│   │   ├── documents.py
│   │   └── onlyoffice.py
│   │
│   ├── models/
│   │   └── document.py
│   │
│   └── services/
│       ├── minio_service.py
│       ├── redis_service.py
│       └── onlyoffice_service.py
│
├── frontend/
│   └── index.html
│
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── .env
└── README.md
```

---

# 5. Prerequisites

Install:

* Docker
* Docker Compose

Verify:

```bash
docker --version
```

```bash
docker compose version
```

Example:

```text
Docker version 28.x
Docker Compose version v2.x
```

---

# 6. Docker Compose

Create:

```text
docker-compose.yml
```

with:

```yaml
services:

  minio:
    image: quay.io/minio/minio:latest
    container_name: document-minio

    command: server /data --console-address ":9001"

    environment:
      MINIO_ROOT_USER: minioadmin
      MINIO_ROOT_PASSWORD: minioadmin123

    ports:
      - "9000:9000"
      - "9001:9001"

    volumes:
      - minio_data:/data


  redis:
    image: redis:7-alpine
    container_name: document-redis

    command: redis-server --appendonly yes

    ports:
      - "6379:6379"

    volumes:
      - redis_data:/data


  onlyoffice:
    image: onlyoffice/documentserver:latest
    container_name: document-onlyoffice

    ports:
      - "8080:80"

    environment:
      JWT_ENABLED: "false"
      ALLOW_PRIVATE_IP_ADDRESS: "true"

    extra_hosts:
      - "host.docker.internal:host-gateway"

    volumes:
      - onlyoffice_data:/var/www/onlyoffice/Data


  api:
    build: .

    container_name: document-api

    ports:
      - "8000:8000"

    extra_hosts:
      - "host.docker.internal:host-gateway"

    environment:

      MINIO_ENDPOINT: minio:9000
      MINIO_ACCESS_KEY: minioadmin
      MINIO_SECRET_KEY: minioadmin123
      MINIO_BUCKET: documents
      MINIO_SECURE: "false"

      REDIS_HOST: redis
      REDIS_PORT: "6379"
      REDIS_DB: "0"

      INTERNAL_API_URL: http://api:8000
      PUBLIC_API_URL: http://localhost:8000

      ONLYOFFICE_URL: http://onlyoffice

    depends_on:
      - minio
      - redis
      - onlyoffice


volumes:

  minio_data:
  redis_data:
  onlyoffice_data:
```

---

# 7. Dockerfile

Create:

```text
Dockerfile
```

```dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY frontend ./frontend

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

# 8. Python Dependencies

Create:

```text
requirements.txt
```

Example:

```text
fastapi
uvicorn[standard]
python-multipart
pydantic-settings
redis
minio
httpx
```

---

# 9. Configuration

The application uses the following configuration:

```text
MINIO_ENDPOINT=minio:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin123
MINIO_BUCKET=documents
MINIO_SECURE=false

REDIS_HOST=redis
REDIS_PORT=6379
REDIS_DB=0

INTERNAL_API_URL=http://api:8000
PUBLIC_API_URL=http://localhost:8000

ONLYOFFICE_URL=http://onlyoffice
```

### Important

`INTERNAL_API_URL` and `PUBLIC_API_URL` have different purposes.

Inside Docker:

```text
http://api:8000
```

is used because the Docker service is called `api`.

From the browser:

```text
http://localhost:8000
```

is used because port `8000` is published to the host.

Similarly:

```text
http://onlyoffice
```

is used for container-to-container communication.

---

# 10. Build the Application

From the project directory:

```bash
docker compose build
```

For a completely fresh build:

```bash
docker compose build --no-cache
```

---

# 11. Start the Application

Start all services:

```bash
docker compose up -d
```

Check running containers:

```bash
docker compose ps
```

Expected:

```text
document-api
document-minio
document-redis
document-onlyoffice
```

---

# 12. Check Application Logs

FastAPI:

```bash
docker logs -f document-api
```

ONLYOFFICE:

```bash
docker logs -f document-onlyoffice
```

Redis:

```bash
docker logs -f document-redis
```

MinIO:

```bash
docker logs -f document-minio
```

---

# 13. Access the Application

Open:

```text
http://localhost:8000
```

The FastAPI application serves the frontend.

ONLYOFFICE JavaScript API is loaded from:

```text
http://localhost:8080/web-apps/apps/api/documents/api.js
```

---

# 14. MinIO Console

Open:

```text
http://localhost:9001
```

Login:

```text
Username: minioadmin
Password: minioadmin123
```

The application automatically creates the:

```text
documents
```

bucket.

---

# 15. Redis

Redis is available on:

```text
localhost:6379
```

Inside Docker, the application connects to:

```text
redis:6379
```

Redis stores metadata such as:

```json
{
  "document_id": "197f08b9-fc22-44ab-8226-b3dc9b51968f",
  "filename": "example.docx",
  "bucket": "documents",
  "s3_key": "197f08b9-fc22-44ab-8226-b3dc9b51968f/example.docx",
  "content_type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
  "version": 1,
  "created_at": "...",
  "updated_at": "..."
}
```

The `version` field can remain in the metadata model for compatibility, but it is **not incremented** during document saves.

---

# 16. REST API

## Upload Document

```http
POST /documents
```

Multipart form:

```text
file=<document>
```

Example:

```bash
curl -X POST \
  -F "file=@example.docx" \
  http://localhost:8000/documents
```

---

## Get Document Metadata

```http
GET /documents/{document_id}
```

Example:

```bash
curl http://localhost:8000/documents/<DOCUMENT_ID>
```

---

## Download Document

```http
GET /documents/{document_id}/download
```

Example:

```text
http://localhost:8000/documents/<DOCUMENT_ID>/download
```

---

## Get ONLYOFFICE Configuration

```http
GET /documents/{document_id}/edit
```

This endpoint creates the ONLYOFFICE editor configuration.

---

## Force Save

```http
POST /documents/{document_id}/force-save
```

This sends a force-save command to ONLYOFFICE.

---

## ONLYOFFICE Callback

```http
POST /onlyoffice/callback/{document_id}
```

ONLYOFFICE calls this endpoint after saving the document.

---

## Delete Document

```http
DELETE /documents/{document_id}
```

This removes:

* MinIO object
* Redis metadata

---

# 17. Document Synchronization

The system does not create document versions.

For example, the initial document is stored as:

```text
documents/
└── 197f08b9-fc22-44ab-8226-b3dc9b51968f/
    └── example.docx
```

After the user edits the document:

```text
documents/
└── 197f08b9-fc22-44ab-8226-b3dc9b51968f/
    └── example.docx
```

The same object is overwritten.

This provides simple synchronization of the latest document.

---

# 18. ONLYOFFICE Save Status

The callback uses ONLYOFFICE status values.

Important statuses:

```text
2 = document is ready for saving
6 = force save
```

The application synchronizes the document when:

```python
status in (2, 6)
```

Other statuses do not trigger a MinIO update.

---

# 19. ONLYOFFICE Callback URL

The editor configuration contains:

```json
{
  "editorConfig": {
    "callbackUrl": "http://api:8000/onlyoffice/callback/{document_id}"
  }
}
```

This is important because the callback is made from the ONLYOFFICE Docker container.

Therefore:

```text
ONLYOFFICE
     |
     | Docker network
     v
api:8000
```

Do not use:

```text
localhost:8000
```

for the internal callback.

---

# 20. Callback File Download

ONLYOFFICE can return a temporary URL similar to:

```text
http://localhost:8080/cache/files/data/.../output.docx
```

In the test Docker environment, the application can translate this URL to the Docker host:

```text
http://host.docker.internal:8080/cache/files/data/.../output.docx
```

The API downloads the updated DOCX and overwrites the existing MinIO object.

The Docker API service therefore contains:

```yaml
extra_hosts:
  - "host.docker.internal:host-gateway"
```

This approach is intended for the test environment.

For production, use a proper internal DNS/reverse-proxy hostname instead of relying on `host.docker.internal`.

---

# 21. Health Check

The application provides:

```http
GET /health
```

Test:

```bash
curl http://localhost:8000/health
```

Expected:

```json
{
  "status": "ok"
}
```

---

# 22. Docker Network Troubleshooting

Check Docker networks:

```bash
docker network ls
```

Inspect the Compose network:

```bash
docker network inspect document-editor_default
```

The exact network name can vary depending on the project directory.

Check API → ONLYOFFICE:

```bash
docker exec -it document-api python -c "import httpx; r=httpx.get('http://onlyoffice', timeout=10); print(r.status_code)"
```

A response such as:

```text
302
```

is expected and proves that the API container can reach ONLYOFFICE.

---

# 23. Troubleshooting Save

Check API logs:

```bash
docker logs -f document-api
```

When saving, you should see:

```text
ONLYOFFICE CALLBACK
Document: <DOCUMENT_ID>
Payload: ...
ONLYOFFICE status: 6
Downloading updated DOCX...
Downloaded updated DOCX: XXXXX bytes
Document overwritten in MinIO: ...
DOCUMENT SYNCHRONIZED SUCCESSFULLY
```

If you see:

```text
SYNC ERROR
```

check the callback URL and the ONLYOFFICE cache file access.

---

# 24. Complete Deployment

For a clean deployment:

```bash
docker compose down
```

Build:

```bash
docker compose build --no-cache
```

Start:

```bash
docker compose up -d
```

Check:

```bash
docker compose ps
```

Check API:

```bash
curl http://localhost:8000/health
```

Open:

```text
http://localhost:8000
```

---

# 25. Stop the Application

Stop containers:

```bash
docker compose stop
```

Remove containers:

```bash
docker compose down
```

Remove containers and volumes:

```bash
docker compose down -v
```

**Warning:** `docker compose down -v` deletes the Docker volumes containing MinIO and Redis data.

---

# 26. Rebuild After Code Changes

After changing Python code:

```bash
docker compose build api
docker compose up -d api
```

For a completely clean rebuild:

```bash
docker compose down
docker compose build --no-cache
docker compose up -d
```

---

# 27. Production Considerations

This Docker Compose configuration is suitable for development and test environments.

For production, consider:

* HTTPS/TLS
* ONLYOFFICE JWT authentication
* MinIO authentication with strong credentials
* Redis authentication
* Reverse proxy such as Nginx
* Domain names instead of localhost
* Persistent storage
* Backup strategy
* Container resource limits
* Authentication/authorization
* File type and file size validation
* Antivirus scanning
* Audit logging
* Access control
* Network isolation
* Secrets management

Example production architecture:

```text
                         Internet / Intranet
                                |
                                v
                         +-------------+
                         |    Nginx    |
                         | HTTPS/TLS   |
                         +------+------+
                                |
                 +--------------+--------------+
                 |                             |
                 v                             v
             FastAPI                       ONLYOFFICE
             :8000                           :80
                 |
          +------+------+
          |             |
          v             v
       Redis           MinIO
```

---

# 28. Summary

The application provides a simple self-hosted document editing platform:

```text
Upload
   ↓
FastAPI
   ↓
MinIO + Redis
   ↓
ONLYOFFICE
   ↓
User edits document
   ↓
ONLYOFFICE Save
   ↓
FastAPI Callback
   ↓
Download updated DOCX
   ↓
Overwrite MinIO
   ↓
Update Redis
```

The latest document is always stored in the same MinIO object.

No document versioning is required.

---

## Quick Start

```bash
# 1. Build
docker compose build

# 2. Start
docker compose up -d

# 3. Check containers
docker compose ps

# 4. Check API
curl http://localhost:8000/health

# 5. Open application
# http://localhost:8000

# 6. View logs
docker logs -f document-api
```

The application is then available at:

```text
Application:
http://localhost:8000

ONLYOFFICE:
http://localhost:8080

MinIO Console:
http://localhost:9001

Redis:
localhost:6379
```
