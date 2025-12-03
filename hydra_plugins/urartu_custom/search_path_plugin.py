from hydra.core.config_search_path import ConfigSearchPath
from hydra.plugins.search_path_plugin import SearchPathPlugin
from pathlib import Path
import os
import getpass

class LLMRoleplaySearchPathPlugin(SearchPathPlugin):
    def manipulate_search_path(self, search_path: ConfigSearchPath) -> None:
        # Assuming we run from the repo root
        cwd = Path.cwd()

        # Add llm_roleplay/configs_andreii explicitly if it exists

        try:
            current_user = getpass.getuser()
        except Exception:
            current_user = "unknown"

        # Check if we are in the repo root and correct dirs exist
        # We look for llm_roleplay/configs_andreii
        # Note: configs_andreii contains configs for user 'andreii', but in this codebase
        # it seems to be the shared location for these experiments.

        # Also support dynamic user configs if they exist
        if (cwd / "llm_roleplay").exists():
            search_path.append(provider="llm-roleplay", path=f"file://{cwd}/llm_roleplay/configs_andreii")
            search_path.append(provider="llm-roleplay", path=f"file://{cwd}/llm_roleplay/configs_{current_user}")
            search_path.append(provider="llm-roleplay", path=f"file://{cwd}/llm_roleplay/configs")
