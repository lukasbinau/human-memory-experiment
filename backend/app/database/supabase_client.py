import os

from supabase import Client, create_client


class SupabaseNotConfiguredError(RuntimeError):
    pass


def get_supabase_client() -> Client:
    url = os.getenv("SUPABASE_URL")
    service_role_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

    if not url or not service_role_key:
        raise SupabaseNotConfiguredError(
            "Set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY before using Supabase."
        )

    return create_client(url, service_role_key)


def save_session(session: dict) -> dict:
    client = get_supabase_client()
    result = client.table("sessions").insert(session).execute()
    return result.data[0]


def save_trial(trial: dict) -> dict:
    client = get_supabase_client()
    result = client.table("trials").upsert(
        trial,
        on_conflict="session_id,trial_number",
    ).execute()
    return result.data[0]


def get_session(session_id: str) -> dict | None:
    client = get_supabase_client()
    result = client.table("sessions").select("*").eq("id", session_id).limit(1).execute()
    return result.data[0] if result.data else None


def get_trials(session_id: str) -> list[dict]:
    client = get_supabase_client()
    result = (
        client.table("trials")
        .select("*")
        .eq("session_id", session_id)
        .order("trial_number")
        .execute()
    )
    return result.data

def get_next_trial_number(session_id: str) -> int:
    client = get_supabase_client()
    result = (
        client.table("trials")
        .select("trial_number")
        .eq("session_id", session_id)
        .order("trial_number", desc=True)
        .limit(1)
        .execute()
    )
    return result.data[0]["trial_number"] + 1 if result.data else 1


def complete_session(session_id: str) -> dict:
    from datetime import datetime, timezone

    client = get_supabase_client()
    result = (
        client.table("sessions")
        .update({"status": "completed", "completed_at": datetime.now(timezone.utc).isoformat()})
        .eq("id", session_id)
        .execute()
    )
    return result.data[0]
