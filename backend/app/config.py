from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql://logpulse:logpulse@db:5432/logpulse"
    pool_min_size: int = 2
    pool_max_size: int = 10

    class Config:
        env_file = ".env"


settings = Settings()
