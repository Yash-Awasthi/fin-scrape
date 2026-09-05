"""
ZAI World Model v2 - ULTIMATE EDITION
Auto hardware detection + Auto LLM selection + Full power
By Zawwar (Zawwarsami16)
"""

import os
import sys
import platform
import subprocess
import json
import time

# ============================================================
# COLORS FOR TERMINAL
# ============================================================
class C:
    GREEN  = "\033[92m"
    CYAN   = "\033[96m"
    YELLOW = "\033[93m"
    RED    = "\033[91m"
    BOLD   = "\033[1m"
    RESET  = "\033[0m"
    DIM    = "\033[2m"

def p(text, color=C.RESET):
    print(f"{color}{text}{C.RESET}")

def banner():
    os.system("cls" if os.name == "nt" else "clear")
    p("""
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║         ZAI WORLD MODEL v2 — ULTIMATE EDITION               ║
║         Macro Market Prediction AI by ZAWWAR                 ║
║         github.com/Zawwarsami16                              ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
""", C.CYAN)

# ============================================================
# HARDWARE DETECTION
# ============================================================
def detect_hardware():
    p("\n🔍 Hardware detect kar raha hun...\n", C.YELLOW)
    
    hw = {
        "os": platform.system(),
        "os_version": platform.version(),
        "cpu": platform.processor(),
        "cpu_cores": os.cpu_count(),
        "ram_gb": 0,
        "gpu": None,
        "gpu_vram_gb": 0,
        "gpu_type": "none",  # none / nvidia / amd / apple
        "disk_free_gb": 0,
        "python_version": sys.version,
        "can_run_local_llm": False,
        "recommended_llm": None,
    }

    # RAM detection
    try:
        import psutil
        hw["ram_gb"] = round(psutil.virtual_memory().total / (1024**3), 1)
        hw["disk_free_gb"] = round(psutil.disk_usage("/").free / (1024**3), 1)
    except:
        try:
            if platform.system() == "Linux":
                with open("/proc/meminfo") as f:
                    for line in f:
                        if "MemTotal" in line:
                            kb = int(line.split()[1])
                            hw["ram_gb"] = round(kb / (1024**2), 1)
                            break
            elif platform.system() == "Windows":
                result = subprocess.run(
                    ["wmic", "computersystem", "get", "TotalPhysicalMemory"],
                    capture_output=True, text=True)
                bytes_val = int(result.stdout.strip().split("\n")[-1].strip())
                hw["ram_gb"] = round(bytes_val / (1024**3), 1)
        except:
            hw["ram_gb"] = 8  # assume 8GB

    # GPU detection
    # Try NVIDIA
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=name,memory.total",
             "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=10)
        if result.returncode == 0 and result.stdout.strip():
            lines = result.stdout.strip().split("\n")
            gpu_name = lines[0].split(",")[0].strip()
            vram_mb = int(lines[0].split(",")[1].strip())
            hw["gpu"] = gpu_name
            hw["gpu_vram_gb"] = round(vram_mb / 1024, 1)
            hw["gpu_type"] = "nvidia"
    except:
        pass

    # Try AMD
    if not hw["gpu"]:
        try:
            result = subprocess.run(
                ["rocminfo"], capture_output=True, text=True, timeout=10)
            if result.returncode == 0 and "GPU" in result.stdout:
                hw["gpu_type"] = "amd"
                hw["gpu"] = "AMD GPU (ROCm)"
        except:
            pass

    # Try Apple Silicon
    if not hw["gpu"] and platform.system() == "Darwin":
        try:
            result = subprocess.run(
                ["sysctl", "-n", "machdep.cpu.brand_string"],
                capture_output=True, text=True)
            if "Apple" in result.stdout:
                hw["gpu_type"] = "apple"
                hw["gpu"] = result.stdout.strip()
                hw["gpu_vram_gb"] = hw["ram_gb"] * 0.75  # Unified memory
        except:
            pass

    # Decide LLM capability
    if hw["gpu_type"] == "nvidia":
        if hw["gpu_vram_gb"] >= 24:
            hw["can_run_local_llm"] = True
            hw["recommended_llm"] = "llama3:70b"
        elif hw["gpu_vram_gb"] >= 12:
            hw["can_run_local_llm"] = True
            hw["recommended_llm"] = "llama3:13b"
        elif hw["gpu_vram_gb"] >= 6:
            hw["can_run_local_llm"] = True
            hw["recommended_llm"] = "llama3:8b"
        elif hw["gpu_vram_gb"] >= 4:
            hw["can_run_local_llm"] = True
            hw["recommended_llm"] = "mistral:7b"
    elif hw["gpu_type"] == "apple":
        if hw["ram_gb"] >= 32:
            hw["can_run_local_llm"] = True
            hw["recommended_llm"] = "llama3:13b"
        elif hw["ram_gb"] >= 16:
            hw["can_run_local_llm"] = True
            hw["recommended_llm"] = "llama3:8b"
    elif hw["gpu_type"] == "amd":
        hw["can_run_local_llm"] = True
        hw["recommended_llm"] = "llama3:8b"
    elif hw["ram_gb"] >= 16:
        # CPU only - slow but possible with small model
        hw["can_run_local_llm"] = True
        hw["recommended_llm"] = "phi3:mini"  # Very small, CPU friendly

    # Print results
    p(f"  💻 OS:          {hw['os']} {hw.get('os_version','')[:30]}", C.CYAN)
    p(f"  🧠 CPU:         {hw['cpu'][:50] if hw['cpu'] else 'Unknown'} ({hw['cpu_cores']} cores)", C.CYAN)
    p(f"  💾 RAM:         {hw['ram_gb']} GB", C.CYAN)
    p(f"  💿 Disk Free:   {hw['disk_free_gb']} GB", C.CYAN)

    if hw["gpu"]:
        p(f"  🎮 GPU:         {hw['gpu']}", C.GREEN)
        p(f"  🎮 VRAM:        {hw['gpu_vram_gb']} GB", C.GREEN)
    else:
        p(f"  🎮 GPU:         Not detected (CPU mode)", C.YELLOW)

    print()
    if hw["can_run_local_llm"]:
        p(f"  ✅ LOCAL LLM:   CAN RUN → {hw['recommended_llm']}", C.GREEN)
        p(f"     (FREE predictions — no API needed!)", C.GREEN)
    else:
        p(f"  ⚡ LOCAL LLM:   Hardware insufficient — using Claude API", C.YELLOW)
        p(f"     (Need: 4GB+ VRAM or 16GB+ RAM)", C.DIM)

    return hw

