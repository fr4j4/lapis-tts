"""
Benchmark API endpoints for LAPIS TTS.
Provides system metrics, benchmark execution, and historical results.
"""
import os
import time
import uuid
import json
import logging
import psutil
import threading
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List
from dataclasses import dataclass, field, asdict
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/benchmark", tags=["benchmark"])

BENCHMARK_DIR = Path(__file__).parent.parent.parent / "benchmark-results"
BENCHMARK_DIR.mkdir(exist_ok=True)


@dataclass
class SystemInfo:
    hostname: str
    cpu_cores: int
    cpu_model: str
    cpu_freq_mhz: float
    ram_total_gb: float
    ram_available_gb: float
    os_name: str
    os_version: str
    python_version: str
    piper_version: str
    onnxruntime_version: str
    process_pid: int
    process_memory_mb: float


@dataclass
class VoiceResult:
    voice_id: str
    latency_ms: float
    synthesis_time_ms: float
    model_load_time_ms: float
    audio_size_bytes: int
    audio_duration_ms: float
    audio_duration_sec: float
    chars_per_second: float
    text_chars: int
    text_words: int
    text_sentences: int
    seconds_per_char: float
    success: bool
    error: Optional[str] = None


@dataclass
class BenchmarkResult:
    test_id: str
    timestamp: str
    system_info: SystemInfo
    test_config: Dict
    results: List[VoiceResult]
    aggregate: Dict


