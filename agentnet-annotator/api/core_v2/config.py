"""Configuration management for core v2 modules."""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional
from pathlib import Path
import os


@dataclass
class RecordingConfig:
    """Configuration for recording functionality."""
    natural_scrolling: bool = True
    generate_window_a11y: bool = False
    generate_element_a11y: bool = True
    max_events_per_file: int = 1000
    compression_enabled: bool = True
    video_quality: str = "medium"  # low, medium, high
    frame_rate: int = 30
    
    # File paths
    recording_dir: Optional[Path] = None
    temp_dir: Optional[Path] = None
    
    def __post_init__(self):
        if self.recording_dir is None:
            self.recording_dir = Path.home() / "Documents" / "AgentNet" / "recordings"
        if self.temp_dir is None:
            self.temp_dir = Path.home() / "Documents" / "AgentNet" / "temp"


@dataclass
class AccessibilityConfig:
    """Configuration for accessibility tree functionality."""
    max_tree_depth: int = 10
    include_invisible_elements: bool = False
    cache_tree_results: bool = True
    cache_timeout_seconds: int = 30
    element_timeout_ms: int = 5000
    parallel_processing: bool = True
    max_workers: int = 4


@dataclass
class VideoConfig:
    """Configuration for video processing."""
    output_format: str = "mp4"
    codec: str = "h264"
    bitrate: str = "2M"
    scale: Optional[str] = None  # e.g., "1920:1080"
    fps: int = 30
    quality: int = 23  # CRF value for h264


@dataclass 
class FileConfig:
    """Configuration for file operations."""
    encryption_enabled: bool = True
    compression_level: int = 6  # 1-9
    backup_enabled: bool = True
    max_file_size_mb: int = 100
    auto_cleanup_days: int = 30
    
    # Buffer sizes
    read_buffer_size: int = 8192
    write_buffer_size: int = 8192


@dataclass
class PlatformConfig:
    """Platform-specific configuration."""
    notification_enabled: bool = True
    system_integration: bool = True
    respect_system_settings: bool = True
    
    # Platform detection
    force_platform: Optional[str] = None  # "darwin", "windows", "linux"


@dataclass
class CoreConfig:
    """Main configuration container for core v2."""
    recording: RecordingConfig = field(default_factory=RecordingConfig)
    accessibility: AccessibilityConfig = field(default_factory=AccessibilityConfig)
    video: VideoConfig = field(default_factory=VideoConfig)
    files: FileConfig = field(default_factory=FileConfig)
    platform: PlatformConfig = field(default_factory=PlatformConfig)
    
    # Global settings
    debug_mode: bool = False
    log_level: str = "INFO"
    performance_monitoring: bool = False
    
    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> 'CoreConfig':
        """Create CoreConfig from dictionary."""
        config = cls()
        
        if 'recording' in config_dict:
            config.recording = RecordingConfig(**config_dict['recording'])
        if 'accessibility' in config_dict:
            config.accessibility = AccessibilityConfig(**config_dict['accessibility'])
        if 'video' in config_dict:
            config.video = VideoConfig(**config_dict['video'])
        if 'files' in config_dict:
            config.files = FileConfig(**config_dict['files'])
        if 'platform' in config_dict:
            config.platform = PlatformConfig(**config_dict['platform'])
            
        # Global settings
        for key in ['debug_mode', 'log_level', 'performance_monitoring']:
            if key in config_dict:
                setattr(config, key, config_dict[key])
        
        return config
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert CoreConfig to dictionary."""
        return {
            'recording': self.recording.__dict__,
            'accessibility': self.accessibility.__dict__,
            'video': self.video.__dict__,
            'files': self.files.__dict__,
            'platform': self.platform.__dict__,
            'debug_mode': self.debug_mode,
            'log_level': self.log_level,
            'performance_monitoring': self.performance_monitoring,
        }
    
    def ensure_directories(self) -> None:
        """Ensure all required directories exist."""
        directories = [
            self.recording.recording_dir,
            self.recording.temp_dir,
        ]
        
        for directory in directories:
            if directory:
                directory.mkdir(parents=True, exist_ok=True)


# Global configuration instance
_global_config: Optional[CoreConfig] = None


def get_config() -> CoreConfig:
    """Get the global configuration instance."""
    global _global_config
    if _global_config is None:
        _global_config = CoreConfig()
        _global_config.ensure_directories()
    return _global_config


def set_config(config: CoreConfig) -> None:
    """Set the global configuration instance."""
    global _global_config
    _global_config = config
    _global_config.ensure_directories()


def reset_config() -> None:
    """Reset configuration to defaults."""
    global _global_config
    _global_config = None