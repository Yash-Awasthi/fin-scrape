"""
ZAI Oracle — Hardware Detector
by Zawwar (github.com/Zawwarsami16)

Runs first on every startup.
Scans the machine, detects GPU/RAM/Ollama, checks API keys.
If both a good GPU and an API key are available,
it asks which one you want to use — you decide.

The result drives every AI decision in the system.
"""

import os
import sys
import platform
import subprocess
from config import GROQ_KEY, GEMINI_KEY, ANTHROPIC_KEY


# ANSI colors for terminal output
G = "\033[92m"   # green
C = "\033[96m"   # cyan
Y = "\033[93m"   # yellow
R = "\033[91m"   # red
W = "\033[97m"   # white
D = "\033[2m"    # dim
B = "\033[1m"    # bold
X = "\033[0m"    # reset


def detect_gpu():
    """Checks for NVIDIA, AMD, or Apple Silicon GPU."""
    gpu_info = {"type": "none", "name": None, "vram_gb": 0}

    # NVIDIA
    try:
        r = subprocess.run(
            ["nvidia-smi", "--query-gpu=name,memory.total",
             "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=8
        )
        if r.returncode == 0 and r.stdout.strip():
            parts = r.stdout.strip().split("\n")[0].split(",")
            gpu_info["type"]    = "nvidia"
            gpu_info["name"]    = parts[0].strip()
            gpu_info["vram_gb"] = round(int(parts[1].strip()) / 1024, 1)
            return gpu_info
    except Exception:
        pass

    # AMD (ROCm)
    try:
        r = subprocess.run(["rocminfo"], capture_output=True, text=True, timeout=8)
        if r.returncode == 0 and "GPU" in r.stdout:
            gpu_info["type"] = "amd"
            gpu_info["name"] = "AMD GPU (ROCm)"
            return gpu_info
    except Exception:
        pass

    # Apple Silicon (unified memory acts as GPU)
    if platform.system() == "Darwin":
        try:
            r = subprocess.run(
                ["sysctl", "-n", "machdep.cpu.brand_string"],
                capture_output=True, text=True
            )
            if "Apple" in r.stdout:
                gpu_info["type"] = "apple"
                gpu_info["name"] = r.stdout.strip()
                return gpu_info
        except Exception:
            pass

    return gpu_info


def get_ram():
    """Returns total RAM in GB."""
    try:
        import psutil
        return round(psutil.virtual_memory().total / (1024 ** 3), 1)
    except Exception:
        pass
    try:
        if platform.system() == "Linux":
            with open("/proc/meminfo") as f:
                for line in f:
                    if "MemTotal" in line:
                        return round(int(line.split()[1]) / (1024 ** 2), 1)
    except Exception:
        pass
    return 8.0


def get_disk_free():
    """Returns free disk space in GB."""
    try:
        import psutil
        return round(psutil.disk_usage("/").free / (1024 ** 3), 1)
    except Exception:
        return 0


def check_ollama():
    """
    Checks if Ollama is installed and which models are available.
    Returns (is_installed, best_model_available)
    """
    try:
        r = subprocess.run(
            ["ollama", "list"],
            capture_output=True, text=True, timeout=5
        )
        if r.returncode != 0:
            return False, None

        lines = r.stdout.strip().split("\n")
        models = []
        for line in lines[1:]:  # skip header
            if line.strip():
                model_name = line.split()[0]
                models.append(model_name)

        if not models:
            return True, None  # installed but no models pulled

        # Preference order — best quality first
        preferred = [
            "llama3:70b", "llama3:13b", "llama3:8b",
            "llama-3.3-70b", "llama-3.1-70b",
            "mistral:7b", "phi3:mini",
        ]
        for p in preferred:
            for m in models:
                if p in m:
                    return True, m

        return True, models[0]  # fallback to whatever is there

    except Exception:
        return False, None


def pick_best_local_model(gpu_info, ram_gb):
    """
    Given hardware specs, recommends the best Ollama model to use.
    These are rough guidelines based on what actually runs well.
    """
    vram = gpu_info.get("vram_gb", 0)
    gtype = gpu_info.get("type", "none")

    if gtype == "nvidia":
        if   vram >= 24: return "llama3:70b"
        elif vram >= 12: return "llama3:13b"
        elif vram >= 8:  return "llama3:8b"
        elif vram >= 4:  return "mistral:7b"
        else:            return "phi3:mini"
    elif gtype == "apple":
        if   ram_gb >= 32: return "llama3:13b"
        elif ram_gb >= 16: return "llama3:8b"
        else:              return "phi3:mini"
    elif gtype == "amd":
        return "llama3:8b"
    else:
        # CPU only — phi3:mini is the only sane choice
        return "phi3:mini"


def check_api_keys():
    """
    Checks which API keys are configured.
    Returns list of available providers in priority order.
    """
    available = []
    if GROQ_KEY:      available.append(("groq",      "Groq (llama3-70b) — FREE"))
    if GEMINI_KEY:    available.append(("gemini",    "Google Gemini — FREE tier"))
    if ANTHROPIC_KEY: available.append(("anthropic", "Anthropic Claude — paid, most accurate"))
    return available


def ask_user_preference(has_good_gpu, ollama_model, api_providers):
    """
    If both local GPU and API are available, ask the user which to use.
    Only called when there's a real choice to make.
    """
    if not has_good_gpu or not api_providers:
        return None  # no choice needed, auto-decide

    print(f"\n{B}{W}  Both local GPU and API keys detected.{X}")
    print(f"{D}  Which AI mode do you want to use?{X}\n")
    print(f"  {G}[1]{X} Local LLM  ({ollama_model}) — offline, free, private")
    print(f"  {C}[2]{X} API        ({api_providers[0][1]}) — online, faster")
    print(f"  {Y}[3]{X} Auto       — system decides based on query complexity")

    while True:
        try:
            choice = input(f"\n  {W}Your choice (1/2/3):{X} ").strip()
            if choice == "1": return "ollama"
            if choice == "2": return "api"
            if choice == "3": return "auto"
        except (KeyboardInterrupt, EOFError):
            return "auto"
        print(f"  {Y}  Please enter 1, 2, or 3{X}")


def detect():
    """
    Full hardware scan.
    Returns a profile dict that drives all downstream decisions.
    """
    ram_gb      = get_ram()
    disk_gb     = get_disk_free()
    gpu_info    = detect_gpu()
    ollama_ok, ollama_model = check_ollama()
    api_keys    = check_api_keys()

    # Does this machine have a GPU good enough for real LLM inference?
    has_good_gpu = (
        gpu_info["type"] in ("nvidia", "amd") and gpu_info["vram_gb"] >= 4
    ) or (
        gpu_info["type"] == "apple" and ram_gb >= 16
    )

    recommended_model = pick_best_local_model(gpu_info, ram_gb)

    # Decide AI mode
    user_pref = ask_user_preference(
        has_good_gpu and ollama_ok and ollama_model,
        ollama_model,
        api_keys
    )

    if user_pref:
        ai_mode = user_pref
    elif api_keys:
        ai_mode = "api"
    elif ollama_ok and ollama_model:
        ai_mode = "ollama"
    else:
        ai_mode = "none"

    return {
        "os":               platform.system(),
        "cpu_cores":        os.cpu_count() or 1,
        "ram_gb":           ram_gb,
        "disk_free_gb":     disk_gb,
        "gpu":              gpu_info,
        "has_good_gpu":     has_good_gpu,
        "ollama_ready":     ollama_ok,
        "ollama_model":     ollama_model,
        "recommended_llm":  recommended_model,
        "api_keys":         api_keys,
        "ai_mode":          ai_mode,
        "primary_api":      api_keys[0][0] if api_keys else None,
    }


def print_report(hw):
    """Prints a clean hardware summary to terminal."""
    gpu   = hw["gpu"]
    amode = hw["ai_mode"]
    api   = hw["api_keys"]

    mode_str = {
        "api":    f"{G}{api[0][1] if api else 'API'}{X}",
        "ollama": f"{C}Local LLM ({hw['ollama_model']}){X}",
        "auto":   f"{Y}Auto-select per query{X}",
        "none":   f"{Y}Rule-based (no AI key found){X}",
    }.get(amode, amode)

    print(f"\n{D}  {'─'*42}{X}")
    print(f"  {W}HARDWARE SCAN{X}")
    print(f"{D}  {'─'*42}{X}")
    print(f"  OS           {hw['os']}  ({hw['cpu_cores']} cores)")
    print(f"  RAM          {hw['ram_gb']} GB")
    print(f"  Disk free    {hw['disk_free_gb']} GB")

    if gpu["name"]:
        print(f"  GPU          {G}{gpu['name']}{X}", end="")
        if gpu["vram_gb"]:
            print(f"  ({gpu['vram_gb']} GB VRAM)", end="")
        print()
    else:
        print(f"  GPU          {D}none detected{X}")

    if hw["ollama_ready"]:
        model = hw["ollama_model"] or "installed, no models pulled"
        print(f"  Ollama       {G}ready{X}  ({model})")
    else:
        print(f"  Ollama       {D}not installed{X}")

    print(f"{D}  {'─'*42}{X}")
    print(f"  AI mode      {mode_str}")
    print(f"{D}  {'─'*42}{X}\n")

    if amode == "none":
        print(f"  {Y}No AI key found. Add to .env file:{X}")
        print(f"  {D}GROQ_KEY=gsk_...   (free at groq.com){X}\n")


if __name__ == "__main__":
    hw = detect()
    print_report(hw)
