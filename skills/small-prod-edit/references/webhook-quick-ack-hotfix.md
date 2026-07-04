# Webhook quick-ACK hotfix pattern

Use this reference when a live bot/webhook looks “down” during provider/network degradation, but the service itself is healthy.

## Symptom
- Reverse proxy/application is up and normal health checks pass.
- Incoming webhook requests from the upstream platform sometimes end as client-aborted responses (for example nginx `499`) or upstream retries.
- Logs show the handler eventually works, but the platform times out before it receives the HTTP response.

## Durable lesson
Webhook handlers should acknowledge receipt before any non-essential external network call. Cosmetic calls such as reactions, typing indicators, “read” marks, command registration, file downloads, OCR, or model calls must run after the ACK in a background worker/queue.

Bad shape:
```python
# Before returning HTTP 200 to the platform
call_platform_reaction_api(...)
call_platform_typing_api(...)
threading.Thread(target=process_message, ...).start()
return {"accepted": True}
```

Good shape:
```python
def worker():
    call_platform_reaction_api(...)   # cosmetic, best-effort
    call_platform_typing_api(...)
    process_message(...)

threading.Thread(target=worker, daemon=True).start()
return {"accepted": True}
```

## Verification
1. Syntax/import check before restart.
2. Restart only the affected service.
3. Confirm the public webhook endpoint returns 200 quickly (sub-second; ideally tens of milliseconds for readiness GET/empty request).
4. Check application logs for new exceptions after restart.
5. Check access logs for no new client-aborted webhook entries after the fix.

## Pitfalls
- Do not interpret a transient external API delay as app overload if CPU/RAM and local service health are normal.
- A failed health check immediately after restart can just be the app still binding the port; verify service status/logs before rollback.
- Keep the pre-ACK path local and tiny: parse enough to start the worker, then return.