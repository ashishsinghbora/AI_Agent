"""Configuration Management & Hardware Detection"""

import subprocess
import logging
import os
import json
from pathlib import Path
from dataclasses import dataclass
from typing import Optional, Dict, Any
from enum import Enum

logger = logging.getLogger(__name__)


class OutputMode(str, Enum):
    """Research output format modes"""
    QUICK = "quick"      # 1-2 sentences, heuristic-first
    FULL = "full"        # Detailed analysis with all sources
    PAPER = "paper"      # Academic format with citations


class PerformanceProfile(str, Enum):
    """Research speed profiles"""
    ECO = "eco"          # Fast, minimal sources, no thinking
    BALANCED = "balanced"  # Medium, moderate sources, some thinking
    DEEP = "deep"        # Slow, many sources, full thinking


@dataclass
class GPUInfo:
    """GPU Hardware Information"""
    available: bool
    device_id: str
    vram_total_gb: float
    vram_used_gb: float
    vram_percent: float
    temperature_c: float
    compute_units: int
    backend: str  # "rocm" or "cuda" or None


@dataclass
class CPUInfo:
    """CPU Hardware Information"""
    cores: int
    threads: int
    model_name: str
    max_freq_ghz: float
    current_percent: float
    memory_total_gb: float
    memory_available_gb: float