# ============================================================
# DEPENDENCY INSTALLER
# ============================================================
def install_package(package, import_name=None):
    import_name = import_name or package
    try:
        __import__(import_name)
        return True
    except ImportError:
        pass

    p(f"  📦 Installing {package}...", C.YELLOW)
    try:
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", package,
            "--break-system-packages", "-q"
        ])
        return True
    except:
        try:
            subprocess.check_call([
                sys.executable, "-m", "pip", "install", package, "-q"
            ])
            return True
        except:
            return False

def install_all_dependencies(hw):
    p("\n📦 Dependencies check kar raha hun...\n", C.YELLOW)

    # Base packages
    base = [
        ("requests", "requests"),
        ("pandas", "pandas"),
        ("numpy", "numpy"),
        ("yfinance", "yfinance"),
        ("psutil", "psutil"),
        ("rich", "rich"),          # Beautiful terminal UI
        ("plotext", "plotext"),    # Terminal charts
    ]

    for pkg, imp in base:
        if install_package(pkg, imp):
            p(f"  ✅ {pkg}", C.GREEN)
        else:
            p(f"  ❌ {pkg} — install manually", C.RED)

    # Ollama for local LLM
    if hw["can_run_local_llm"]:
        p(f"\n  🤖 Local LLM setup ({hw['recommended_llm']})...", C.CYAN)
        if not check_ollama():
            p(f"  📥 Ollama install karna hoga:", C.YELLOW)
            if hw["os"] == "Linux":
                p(f"     curl -fsSL https://ollama.com/install.sh | sh", C.CYAN)
            elif hw["os"] == "Windows":
                p(f"     https://ollama.com/download/windows se download karo", C.CYAN)
            elif hw["os"] == "Darwin":
                p(f"     https://ollama.com/download/mac se download karo", C.CYAN)

            ans = input("\n  Ollama install kiya? (y/n): ").strip().lower()
            if ans == "y":
                if check_ollama():
                    pull_ollama_model(hw["recommended_llm"])
        else:
            p(f"  ✅ Ollama already installed!", C.GREEN)
            pull_ollama_model(hw["recommended_llm"])

