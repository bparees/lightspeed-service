import traceback
import os
import dotenv
from pydantic import BaseModel
from typing import List, Optional, Dict
import yaml

from .logger import Logger

class ModelConfig(BaseModel):
    name: str = None
    url: str = None
    credential_path: str = None

    def __init__(self,data):
        super().__init__()
        if data is None:
            raise Exception(f"model config is missing for model {data['name']}")
        self.name = data.get("name",None)
        self.url = data.get("url",None)
        self.credential_path = data.get("credential_path",None)

class ProviderConfig(BaseModel):
    name: str = None
    url: str = None
    credential_path: str = None
    models: Dict[str, ModelConfig] = {}

    def __init__(self,data):
        super().__init__()
        if data is None:
            return
        self.name = data.get("name",None)
        self.url = data.get("url",None)
        self.credential_path = data.get("credential_path",None)
        if data.get("models",None) is None or len(data["models"]) == 0:
            raise Exception(f"no models configured for provider {data['name']}")
        for m in data["models"]:
            if m.get("name",None) is None:
                raise Exception("model name is missing")
            model=ModelConfig(m)
            self.models[m["name"]] = model


class LLMConfig(BaseModel):
    providers: Dict[str,ProviderConfig] = {}

    def __init__(self,data: dict):
        super().__init__()
        if data is None or len(data) == 0:
            raise Exception("no llm providers configured")
        for p in data:
            if p.get("name",None) is None:
                raise Exception("provider name is missing")
            provider=ProviderConfig(p)
            self.providers[p["name"]] = provider

class RedisConfig(BaseModel):
    host: str = None
    port: int = None
    max_memory: str = None
    max_memory_policy: str = None

    def __init__(self,data):
        super().__init__()
        if data is None:
            return
        self.host = data.get("host",None)
        self.port = data.get("port",None)
        self.max_memory = data.get("max_memory",None)
        self.max_memory_policy = data.get("max_memory_policy",None)


class MemoryConfig(BaseModel):
    max_entries: int = None

    def __init__(self,data):
        super().__init__()
        if data is None:
            return
        self.max_entries = data.get("max_entries",None)

class ConversationCacheConfig(BaseModel):
    type: str = None
    redis: Optional[RedisConfig] = None
    memory: Optional[MemoryConfig] = None

    def __init__(self,data):
        super().__init__()
        if data is None:
            return
        self.type = data.get("type",None)
        if self.type == "redis":
            if data.get("redis",None) is None:
                raise Exception("redis config is missing")
            self.redis = RedisConfig(data.get("redis",None))
        elif self.type == "memory":
            if data.get("memory",None) is None:
                raise Exception("memory config is missing")
            self.memory = MemoryConfig(data.get("memory",None))

class LoggerConfig(BaseModel):
    level: str = None
    filename: str = None

    def __init__(self,data):
        super().__init__()
        if data is None:
            return
        self.level = data.get("level",None)
        self.filename = data.get("filename",None)

class OLSConfig(BaseModel):
    enable_debug_ui: bool = False
    default_model: str = None    
    classifier_model: str = None
    conversation_cache: ConversationCacheConfig = None
    logger_config: LoggerConfig = None

    def __init__(self, data):
        super().__init__()
        if data is None:
            return
        self.default_model=data.get("default_model",None)
        self.enable_debug_ui = data.get("enable_debug_ui", False)
        self.conversation_cache = ConversationCacheConfig(data.get("conversation_cache",None))
        self.logger_config = LoggerConfig(data.get("logger_config",None))


class Config:
    llm_config: LLMConfig = None
    ols_config: OLSConfig = None

    def __init__(self, data):
        super().__init__()
        if data is None:
            return
        self.llm_config = LLMConfig(data.get("llm_providers",None))
        self.ols_config = OLSConfig(data.get("ols_config",None))

    def validate(self):
        if self.llm_config is None:
            raise Exception("no llm config found")
        if self.llm_config.providers is None or len(self.llm_config.providers) == 0:
            raise Exception("no llm providers found")
        if self.ols_config is None:
            raise Exception("no ols config found")
        if self.ols_config.default_model is None:
            raise Exception("default model is not set")
        if self.ols_config.classifier_model is None:
            raise Exception("classifier model is not set")
        if self.ols_config.conversation_cache is None:
            raise Exception("conversation cache is not set")
        if self.ols_config.logger_config is None:
            raise Exception("logger config is not set")
        


def load_config(config_file):
    try:
        f=open(config_file, "r")
        data = yaml.safe_load(f)
        return Config(data)
    except Exception as e:
        print(f"Failed to load config file {config_file.name}: {str(e)}")
        print(traceback.format_exc())
        exit(1)



class DeadConfig:
    def __init__(self, logger=None):
        # Load the dotenv configuration & set defaults
        dotenv.load_dotenv()
        self.set_defaults()

        # Parse arguments & set logger
        self.logger = (
            logger
            if logger
            else Logger(logger_name="default", logfile=self.logfile).logger
        )

    def set_defaults(self):
        """
        Set default global required parameters if none was found
        """
        # set logs file. Disable logging to file when not defined.
        self.logfile = os.getenv("OLS_LOGFILE", None)

        # enable local ui?
        self.enable_ui = (
            True if os.getenv("OLS_ENABLE_UI", "True").lower() == "true" else False
        )

        # set default LLM model
        self.base_completion_model = os.getenv(
            "BASE_COMPLETION_MODEL", "ibm/granite-20b-instruct-v1"
        )
