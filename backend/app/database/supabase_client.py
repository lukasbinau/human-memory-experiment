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
    result = client.table("trials").insert(trial).execute()
    return result.data[0]
