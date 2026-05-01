# qcpj-crawler

## Overview

This service provides local crawler task execution and task status push-back to backend via websocket.

- Entry API: `POST /run`
- Pause: `POST /task/pause`
- Terminate: `POST /task/terminate`
- WS health: `GET /ws/status`

## New Platform Structure

```text
qcpj-crawler/
  api/
  core/
    executor.py              # dispatch by platform
    worker.py
  platforms/
    registry.py              # platform executor registry
    benben/
      auth.py                # benben login/auth isolation
      crawler.py             # benben crawling implementation
      executor.py            # benben task execution flow
  auth/
    benben/
      auth.json              # platform-specific auth storage
```

## Platform Dispatch

`/run` supports `platform` field. Default: `benben`.

Request example:

```json
{
  "platform": "benben",
  "mode": "batch",
  "taskType": "batch",
  "triggerBy": "frontend",
  "skus": ["SKU001", "SKU002"],
  "city": "武汉",
  "suppliers": ["供应商A", "供应商B"]
}
```

## Auth Isolation

- New auth path: `auth/<platform>/auth.json`
- Current benben auth path: `auth/benben/auth.json`
- Backward compatibility: if `auth/auth.json` exists, benben auth manager will read and migrate it.

## Run

```bash
pip install -r requirements.txt
python main.py
```

## Build exe

```bash
pyinstaller -F -w ./main.py -n bbws
```

## Environment Variables

- `PORT` (default `5000`)
- `DEFAULT_PLATFORM` (default `benben`)
- `AUTH_ROOT_DIR` (default `./auth`)
- `BACKEND_BASE_URL`
- `BACKEND_WS_INGEST_URL`
- `BACKEND_USERNAME`
- `BACKEND_PASSWORD`
- `HTTP_TIMEOUT_SECONDS`
- `HTTP_CONNECT_TIMEOUT_SECONDS`
- `HTTP_RETRY_TIMES`
- `HTTP_RETRY_BACKOFF_SECONDS`
