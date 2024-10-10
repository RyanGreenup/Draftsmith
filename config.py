import yaml
import os
from xdg import BaseDirectory
import shutil
from pprint import pprint


class Config:
    def __init__(self):
        self.app_name = "draftsmith"
        # Get XDG dirs
        self.xdg_config_home = BaseDirectory.xdg_config_home
        self.xdg_data_home = BaseDirectory.xdg_data_home
        self.config_dir = os.path.join(self.xdg_config_home, self.app_name)
        self.config_file = os.path.join(self.config_dir, "config.yaml")
        self.data_home = os.path.join(self.xdg_data_home, self.app_name)

        # CSS
        self.default_style = "github-pandoc.css"
        self.default_style_path = os.path.join(
            os.path.dirname(__file__), self.default_style
        )

        self.config = self.get_config()

    def default_config(self):
        return {
            "editor": "vim",
            "local_katex": True,
            "allow_remote_content": False,
            "link_revisits_tab": False,
            "css_path": os.path.abspath(self.default_style_path),
        }

    def write_default_config(self):
        if not os.path.exists(self.config_dir):
            os.makedirs(self.config_dir)
        with open(self.config_file, "w") as f:
            yaml.dump(self.default_config(), f)

        shutil.copy(self.default_style_path, self.data_home)

    def load_config(self):
        with open(self.config_file) as f:
            return yaml.safe_load(f)

    def get_config(self):
        if not os.path.exists(self.config_file):
            self.write_default_config()
        return self.load_config()

    def __repr__(self):
        conf = self.config.copy()
        # Dump to yaml
        return yaml.dump(conf)


if __name__ == "__main__":
    config = Config()
    print(config)
