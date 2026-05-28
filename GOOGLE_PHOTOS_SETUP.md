# Google Photos OAuth Setup

Use this for a personal test app. Do not share your Google password or OAuth token.

## 1. Create OAuth Credentials

1. Go to Google Cloud Console.
2. Create a project, or choose an existing project.
3. Enable **Google Photos Library API**.
4. Configure OAuth consent screen:
   - User type: External is fine for personal testing.
   - Publishing status: Testing.
   - Test users: add the Gmail account that owns the Google Photos library.
5. Create credentials:
   - Type: OAuth client ID.
   - Application type: Desktop app.
6. Download the JSON and save it as:

   ```text
   client_secret.json
   ```

   in this project folder.

## 2. Authorize

Run:

```powershell
python .\photo_pipeline.py auth
```

A browser opens. Log in with your Google account and approve the requested Photos upload permission.

The script saves `token.json` locally. Keep it private.

## 3. Google Photos API Limits

This script uses the `photoslibrary.appendonly` scope. It can upload media and place media into albums created by this script/app. It should not be treated as a full Google Photos library manager.

Keep `album_cache.json`. It maps product names to the album IDs created by this script.
