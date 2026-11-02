# Deploy GATE Prep Hub to Render

This deployment bundle is for the FastAPI + SQLite version of GATE Prep Hub.

## Important
- `render.yaml` provisions a Render Web Service and a 1 GB persistent disk.
- The Blueprint uses Render's Starter web-service plan because persistent disks require a paid service. Check current Render pricing before approving.
- The database is stored at `/var/data/gateprep.db`, outside the application release directory, so it survives deploys and restarts.
- This app is currently a single-workspace application without user login or per-user data isolation. Do not use it for sensitive personal documents or open public uploads until authentication, authorization, upload scanning, rate limiting and backups are added.

## Steps
1. In your GitHub repository, replace the root `app.py` with the `app.py` in this bundle.
2. Add `render.yaml` and make sure `requirements.txt` is in the repository root.
3. Commit and push these files to the default branch.
4. Sign in to Render and connect your GitHub account.
5. Choose **New → Blueprint**, select `sahith8639/GATE-PREP-HUB`, and approve the Blueprint.
6. Render will build with `pip install -r requirements.txt` and run:
   `uvicorn app:app --host 0.0.0.0 --port $PORT`
7. After deployment, open the generated `onrender.com` URL and verify `/api/health` returns `{"status":"ok", ...}`.

## Existing database migration
If your current local `data/gateprep.db` contains personal notes, tasks, progress or uploads, back it up before deploying. A new Render disk starts with a newly seeded database. The existing local SQLite file is not automatically copied to Render. Import/migration should be done securely after deployment.

## Security before public multi-user launch
The current app has no authentication and exposes its workspace APIs publicly. Treat the first deployment as a private demo until authentication and per-user ownership controls are implemented. Do not upload sensitive files.
