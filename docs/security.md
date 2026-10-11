# Security baseline

Hyttestatus may expose camera images and energy information to multiple users, so security is part of the MVP rather than a later add-on.

- Keep the repository private during early development.
- Never commit `.env`, actual VRM tokens, passwords, images from the cabin, or production exports.
- Use HTTPS for external browser access and authenticated uploads.
- Do not expose the camera, Frigate, database, Docker socket, or Unraid administration to the public internet.
- Store VRM credentials only in server-side configuration or a secret manager supported by the deployment.
- Use password hashing from a vetted library; never store plaintext passwords.
- Enforce authorization in every API route, including media URLs and history endpoints.
- Guests receive only explicitly published media and allowlisted metrics.
- Avoid recording tokens, passwords, signed links, or full sensitive API bodies in application logs.
- Configure retention for images and clips, and document it to site owners.
- Back up the database and media and periodically verify restoration.
- Provide a way to revoke a user or upload credential.
- Before commercialization, review applicable privacy/data-protection obligations and the chosen hosting arrangement.