class BenchmarkRunner:
    """Handles benchmark execution and result storage."""

    def __init__(self):
        self._lock = threading.Lock()
        self._current_test: Optional[BenchmarkResult] = None
        self._progress_callback = None

    def set_progress_callback(self, callback):
        self._progress_callback = callback

    def get_system_info(self) -> SystemInfo:
        """Gather current system information."""
        import socket
        
        cpu_count = psutil.cpu_count(logical=True)
        cpu_physical = psutil.cpu_count(logical=False)
        
        try:
            cpu_model = psutil.cpu_freq()._current if psutil.cpu_freq() else "Unknown"
        except:
            cpu_model = "Unknown"
        
        try:
            cpu_freq = psutil.cpu_freq().current if psutil.cpu_freq() else 0
        except:
            cpu_freq = 0

        mem = psutil.virtual_memory()
        
        try:
            import platform
            os_name = platform.system()
            os_version = platform.version()
        except:
            os_name = "Unknown"
            os_version = "Unknown"

        process = psutil.Process()
        
        # Get versions
        piper_version = "Unknown"
        onnxruntime_version = "Unknown"
        try:
            import piper
            piper_version = getattr(piper, '__version__', 'unknown')
        except:
            pass
        try:
            import onnxruntime
            onnxruntime_version = getattr(onnxruntime, '__version__', 'unknown')
        except:
            pass
        
        return SystemInfo(
            hostname=socket.gethostname(),
            cpu_cores=cpu_physical or cpu_count,
            cpu_model=cpu_model,
            cpu_freq_mhz=int(cpu_freq) if cpu_freq else 0,
            ram_total_gb=round(mem.total / (1024**3), 2),
            ram_available_gb=round(mem.available / (1024**3), 2),
            os_name=os_name,
            os_version=os_version,
            python_version=f"{os.sys.version_info.major}.{os.sys.version_info.minor}",
            piper_version=piper_version,
            onnxruntime_version=onnxruntime_version,
            process_pid=process.pid,
            process_memory_mb=round(process.memory_info().rss / (1024**2), 2),
        )

    def get_process_memory(self) -> float:
        """Get current process memory in MB."""
        try:
            process = psutil.Process()
            return round(process.memory_info().rss / (1024**2), 2)
        except:
            return 0

    def run_benchmark(
        self,
        text: str,
        voices: List[str],
        repetitions: int = 1,
        tts_engine=None,
        voice_config_manager=None,
    ) -> BenchmarkResult:
        """Execute benchmark across specified voices."""
        
        test_id = str(uuid.uuid4())[:8]
        timestamp = datetime.now().isoformat()
        system_info = self.get_system_info()
        
        results: List[VoiceResult] = []
        
        voice_list = voices
        if not voice_list:
            voice_list = [v["voice_id"] for v in voice_config_manager.list_voices()]
        
        total_tests = len(voice_list) * repetitions
        current_test = 0
        
        with self._lock:
            self._current_test = BenchmarkResult(
                test_id=test_id,
                timestamp=timestamp,
                system_info=system_info,
                test_config={"text": text, "voices": voice_list, "repetitions": repetitions},
                results=[],
                aggregate={},
            )
        
        logger.info(f"Starting benchmark {test_id} with {len(voice_list)} voices x {repetitions} reps")
        
        for voice_id in voice_list:
            for rep in range(repetitions):
                current_test += 1
                
                if self._progress_callback:
                    self._progress_callback({
                        "voice_id": voice_id,
                        "repetition": rep + 1,
                        "current": current_test,
                        "total": total_tests,
                    })
                
                voice_result = self._run_single_test(
                    voice_id, text, tts_engine, voice_config_manager
                )
                results.append(voice_result)
                
                with self._lock:
                    self._current_test.results.append(voice_result)
        
        aggregate = self._compute_aggregate(results)
        
        benchmark_result = BenchmarkResult(
            test_id=test_id,
            timestamp=timestamp,
            system_info=system_info,
            test_config={"text": text, "voices": voice_list, "repetitions": repetitions},
            results=results,
            aggregate=aggregate,
        )
        
        self._save_result(benchmark_result)
        logger.info(f"Benchmark {test_id} completed. Avg latency: {aggregate.get('avg_latency_ms', 0):.2f}ms")
        
        return benchmark_result

    def _run_single_test(
        self,
        voice_id: str,
        text: str,
        tts_engine,
        voice_config_manager,
    ) -> VoiceResult:
        """Run a single benchmark test for one voice."""
        
        start_time = time.perf_counter()
        synthesis_start = start_time
        
        # Calculate text metrics
        text_chars = len(text)
        text_words = len(text.split())
        text_sentences = text.count('.') + text.count('!') + text.count('?')
        if text_sentences == 0 and text_chars > 0:
            text_sentences = 1
        
        try:
            voice_config = voice_config_manager.get_voice(voice_id)
            if not voice_config:
                return VoiceResult(
                    voice_id=voice_id,
                    latency_ms=0,
                    synthesis_time_ms=0,
                    model_load_time_ms=0,
                    audio_size_bytes=0,
                    audio_duration_ms=0,
                    audio_duration_sec=0,
                    chars_per_second=0,
                    text_chars=0,
                    text_words=0,
                    text_sentences=0,
                    seconds_per_char=0,
                    success=False,
                    error="Voice not found",
                )
            
            voice_model = voice_config["model"]
            params = voice_config.get("params", {})
            
            # Track model load time
            load_start = time.perf_counter()
            was_loaded = voice_model in tts_engine._voices
            audio_bytes = tts_engine.synthesize(
                voice_model,
                text,
                length_scale=params.get("length_scale", 1.0),
                noise_scale=params.get("noise_scale", 0.667),
                noise_w_scale=params.get("noise_w_scale", 0.8),
            )
            load_end = time.perf_counter()
            
            model_load_time = 0 if was_loaded else (load_end - load_start) * 1000
            
            synthesis_end = time.perf_counter()
            latency = (synthesis_end - start_time) * 1000
            synthesis_time = (synthesis_end - load_start) * 1000
            
            audio_size = len(audio_bytes)
            chars_per_sec = (text_chars / synthesis_time * 1000) if synthesis_time > 0 else 0
            
            audio_duration_ms = self._get_audio_duration_ms(audio_bytes)
            audio_duration_sec = audio_duration_ms / 1000
            seconds_per_char = audio_duration_sec / text_chars if text_chars > 0 else 0
            
            return VoiceResult(
                voice_id=voice_id,
                latency_ms=round(latency, 2),
                synthesis_time_ms=round(synthesis_time, 2),
                model_load_time_ms=round(model_load_time, 2),
                audio_size_bytes=audio_size,
                audio_duration_ms=round(audio_duration_ms, 2),
                audio_duration_sec=round(audio_duration_sec, 3),
                chars_per_second=round(chars_per_sec, 2),
                text_chars=text_chars,
                text_words=text_words,
                text_sentences=text_sentences,
                seconds_per_char=round(seconds_per_char, 4),
                success=True,
            )
            
        except Exception as e:
            end_time = time.perf_counter()
            latency = (end_time - start_time) * 1000
            
            logger.error(f"Benchmark error for {voice_id}: {e}")
            
            return VoiceResult(
                voice_id=voice_id,
                latency_ms=round(latency, 2),
                synthesis_time_ms=0,
                model_load_time_ms=0,
                audio_size_bytes=0,
                audio_duration_ms=0,
                audio_duration_sec=0,
                chars_per_second=0,
                text_chars=text_chars,
                text_words=text_words,
                text_sentences=text_sentences,
                seconds_per_char=0,
                success=False,
                error=str(e),
            )

    def _get_audio_duration_ms(self, audio_bytes: bytes) -> float:
        """Calculate audio duration from WAV bytes."""
        try:
            import wave
            import io
            with wave.open(io.BytesIO(audio_bytes), 'rb') as wf:
                frames = wf.getnframes()
                rate = wf.getframerate()
                return (frames / rate * 1000) if rate > 0 else 0
        except:
            return 0

    def _compute_aggregate(self, results: List[VoiceResult]) -> Dict:
        """Compute aggregate statistics."""
        successful = [r for r in results if r.success]
        
        if not successful:
            return {
                "total_tests": len(results),
                "successful": 0,
                "failed": len(results),
                "avg_latency_ms": 0,
                "avg_synthesis_time_ms": 0,
                "avg_model_load_time_ms": 0,
                "avg_audio_size_bytes": 0,
                "avg_audio_duration_sec": 0,
                "avg_chars_per_second": 0,
                "min_latency_ms": 0,
                "max_latency_ms": 0,
            }
        
        latencies = [r.latency_ms for r in successful]
        synthesis_times = [r.synthesis_time_ms for r in successful]
        model_load_times = [r.model_load_time_ms for r in successful]
        audio_sizes = [r.audio_size_bytes for r in successful]
        audio_durations = [r.audio_duration_sec for r in successful]
        chars_per_sec = [r.chars_per_second for r in successful]
        
        return {
            "total_tests": len(results),
            "successful": len(successful),
            "failed": len(results) - len(successful),
            "avg_latency_ms": round(sum(latencies) / len(latencies), 2),
            "avg_synthesis_time_ms": round(sum(synthesis_times) / len(synthesis_times), 2),
            "avg_model_load_time_ms": round(sum(model_load_times) / len(model_load_times), 2),
            "avg_audio_size_bytes": round(sum(audio_sizes) / len(audio_sizes), 2),
            "avg_audio_duration_sec": round(sum(audio_durations) / len(audio_durations), 3),
            "avg_chars_per_second": round(sum(chars_per_sec) / len(chars_per_sec), 2),
            "min_latency_ms": round(min(latencies), 2),
            "max_latency_ms": round(max(latencies), 2),
        }

    def _save_result(self, result: BenchmarkResult):
        """Save benchmark result to disk."""
        try:
            filepath = BENCHMARK_DIR / f"benchmark_{result.test_id}.json"
            data = {
                "test_id": result.test_id,
                "timestamp": result.timestamp,
                "system_info": asdict(result.system_info),
                "test_config": result.test_config,
                "results": [asdict(r) for r in result.results],
                "aggregate": result.aggregate,
            }
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2)
            logger.info(f"Saved benchmark result to {filepath}")
        except Exception as e:
            logger.error(f"Failed to save benchmark result: {e}")

    def load_result(self, test_id: str) -> Optional[Dict]:
        """Load a specific benchmark result."""
        filepath = BENCHMARK_DIR / f"benchmark_{test_id}.json"
        if not filepath.exists():
            return None
        try:
            with open(filepath, 'r') as f:
                return json.load(f)
        except:
            return None

    def load_all_results(self) -> List[Dict]:
        """Load all benchmark results."""
        results = []
        if not BENCHMARK_DIR.exists():
            return results
        
        for filepath in sorted(BENCHMARK_DIR.glob("benchmark_*.json"), reverse=True):
            try:
                with open(filepath, 'r') as f:
                    results.append(json.load(f))
            except:
                continue
        
        return results

    def delete_result(self, test_id: str) -> bool:
        """Delete a benchmark result."""
        filepath = BENCHMARK_DIR / f"benchmark_{test_id}.json"
        if filepath.exists():
            filepath.unlink()
            return True
        return False