def check_ollama():
    try:
        result = subprocess.run(["ollama", "list"],
                                capture_output=True, text=True, timeout=5)
        return result.returncode == 0
    except:
        return False

def pull_ollama_model(model_name):
    p(f"\n  📥 Model download kar raha hun: {model_name}", C.YELLOW)
    p(f"  ⚠️  Ye time lagega — model size: ", C.YELLOW, end="")

    sizes = {
        "llama3:70b": "40GB", "llama3:13b": "8GB",
        "llama3:8b": "5GB", "mistral:7b": "4GB", "phi3:mini": "2GB"
    }
    p(sizes.get(model_name, "unknown"), C.RED)

    ans = input(f"  Download karna hai? (y/n): ").strip().lower()
    if ans == "y":
        subprocess.run(["ollama", "pull", model_name])
        p(f"  ✅ Model ready: {model_name}", C.GREEN)

# ============================================================
# AI BRAIN - Auto selects Claude API or Local LLM
# ============================================================
def ask_ai(prompt, hw, config):
    """Auto-detect: local LLM use karo ya Claude API"""

    # Try local LLM first if available
    if hw.get("can_run_local_llm") and check_ollama():
        model = hw.get("recommended_llm", "llama3:8b")
        try:
            result = subprocess.run(
                ["ollama", "run", model, prompt],
                capture_output=True, text=True, timeout=120)
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout.strip(), "local"
        except:
            pass

    # Fallback: Claude API
    api_key = config.get("ANTHROPIC_KEY", "")
    if api_key and api_key != "YOUR_ANTHROPIC_API_KEY_HERE":
        try:
            import requests as req
            response = req.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json"
                },
                json={
                    "model": "claude-sonnet-4-20250514",
                    "max_tokens": 1500,
                    "messages": [{"role": "user", "content": prompt}]
                },
                timeout=60
            )
            result = response.json()
            if "content" in result:
                return result["content"][0]["text"], "claude_api"
        except Exception as e:
            return None, f"error: {e}"

    return None, "no_ai_available"

