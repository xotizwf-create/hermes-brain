# PostgreSQL Install And Hardening

## Install Checklist

- Install PostgreSQL from the OS package repository unless a project needs a specific version.
- Enable and start the service with systemd.
- Create a project database owner role and database.
- Create an application role with only the permissions it needs.
- Put connection strings in the approved secret store or root-owned env file.

## Hardening Checklist

- Keep `listen_addresses` local unless remote access is required.
- Use firewall rules before allowing remote database access.
- Use strong generated passwords for database roles.
- Avoid `trust` authentication outside local maintenance contexts.
- Keep app roles out of superuser, replication, and create-db permissions unless explicitly required.
- Back up config files before editing `postgresql.conf` or `pg_hba.conf`.

## Verification

```bash
systemctl status postgresql --no-pager
pg_isready
sudo -u postgres psql -c "\\du"
sudo -u postgres psql -c "\\l"
```
