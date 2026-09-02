# Database layer

`supabase_client.py` is the only backend module that talks to Supabase. It requires `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY` in the local environment.

The service-role key must stay on the backend and must never be sent to the browser.
