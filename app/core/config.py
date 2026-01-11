from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str
    DEBUG: bool = False
    DATABASE_URL: str

    GOOGLE_CLIENT_ID: str
    GOOGLE_CLIENT_SECRET: str
    GOOGLE_REDIRECT_URI: str

    ACCESS_TOKEN_SECRET: str
    REFRESH_TOKEN_SECRET: str

    class Config:
        env_file = ".env"


settings = Settings()  # type: ignore