class GPUDetector:
    """Detects and queries GPU availability (AMD ROCm / NVIDIA CUDA)"""

    @staticmethod
    def detect() -> Optional[GPUInfo]:
        """Detect AMD or NVIDIA GPU via rocm-smi or nvidia-smi"""
        # Try ROCm first (AMD)
        gpu_info = GPUDetector._detect_rocm()
        if gpu_info:
            return gpu_info

        # Fallback: try NVIDIA CUDA
        gpu_info = GPUDetector._detect_cuda()
        if gpu_info:
            return gpu_info

        logger.warning("No GPU detected. Using CPU-only mode.")
        return None

    @staticmethod
    def _detect_rocm() -> Optional[GPUInfo]:
        """Detect AMD GPU via rocm-smi"""
        try:
            result = subprocess.run(
                ["rocm-smi", "--json"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                data = json.loads(result.stdout)
                if data and isinstance(data, list) and len(data) > 0:
                    device = data[0]
                    return GPUInfo(
                        available=True,
                        device_id=device.get("gpu_id", "0"),
                        vram_total_gb=float(device.get("vram_total", 4096)) / 1024,
                        vram_used_gb=float(device.get("vram_used", 0)) / 1024,
                        vram_percent=float(device.get("vram_percent", 0)),
                        temperature_c=float(device.get("temperature_edge", 0)),
                        compute_units=int(device.get("compute_units", 8)),
                        backend="rocm"
                    )
        except (subprocess.TimeoutExpired, json.JSONDecodeError, KeyError, FileNotFoundError) as e:
            logger.debug(f"ROCm detection failed: {e}")
        return None

    @staticmethod
    def _detect_cuda() -> Optional[GPUInfo]:
        """Detect NVIDIA GPU via nvidia-smi (optional fallback)"""
        try:
            result = subprocess.run(
                ["nvidia-smi", "--query-gpu=index,memory.total,memory.used,temperature.gpu",
                 "--format=csv,nounits,noheader"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                line = result.stdout.strip().split('\n')[0]
                parts = [p.strip() for p in line.split(',')]
                if len(parts) >= 4:
                    total_mb = float(parts[1])
                    used_mb = float(parts[2])
                    return GPUInfo(
                        available=True,
                        device_id=parts[0],
                        vram_total_gb=total_mb / 1024,
                        vram_used_gb=used_mb / 1024,
                        vram_percent=(used_mb / total_mb * 100) if total_mb > 0 else 0,
                        temperature_c=float(parts[3]),
                        compute_units=0,  # N/A for CUDA
                        backend="cuda"
                    )
        except (subprocess.TimeoutExpired, ValueError, FileNotFoundError, IndexError) as e:
            logger.debug(f"CUDA detection failed: {e}")
        return None


class CPUProfiler:
    """Profiles CPU capabilities and current usage"""

    @staticmethod
    def profile() -> CPUInfo:
        """Get CPU info using psutil"""
        import psutil

        cpu_count = psutil.cpu_count(logical=False) or 4
        cpu_threads = psutil.cpu_count(logical=True) or 8
        cpu_freq = psutil.cpu_freq()
        max_ghz = cpu_freq.max / 1000 if cpu_freq else 2.0
        
        vm = psutil.virtual_memory()
        cpu_percent = psutil.cpu_percent(interval=0.1)

        # Get CPU model name
        model_name = "Unknown"
        try:
            with open("/proc/cpuinfo", "r") as f:
                for line in f:
                    if line.startswith("model name"):
                        model_name = line.split(":", 1)[1].strip()
                        break
        except FileNotFoundError:
            pass

        return CPUInfo(
            cores=cpu_count,
            threads=cpu_threads,
            model_name=model_name,
            max_freq_ghz=max_ghz,
            current_percent=cpu_percent,
            memory_total_gb=vm.total / (1024 ** 3),
            memory_available_gb=vm.available / (1024 ** 3)
        )


class ConfigManager:
    """Central configuration and environment management"""

    def __init__(self, config_path: Optional[str] = None):
        """Initialize configuration from .env and environment"""
        self.config_path = Path(config_path or "/home/ashu/RnD/research_agent/backend/.env")
        self._env = self._load_env()
        self._gpu_info = GPUDetector.detect()
        self._cpu_info = CPUProfiler.profile()

    @staticmethod
    def _load_env() -> Dict[str, str]:
        """Load .env file or use os.environ"""
        try:
            from dotenv import dotenv_values
            env_path = Path("/home/ashu/RnD/research_agent/backend/.env")
            if env_path.exists():
                return dict(dotenv_values(env_path))
        except ImportError:
            pass

        return dict(os.environ)

    # Ollama Configuration
    @property
    def ollama_base_url(self) -> str:
        return self._env.get("OLLAMA_BASE_URL", "http://localhost:11434")

    @property
    def ollama_primary_model(self) -> str:
        return self._env.get("OLLAMA_PRIMARY_MODEL", "deepseek-r1:7b")

    @property
    def ollama_fallback_model(self) -> str:
        return self._env.get("OLLAMA_FALLBACK_MODEL", "gemma2:2b")

    # API Configuration
    @property
    def fastapi_host(self) -> str:
        return self._env.get("FASTAPI_HOST", "0.0.0.0")

    @property
    def fastapi_port(self) -> int:
        return int(self._env.get("FASTAPI_PORT", "8000"))

    @property
    def tavily_api_key(self) -> Optional[str]:
        return self._env.get("TAVILY_API_KEY")

    # Paths
    @property
    def research_notes_path(self) -> Path:
        path = self._env.get("RESEARCH_NOTES_PATH", "/home/ashu/research_notes")
        p = Path(path)
        p.mkdir(parents=True, exist_ok=True)
        return p

    @property
    def chroma_persist_dir(self) -> Path:
        path = self._env.get("CHROMA_PERSIST_DIR", "/tmp/chroma")
        p = Path(path)
        p.mkdir(parents=True, exist_ok=True)
        return p

    @property
    def db_path(self) -> Path:
        """SQLite database for session history"""
        db = self.research_notes_path / "research_agent.db"
        return db

    # Hardware Info (Read-only)
    @property
    def gpu_info(self) -> Optional[GPUInfo]:
        return self._gpu_info

    @property
    def cpu_info(self) -> CPUInfo:
        return self._cpu_info

    def to_dict(self) -> Dict[str, Any]:
        """Export configuration as dictionary for frontend"""
        return {
            "gpu_available": self._gpu_info.available if self._gpu_info else False,
            "gpu_backend": self._gpu_info.backend if self._gpu_info else None,
            "gpu_vram_total_gb": self._gpu_info.vram_total_gb if self._gpu_info else 0,
            "cpu_cores": self._cpu_info.cores,
            "cpu_model": self._cpu_info.model_name,
            "memory_total_gb": self._cpu_info.memory_total_gb,
            "ollama_models": {
                "thinking": self.ollama_primary_model,
                "fast": self.ollama_fallback_model
            }
        }
