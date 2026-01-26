import json
import os
import platform


def get_obs_websocket_config_path():
    # 获取OBS WebSocket配置文件路径
    if os.name == 'nt':  # Windows
        return os.path.expandvars(r'%APPDATA%\obs-studio\plugin_config\obs-websocket\obs-websocket.ini')
    elif platform.system() == 'Darwin':  # macOS
        return os.path.expanduser(r'~/Library/Application Support/obs-studio/plugin_config/obs-websocket')
    elif platform.system() == 'Linux':  # Linux
        return os.path.expanduser(r'~/.config/obs-studio/plugin_config/obs-websocket')
    else:
        raise NotImplementedError('Unsupported OS')


def enable_obs_websocket():
    if os.name == 'nt':  # Windows
        pass
    elif platform.system() in ('Darwin', 'Linux'):
        # macOS/Linux
        config_path = get_obs_websocket_config_path()

        # Create directory if it doesn't exist
        if not os.path.exists(config_path):
            os.makedirs(config_path, exist_ok=True)
            print(f"Created config directory: {config_path}")

        config = {
            "alerts_enabled": False,
            "auth_required": False,
            "first_load": False,
            "server_enabled": True,
            "server_password": "",
            "server_port": 4455
        }
        config_file = os.path.join(config_path, 'config.json')
        with open(config_file, 'w') as file:
            json.dump(config, file)

        print(f"OBS WebSocket server has been enabled in {config_file}")
    else:
        raise NotImplementedError('Unsupported OS')


if __name__ == "__main__":
    enable_obs_websocket()
