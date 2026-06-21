# systemd unit hygiene for hermes-gateway

Session lesson: avoid adding modern systemd directives to the production gateway unit without verifying host support. On older hosts, directives such as `RestartSteps=` and `RestartMaxDelaySec=` may produce `Unknown key name ... in section 'Service', ignoring.` The gateway can remain `active`, but the unit is not clean and logs become misleading during incident diagnosis.

## Durable pattern
1. Before editing a unit/drop-in, check the host systemd version:
   ```bash
   systemctl --version | head -1
   ```
2. Back up the unit before every write:
   ```bash
   cp -p /etc/systemd/system/hermes-gateway.service /etc/systemd/system/hermes-gateway.service.bak.$(date +%Y%m%d_%H%M%S)
   ```
3. Prefer supported, simple restart controls. Do not add newer backoff directives unless verified on that host.
4. Validate without restarting first:
   ```bash
   systemd-analyze verify /etc/systemd/system/hermes-gateway.service 2>&1 | tee /tmp/hermes-unit-verify.log
   systemctl daemon-reload 2>&1 | tee /tmp/hermes-daemon-reload.log
   journalctl -b -u hermes-gateway --no-pager | grep -iE 'Unknown key|Failed to parse|bad unit|error' || true
   ```
5. If unsupported-key warnings appear, remove the keys and repeat `daemon-reload` + log grep before reporting the service healthy.
6. Only restart after parsing is clean and a restart is genuinely required. For pure unit-file cleanup, `daemon-reload` is often enough.

## Reporting rule
If user frustration follows a gateway interruption, acknowledge the concrete operator mistake first, then report the verification facts: service active, unsupported directives removed, `daemon-reload` clean, and whether a restart was or was not performed.