_benchmark_runner = BenchmarkRunner()


# Global dependencies (initialized in init_benchmark_router)
_tts_engine = None
_voice_config_manager = None


def init_benchmark_router(engine, config_mgr):
    """Initialize the benchmark router with dependencies."""
    global _tts_engine, _voice_config_manager
    _tts_engine = engine
    _voice_config_manager = config_mgr


# ============ API Endpoints ============

@router.get("/system")
async def get_system_info():
    """Get current system information."""
    return asdict(_benchmark_runner.get_system_info())


@router.get("/stats")
async def get_benchmark_stats():
    """Get global benchmark statistics aggregated by system specs."""
    results = _benchmark_runner.load_all_results()
    
    if not results:
        return {
            "total_benchmarks": 0,
            "global_avg_latency_ms": 0,
            "best_voice": None,
            "total_voices_tested": 0,
            "by_system": []
        }
    
    # Aggregate global stats
    all_latencies = []
    all_voices = set()
    best_voice_latencies = {}
    
    for r in results:
        agg = r.get("aggregate", {})
        all_latencies.append(agg.get("avg_latency_ms", 0))
        
        for res in r.get("results", []):
            if res.get("success"):
                all_voices.add(res.get("voice_id"))
                vid = res.get("voice_id")
                if vid not in best_voice_latencies:
                    best_voice_latencies[vid] = []
                best_voice_latencies[vid].append(res.get("latency_ms", 0))
    
    # Find best voice (lowest avg latency)
    best_voice = None
    best_avg = float('inf')
    for vid, lats in best_voice_latencies.items():
        avg = sum(lats) / len(lats)
        if avg < best_avg:
            best_avg = avg
            best_voice = vid
    
    # Group by system
    system_groups = {}
    for r in results:
        sys_info = r.get("system_info", {})
        key = f"{sys_info.get('cpu_cores', 0)} cores / {sys_info.get('ram_total_gb', 0)}GB {sys_info.get('os_name', 'Unknown')}"
        
        if key not in system_groups:
            system_groups[key] = {
                "system_specs": {
                    "cpu_cores": sys_info.get("cpu_cores", 0),
                    "ram_total_gb": sys_info.get("ram_total_gb", 0),
                    "os_name": sys_info.get("os_name", "Unknown"),
                    "hostname": sys_info.get("hostname", "Unknown"),
                },
                "benchmarks": [],
                "total_tests": 0,
                "avg_latency_ms": 0,
                "best_voice": None,
                "best_latency_ms": 0,
            }
        
        agg = r.get("aggregate", {})
        sys_group = system_groups[key]
        sys_group["benchmarks"].append({
            "test_id": r.get("test_id"),
            "timestamp": r.get("timestamp"),
            "avg_latency_ms": agg.get("avg_latency_ms", 0),
            "voices_tested": len(r.get("test_config", {}).get("voices", [])),
        })
        sys_group["total_tests"] += 1
        
        # Track best voice per system (use separate key to avoid conflict)
        if "_voice_latencies" not in sys_group:
            sys_group["_voice_latencies"] = {}
        
        for res in r.get("results", []):
            if res.get("success"):
                vid = res.get("voice_id")
                lat = res.get("latency_ms", 0)
                if vid not in sys_group["_voice_latencies"]:
                    sys_group["_voice_latencies"][vid] = []
                sys_group["_voice_latencies"][vid].append(lat)
    
    # Calculate avg latency per system
    for key, sys_group in system_groups.items():
        lats = [b["avg_latency_ms"] for b in sys_group["benchmarks"]]
        sys_group["avg_latency_ms"] = round(sum(lats) / len(lats), 2) if lats else 0
        
        # Find best voice for this system
        voice_lats = sys_group.get("_voice_latencies", {})
        if voice_lats:
            best_vid = None
            best_vlat = float('inf')
            for vid, lats in voice_lats.items():
                avg = sum(lats) / len(lats)
                if avg < best_vlat:
                    best_vlat = avg
                    best_vid = vid
            sys_group["best_voice"] = best_vid
            sys_group["best_latency_ms"] = round(best_vlat, 2)
        else:
            sys_group["best_voice"] = None
            sys_group["best_latency_ms"] = 0
        
        # Remove internal key
        if "_voice_latencies" in sys_group:
            del sys_group["_voice_latencies"]
    
    return {
        "total_benchmarks": len(results),
        "global_avg_latency_ms": round(sum(all_latencies) / len(all_latencies), 2) if all_latencies else 0,
        "best_voice": best_voice,
        "best_voice_avg_ms": round(best_avg, 2) if best_voice else 0,
        "total_voices_tested": len(all_voices),
        "by_system": list(system_groups.values()),
    }


