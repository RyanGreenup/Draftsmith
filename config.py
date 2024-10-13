import yaml
import shutil
from pathlib import Path
from xdg import BaseDirectory


class Config:
    """
    A class to handle the configuration settings for the Draftsmith application.
    It reads from or initializes a YAML configuration file and sets up necessary directories.
    """

    DEFAULT_STYLE = "github-pandoc.css"

    def __init__(self):
        self.app_name = "draftsmith"

        # Get XDG directories
        self.xdg_config_home = Path(BaseDirectory.xdg_config_home)
        self.xdg_data_home = Path(BaseDirectory.xdg_data_home)

        self.config_dir = self.xdg_config_home / self.app_name
        self.config_file = self.config_dir / "config.yaml"
        self.data_home = self.xdg_data_home / self.app_name

        # Default CSS path
        self.default_style_path = Path(__file__).parent / "assets" / "styles"

        # Load or initialize configuration
        self.config = self.get_config()

    @staticmethod
    def default_config(css_path):
        """
        Returns the default configuration dictionary.
        """
        return {
            "editor": "vim",
            "remote_katex": True,
            "disable_remote_content": False,
            "link_revisits_tab": False,
            # Directory containing CSS files
            "css_path": str(css_path.resolve()),
            # Defaults to a Side by Side Preview (Toggle with Ctrl-G)
            "no_side_by_side": True,
            "insert_wikilinks": False,
            "openai_api_server": "http://localhost:11434",
            "use_relative_paths": False,  # Not yet implemented
            "notification_timeout": 500,
            "fonts": {
                "editor": {
                    "mono": "fira code",
                    "sans": "fira sans",
                    "serif": "fira sans",
                }
            },
        }

    def write_default_config(self):
        """
        Writes the default configuration to the YAML file and copies the default CSS style.
        """
        # Ensure the configuration directory exists
        self.config_dir.mkdir(parents=True, exist_ok=True)

        # Write default configuration to the config file
        with self.config_file.open("w") as f:
            yaml.dump(self.default_config(self.default_style_path), f)

        # Ensure the data home directory exists
        self.data_home.mkdir(parents=True, exist_ok=True)

        # Copy the default CSS directory underneath the data home directory
        shutil.copytree(self.default_style_path, self.data_home / "styles")

    def load_config(self):
        """
        Loads the configuration from the YAML file.
        """
        try:
            with self.config_file.open() as f:
                return yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise ValueError(f"Error parsing the configuration file: {e}")

    def get_config(self):
        """
        Retrieves the current configuration, writing a default one if necessary.
        """
        if not self.config_file.exists():
            self.write_default_config()
        config = self.load_config()
        default_config = self.default_config(self.default_style_path)
        # Update config with any missing defaults
        for key, value in default_config.items():
            config.setdefault(key, value)
        return config

    def __repr__(self):
        """
        Returns a YAML-formatted string representation of the configuration.
        """
        return yaml.dump(self.config, default_flow_style=False)


if __name__ == "__main__":
    config = Config()
    print(config)
