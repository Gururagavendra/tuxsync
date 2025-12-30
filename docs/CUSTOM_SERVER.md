# Custom Server API

**Status:** WIP (Work in Progress)

If you prefer to host your backups on your own server instead of GitHub Gists, TuxSync supports custom server backends.

## API Specification

Your server should implement these endpoints:

### POST /api/backup

**Description:** Create a new backup

**Request Body:**
```json
{
  "metadata": "version: \"1.0\"\ncreated_at: \"2024-12-28T10:30:00Z\"\ndistro: \"Ubuntu\"\ndistro_version: \"24.04\"\npackage_manager: \"apt\"\npackage_count: 142\npackages:\n  - vim\n  - git\n  - docker.io\nhas_bashrc: true",
  "bashrc": "# .bashrc content..."
}
```

**Note:** The `metadata` field contains YAML-formatted string (matching tuxsync.yaml structure).

**Response:**
```json
{
  "backup_id": "unique-id"
}
```

**Status Code:** 201 Created

---

### GET /api/backup/{backup_id}

**Description:** Retrieve a backup by ID

**Response:**
```json
{
  "metadata": "version: \"1.0\"\ncreated_at: \"2024-12-28T10:30:00Z\"\ndistro: \"Ubuntu\"\ndistro_version: \"24.04\"\npackage_manager: \"apt\"\npackage_count: 142\npackages:\n  - vim\n  - git\n  - docker.io\nhas_bashrc: true",
  "bashrc": "# .bashrc content..."
}
```

**Note:** The `metadata` field is a YAML-formatted string.

**Status Code:** 200 OK

**Error Response:**
```json
{
  "error": "Backup not found"
}
```

**Status Code:** 404 Not Found

---

## Usage

To use a custom server with TuxSync:

```bash
# Backup to custom server
tuxsync backup --server https://your-server.com

# Restore from custom server
tuxsync restore <backup_id> --server https://your-server.com
```

## Security Considerations

- Use HTTPS for all endpoints
- Implement authentication (Bearer tokens, API keys, etc.)
- Validate input data
- Rate limiting recommended
- Consider encryption at rest for sensitive data

## Example Implementation

Coming soon - reference implementation using FastAPI/Flask.

## Contributing

Have suggestions for the custom server API? Please open an issue or PR!