# ============================================================
# CONFIG LOADER
# ============================================================
def load_config():
    config_path = os.path.join(os.path.dirname(__file__), "config.py")
    config = {
        "ANTHROPIC_KEY": "YOUR_ANTHROPIC_API_KEY_HERE",
        "DATA_PATH": "./zai_data",
        "UPDATE_INTERVAL": 300,
        "MIN_CONFIDENCE": 65,
        "HISTORY_FROM_YEAR": 1871,
    }
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location("config", config_path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        for key in config:
            if hasattr(mod, key):
                config[key] = getattr(mod, key)
    except:
        pass
    return config

# ============================================================
# SYSTEM STATUS CHECK
# ============================================================
def check_system_status(config):
    p("\n📊 System status check...\n", C.YELLOW)
    
    data_path = config.get("DATA_PATH", "./zai_data")
    hist_path = os.path.join(data_path, "historical")
    
    # Data check
    datasets = []
    if os.path.exists(hist_path):
        datasets = [f.replace(".csv","") for f in os.listdir(hist_path) 
                   if f.endswith(".csv")]
    
    p(f"  📂 Datasets:     {len(datasets)} downloaded", 
      C.GREEN if datasets else C.RED)
    
    # Prediction check
    pred_path = os.path.join(data_path, "predictions", "latest.json")
    if os.path.exists(pred_path):
        with open(pred_path) as f:
            pred = json.load(f)
        gen_at = pred.get("generated_at", "")[:19]
        has_ai = pred.get("ai_prediction") is not None
        p(f"  🤖 Last prediction: {gen_at}", C.GREEN)
        p(f"  🧠 AI prediction:   {'YES' if has_ai else 'NO (API needed)'}", 
          C.GREEN if has_ai else C.YELLOW)
    else:
        p(f"  🤖 Predictions:  None yet", C.YELLOW)
    
    # API key check
    key = config.get("ANTHROPIC_KEY", "")
    if key and key != "YOUR_ANTHROPIC_API_KEY_HERE":
        p(f"  🔑 Claude API:   Key found ✅", C.GREEN)
    else:
        p(f"  🔑 Claude API:   No key (add to config.py)", C.YELLOW)
    
    # Ollama check
    if check_ollama():
        p(f"  🦙 Ollama:       Installed ✅", C.GREEN)
    else:
        p(f"  🦙 Ollama:       Not installed", C.DIM)
    
    return len(datasets) > 0

# ============================================================
# MAIN MENU
# ============================================================
def main_menu(hw, config, has_data):
    while True:
        p("\n" + "─"*60, C.DIM)
        p("  MAIN MENU", C.BOLD)
        p("─"*60, C.DIM)
        p("  1. Download historical data (pehli baar ya update)", C.CYAN)
        p("  2. Run correlation + prediction engine", C.CYAN)
        p("  3. Launch live dashboard (24/7)", C.CYAN)
        p("  4. Hardware info dekhna", C.CYAN)
        p("  5. Exit", C.DIM)
        p("─"*60, C.DIM)

        choice = input("  Choose (1-5): ").strip()

        if choice == "1":
            p("\n▶ Data collector chalao: python3 data_collector.py\n", C.GREEN)
            run = input("  Abhi chalau? (y/n): ").strip().lower()
            if run == "y":
                subprocess.run([sys.executable, "data_collector.py"])

        elif choice == "2":
            if not has_data:
                p("  ❌ Pehle data download karo (Option 1)", C.RED)
                continue

            ai_source = "none"
            if hw["can_run_local_llm"] and check_ollama():
                ai_source = f"local ({hw['recommended_llm']})"
            elif config.get("ANTHROPIC_KEY","") != "YOUR_ANTHROPIC_API_KEY_HERE":
                ai_source = "Claude API"

            p(f"\n  AI Source: {ai_source}", C.CYAN)
            run = input("  Chalau? (y/n): ").strip().lower()
            if run == "y":
                subprocess.run([sys.executable, "correlation_engine.py"])

        elif choice == "3":
            if not has_data:
                p("  ❌ Pehle data download karo (Option 1)", C.RED)
                continue
            p("\n  Dashboard shuru ho raha hai...", C.GREEN)
            subprocess.run([sys.executable, "dashboard.py"])

        elif choice == "4":
            p("\n📊 HARDWARE DETAILS:", C.YELLOW)
            for k, v in hw.items():
                p(f"  {k}: {v}", C.CYAN)

        elif choice == "5":
            p("\n👋 Khuda Hafiz! — Zawwar\n", C.GREEN)
            break

# ============================================================
# MAIN
# ============================================================
if __name__ == "__main__":
    banner()

    # Load config
    config = load_config()

    # Detect hardware
    hw = detect_hardware()

    # Install dependencies
    install_all_dependencies(hw)

    # Check system
    has_data = check_system_status(config)

    # Show AI mode
    p("\n" + "─"*60, C.DIM)
    if hw["can_run_local_llm"] and check_ollama():
        p(f"  🤖 AI MODE: LOCAL ({hw['recommended_llm']}) — FREE & OFFLINE", C.GREEN)
    elif config.get("ANTHROPIC_KEY","") != "YOUR_ANTHROPIC_API_KEY_HERE":
        p(f"  🤖 AI MODE: Claude API — Online", C.CYAN)
    else:
        p(f"  ⚠️  AI MODE: None — Add API key to config.py", C.YELLOW)
    p("─"*60, C.DIM)

    # Main menu
    main_menu(hw, config, has_data)
