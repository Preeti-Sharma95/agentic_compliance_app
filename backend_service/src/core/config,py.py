from __future__ import annotations

from pathlib import path
from typing import Optional, Dict, Any

from pydantic import Field, SecretStr, PositiveInt,computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parents[2]
DEFAULT_DB_PATH = BASE_DIR/ "app.db"
DEFAULT_LOAD_CONFIF_JSON = BASE_DIR / "src" / "configs" / "load_config_json"

class Settings(BaseSettings):
    app_name: str "internal-audit-bot"
    db_url: str = Field(default=)

    secret_key: SecretStr = Field(default=SecretStr(), alias="secret_key")
    access_token_expire_minutes: PositiveInt = Field(default=60 * 24,alias="acces_token_expire")
    algorithm: str = Field(default="HS256", alias="ALGORITHM")

    default_admin_username: str = Field(default="admin", alias="DEFAULT_ADMIN_USERNAME")
    default_admin_password: str = Field(default="admin", alias="DEFAULT_ADMIN_PASSWORD")

# --- API Key Authentication (for Dormant Analyzer) ---
    API_KEY: str = Field(default="changeme", alias="API_KEY")

    # ✅ Add these two lines (read from .env)
    internal_ip_allowlist: str = Field(default="", alias="INTERNAL_IP_ALLOWLIST")
    server_host_allowlist: str = Field(default="", alias="SERVER_HOST_ALLOWLIST")

    # --- LLM (Groq primary) ---
    groq_api_key: SecretStr = Field(..., alias="GROQ_API_KEY")  # required
    llm_type: str = Field(default="groq", alias="LLM_TYPE")  # selector; default to groq
    model_name: str = Field(default="llama-3.3-70b-versatile", alias="MODEL_NAME")
    temperature: float = Field(default=0.1, alias="TEMPERATURE")
    max_tokens: int = Field(default=1500, alias="MAX_TOKENS")
    streaming: bool = Field(default=False, alias="STREAMING")

    # --- OpenAI / Azure OpenAI (optional; kept for future) ---
    openai_api_key: Optional[SecretStr] = Field(default=None, alias="OPENAI_API_KEY")
    openai_api_base: Optional[str] = Field(default=None, alias="OPENAI_API_BASE")
    openai_api_version: Optional[str] = Field(default="2023-03-15-preview", alias="OPENAI_API_VERSION")
    openai_deployment_name: Optional[str] = Field(default=None, alias="OPENAI_DEPLOYMENT_NAME")

    # For Development Need to Update as part of Config
    DORMANT_AGENT_NAME: Dict[str, str] = {
        "safe_deposit_box_agent": "🏦 Safe Deposit Box Dormancy (Art 2.6)",
        "investment_account_agent": "📈 Investment Account Dormancy (Art 2.3)",
        "fixed_deposit_agent": "💰 Fixed Deposit Dormancy (Art 2.2)",
        "demand_deposit_agent": "💳 Demand Deposit Dormancy (Art 2.1.1)",
        "payment_instruments_agent": "📄 Unclaimed Payment Instruments (Art 2.4)",
        "cb_transfer_agent": "🏛️ Central Bank Transfer Eligibility (Art 8.1-8.2)",
        "article_3_process_agent": "📞 Article 3 Process Requirements",
        "high_value_account_agent": "💎 High-Value Account Analysis",
        "transition_detection_agent": "🔄 Dormant-to-Active Transitions",
    }

    # class Config:
    #     """Pydantic configuration for loading environment variables."""
    #     env_file = ".env"
    #     env_file_encoding = "utf-8"

    # --- Local config file used by the app ---
    load_config_json_file_path: Path = Field(
        default=DEFAULT_LOAD_CONFIG_JSON, alias="LOAD_CONFIG_JSON_FILE_PATH"
    )

    # Pydantic v2 settings
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        populate_by_name=True,  # allow snake_case in code + UPPER_SNAKE env names
    )

    # Convenience flags/projections
    @computed_field  # type: ignore[prop-decorator]
    @property
    def is_sqlite(self) -> bool:
        return self.db_url.startswith("sqlite")

    def sanitized_dict(self) -> Dict[str, Any]:
        """Return non-sensitive config suitable for APIs/logs."""
        return {
            "app_name": self.app_name,
            "db_url": self.db_url,
            "llm": {
                "selected": self.llm_type or "groq",
                "groq_enabled": True,  # groq_api_key is required
                "openai_enabled": bool(self.openai_api_key),
                "model_name": self.model_name,
                "temperature": self.temperature,
                "max_tokens": self.max_tokens,
                "streaming": self.streaming,
            },
            "jwt": {
                "algorithm": self.algorithm,
                "access_token_expire_minutes": self.access_token_expire_minutes,
            },
            "load_config_json_file_path": str(self.load_config_json_file_path),
        }


from functools import lru_cache


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


__all__ = ["Settings", "get_settings"]

if __name__ == "__main__":
    print(get_settings().sanitized_dict())