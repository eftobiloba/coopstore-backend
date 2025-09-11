from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database Config
    mongodb_uri: str

    # JWT Config
    secret_key: str
    algorithm: str
    access_token_expire_minutes: int

    api_key: str
    base_url: str

    class Config:
        env_file = ".env"


settings = Settings()
