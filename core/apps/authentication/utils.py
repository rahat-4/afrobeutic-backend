def get_user_media_path_prefix(instance: object, filename: str) -> str:
    return f"user/{instance.email}/{filename}"