class BenchmarkRequest(BaseModel):
    text: str = "Hello world, this is a test of the text to speech system."
    voices: Optional[List[str]] = None
    repetitions: int = 1


@router.post("/run")
async def run_benchmark(request: BenchmarkRequest):
    """
    Run a benchmark test.
    
    - **text**: Text to synthesize
    - **voices**: List of voice IDs to test (default: all)
    - **repetitions**: Number of times to repeat each test
    """
    if not request.text:
        raise HTTPException(status_code=400, detail="Text is required")
    
    if request.repetitions < 1 or request.repetitions > 20:
        raise HTTPException(status_code=400, detail="Repetitions must be between 1 and 20")
    
    if _tts_engine is None or _voice_config_manager is None:
        raise HTTPException(status_code=500, detail="Server not initialized")
    
    result = _benchmark_runner.run_benchmark(
        text=request.text,
        voices=request.voices or [],
        repetitions=request.repetitions,
        tts_engine=_tts_engine,
        voice_config_manager=_voice_config_manager,
    )
    
    return {
        "test_id": result.test_id,
        "timestamp": result.timestamp,
        "aggregate": result.aggregate,
        "system_info": asdict(result.system_info),
        "results": [asdict(r) for r in result.results],
    }


@router.get("/history")
async def get_benchmark_history(limit: int = 20):
    """Get benchmark history."""
    results = _benchmark_runner.load_all_results()
    return {
        "total": len(results),
        "benchmarks": [
            {
                "test_id": r["test_id"],
                "timestamp": r["timestamp"],
                "system": {
                    "cpu_cores": r["system_info"]["cpu_cores"],
                    "ram_total_gb": r["system_info"]["ram_total_gb"],
                },
                "config": r["test_config"],
                "aggregate": r["aggregate"],
            }
            for r in results[:limit]
        ]
    }


