from __future__ import annotations
import os
from typing import Optional
from pydantic import Field, AliasChoices
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)

    MICROSOFT_APP_ID: str = Field(
        validation_alias=AliasChoices("MICROSOFT_APP_ID", "MicrosoftAppId")
    )
    MICROSOFT_APP_PASSWORD: str = Field(
        validation_alias=AliasChoices("MICROSOFT_APP_PASSWORD", "MicrosoftAppPassword")
    )
    MICROSOFT_APP_TENANT_ID: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("MICROSOFT_APP_TENANT_ID", "MicrosoftAppTenantId"),
    )
    MICROSOFT_APP_OAUTH_SCOPE: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices(
            "MICROSOFT_APP_OAUTH_SCOPE",
            "MicrosoftAppOAuthScope",
            "MicrosoftAppScope",
        ),
    )
    BOT_DISPLAY_NAME: str = Field(default="bot de Teams")
    BOT_DEFAULT_REPLY: str = Field(default="Hola, soy tu bot de Teams.")
    PROACTIVE_DEFAULT_MESSAGE: str = Field(default="Hola, este es un mensaje proactivo.")
    PROACTIVE_API_KEY: Optional[str] = Field(default=None)
    PORT: int = int(os.getenv("PORT", "8000"))
    ENV: str = os.getenv("ENV", "prod")

settings = Settings()
