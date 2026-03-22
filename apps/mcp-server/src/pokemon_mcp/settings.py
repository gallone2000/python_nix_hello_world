from pydantic import BaseModel


class Settings(BaseModel):
    pokeapi_base_url: str = "https://pokeapi.co/api/v2"
    http_timeout_seconds: float = 10.0


settings = Settings()