@router.get("/{test_id}")
async def get_benchmark_detail(test_id: str):
    """Get detailed benchmark results."""
    result = _benchmark_runner.load_result(test_id)
    if not result:
        raise HTTPException(status_code=404, detail=f"Benchmark '{test_id}' not found")
    return result


@router.delete("/{test_id}")
async def delete_benchmark(test_id: str):
    """Delete a benchmark result."""
    if _benchmark_runner.delete_result(test_id):
        return {"status": "deleted", "test_id": test_id}
    raise HTTPException(status_code=404, detail=f"Benchmark '{test_id}' not found")


@router.get("/export/{test_id}")
async def export_benchmark_csv(test_id: str):
    """Export benchmark results as CSV."""
    result = _benchmark_runner.load_result(test_id)
    if not result:
        raise HTTPException(status_code=404, detail=f"Benchmark '{test_id}' not found")
    
    import csv
    import io
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    writer.writerow([
        "test_id", "timestamp", "voice_id", "latency_ms", "synthesis_time_ms",
        "audio_size_bytes", "audio_duration_ms", "chars_per_second", "success", "error"
    ])
    
    for r in result["results"]:
        writer.writerow([
            result["test_id"],
            result["timestamp"],
            r["voice_id"],
            r["latency_ms"],
            r["synthesis_time_ms"],
            r["audio_size_bytes"],
            r["audio_duration_ms"],
            r["chars_per_second"],
            r["success"],
            r.get("error", ""),
        ])
    
    writer.writerow([])
    writer.writerow(["Aggregate"])
    for key, value in result["aggregate"].items():
        writer.writerow([key, value])
    
    output.seek(0)
    
    from fastapi.responses import Response
    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=benchmark_{test_id}.csv"},
    )