"""Resource Management: CPU & GPU Allocation, Throttling"""

import asyncio
import logging
import psutil
from dataclasses import dataclass
from typing import Optional
from enum import Enum

logger = logging.getLogger(__name__)


class CPUBudget(str, Enum):
    """CPU percentage budget presets"""
    CONSERVATIVE = "50"  # Use max 50% CPU
    MODERATE = "80"      # Use max 80% CPU
    AGGRESSIVE = "90"    # Use max 90% CPU


@dataclass
class ResourceAllocation:
    """Allocated resources for a research task"""
    max_parallel_fetches: int
    max_sources: int
    cpu_budget_percent: float
    gpu_enabled: bool
    gpu_layers: Optional[int]
    num_threads: int


class CPULimiter:
    """Enforces CPU percentage limits via asyncio semaphore throttling"""

    def __init__(self, cpu_budget_percent: float = 80.0):
        """
        Args:
            cpu_budget_percent: Target CPU usage (0-100)
        """
        self.cpu_budget_percent = min(100, max(1, cpu_budget_percent))
        self._semaphore = asyncio.Semaphore(2)  # Default to 2 concurrent tasks
        self._update_semaphore()

    def _update_semaphore(self):
        """Dynamically adjust semaphore based on CPU budget"""
        cpu_cores = psutil.cpu_count(logical=True) or 8
        # Allocate max concurrent tasks based on CPU budget
        allocated_cores = max(1, min(cpu_cores, int(cpu_cores * self.cpu_budget_percent / 100)))
        self._semaphore = asyncio.Semaphore(allocated_cores)
        logger.info(f"CPU Limiter: budget {self.cpu_budget_percent}%, allocated {allocated_cores} tasks")

    async def acquire(self):
        """Acquire a slot; blocks if CPU budget exhausted"""
        current_cpu = psutil.cpu_percent(interval=0.05)
        if current_cpu > self.cpu_budget_percent:
            await asyncio.sleep(0.2)  # Brief backoff
        
        await self._semaphore.acquire()

    def release(self):
        """Release a slot"""
        self._semaphore.release()

    async def throttled_task(self, coro):
        """Execute coroutine with throttling"""
        await self.acquire()
        try:
            return await coro
        finally:
            self.release()


class GPUAllocator:
    """Manages GPU allocation and offloading parameters"""

    def __init__(self, gpu_info):
        """Args: gpu_info from ConfigManager"""
        self.gpu_info = gpu_info
        self.gpu_available = gpu_info.available if gpu_info else False
        self.gpu_backend = gpu_info.backend if gpu_info else None

    def get_ollama_params(self) -> dict:
        """Return GPU parameters for Ollama model requests"""
        if not self.gpu_available:
            return {"num_gpu": 0}  # CPU-only

        return {
            "num_gpu": self.gpu_info.compute_units,  # Use all available compute units
            "num_thread": psutil.cpu_count(logical=False) or 4,
        }

    def get_env_vars(self) -> dict:
        """Environment variables for Ollama GPU support"""
        if not self.gpu_available:
            return {}

        env = {"OLLAMA_GPU_LAYERS": "auto"}
        
        if self.gpu_backend == "rocm":
            # AMD ROCm environment
            env["ROCM_HOME"] = "/opt/rocm"
            env["HIP_DEVICE_ORDER"] = "PCI"  # Consistent device ordering
        
        return env

    def health_check(self) -> dict:
        """Health status of GPU"""
        if not self.gpu_available:
            return {"status": "unavailable", "reason": "No GPU detected"}

        return {
            "status": "healthy" if self.gpu_info.vram_percent < 95 else "warning",
            "backend": self.gpu_backend,
            "device_id": self.gpu_info.device_id,
            "vram_used_gb": self.gpu_info.vram_used_gb,
            "vram_total_gb": self.gpu_info.vram_total_gb,
            "vram_percent": self.gpu_info.vram_percent,
            "temperature_c": self.gpu_info.temperature_c,
        }


class ResourceManager:
    """Orchestrates CPU & GPU resource allocation for research tasks"""

    def __init__(self, config_manager):
        """Args: config_manager (ConfigManager instance)"""
        self.config = config_manager
        self.cpu_limiter = CPULimiter(cpu_budget_percent=80.0)  # Default
        self.gpu_allocator = GPUAllocator(config_manager.gpu_info)

    def allocate_resources(
        self,
        max_sources: int = 5,
        cpu_budget_percent: float = 80.0,
        gpu_enabled: bool = True
    ) -> ResourceAllocation:
        """Allocate resources based on constraints"""
        
        # Update CPU limiter budget
        self.cpu_limiter.cpu_budget_percent = cpu_budget_percent
        self.cpu_limiter._update_semaphore()

        # Calculate parallel fetches based on CPU cores and budget
        cpu_cores = psutil.cpu_count(logical=True) or 8
        max_parallel = max(1, int(cpu_cores * cpu_budget_percent / 100))

        gpu_ok = gpu_enabled and self.gpu_allocator.gpu_available
        gpu_layers = self.gpu_allocator.gpu_info.compute_units if gpu_ok else 0

        return ResourceAllocation(
            max_parallel_fetches=min(max_parallel, max_sources),
            max_sources=max_sources,
            cpu_budget_percent=cpu_budget_percent,
            gpu_enabled=gpu_ok,
            gpu_layers=gpu_layers if gpu_ok else None,
            num_threads=max(1, cpu_cores // 2)  # Reserve half cores for thinking model
        )

    def get_system_status(self) -> dict:
        """Real-time system resource status"""
        vm = psutil.virtual_memory()
        return {
            "cpu_percent": psutil.cpu_percent(interval=0.1),
            "memory": {
                "used": vm.used / (1024 ** 3),
                "total": vm.total / (1024 ** 3),
                "percent": vm.percent
            },
            "gpu": self.gpu_allocator.health_check(),
            "timestamp": __import__("datetime").datetime.now().isoformat()
        }
