# Security baseline

Hyttestatus exposes energy information, so security is part of the MVP rather than a later add-on.

- Keep the repository private during early development.
- Never commit `.env`, actual VRM tokens, passwords, or production exports.
- Do not expose the database, Docker socket, or Unraid administration to the public internet.
- Store VRM credentials only in server-side configuration or a secret manager supported by the deployment.
- Use password hashing from a vetted library; never store plaintext passwords.
- Enforce authorization in every API route, including telemetry and history endpoints.
- Guests receive only explicitly published, allowlisted metrics.
- Avoid recording tokens, passwords, signed links, or full sensitive API bodies in application logs.
- Back up the database and periodically verify restoration.
- Provide a way to revoke a user credential.
- Before commercialization, review applicable privacy/data-protection obligations and the chosen hosting arrangement.
