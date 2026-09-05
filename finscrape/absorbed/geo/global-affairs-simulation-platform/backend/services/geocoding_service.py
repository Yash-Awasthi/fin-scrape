"""地理坐标解析 - 地名转坐标，带缓存/限速/重试"""
import time
import logging
import json
import os
from typing import Optional, Dict, Tuple, List
from datetime import datetime, timezone

logger = logging.getLogger("geocoding")

# --- 本地坐标缓存 ---

# 内置高质量坐标库，覆盖国关推演常见地点
BUILTIN_COORDINATES: Dict[str, Tuple[float, float]] = {
    "Washington": (38.9072, -77.0369),
    "Washington D.C.": (38.9072, -77.0369),
    "United States": (38.9072, -77.0369),
    "USA": (38.9072, -77.0369),
    "Beijing": (39.9042, 116.4074),
    "China": (35.8617, 104.1954),
    "Moscow": (55.7558, 37.6173),
    "Russia": (61.5240, 105.3188),
    "Tehran": (35.6892, 51.3890),
    "Iran": (32.4279, 53.6880),
    "Kyiv": (50.4501, 30.5234),
    "Kiev": (50.4501, 30.5234),
    "Ukraine": (48.3794, 31.1656),
    "Jerusalem": (31.7683, 35.2137),
    "Tel Aviv": (32.0853, 34.7818),
    "Israel": (31.0461, 34.8516),
    "Gaza": (31.3547, 34.3088),
    "West Bank": (31.9522, 35.2332),
    "Pyongyang": (39.0194, 125.7381),
    "North Korea": (40.3399, 127.5101),
    "Seoul": (37.5665, 126.9780),
    "South Korea": (35.9078, 127.7669),
    "Tokyo": (35.6762, 139.6503),
    "Japan": (36.2048, 138.2529),
    "Taipei": (25.0330, 121.5654),
    "Taiwan": (23.6978, 120.9605),
    "New Delhi": (28.6139, 77.2090),
    "India": (20.5937, 78.9629),
    "Islamabad": (33.6844, 73.0479),
    "Pakistan": (30.3753, 69.3451),
    "Riyadh": (24.7136, 46.6753),
    "Saudi Arabia": (23.8859, 45.0792),
    "Ankara": (39.9334, 32.8597),
    "Turkey": (38.9637, 35.2433),
    "Berlin": (52.5200, 13.4050),
    "Germany": (51.1657, 10.4515),
    "Paris": (48.8566, 2.3522),
    "France": (46.2276, 2.2137),
    "London": (51.5074, -0.1278),
    "United Kingdom": (55.3781, -3.4360),
    "UK": (55.3781, -3.4360),
    "Warsaw": (52.2297, 21.0122),
    "Poland": (51.9194, 19.1451),
    "Brussels": (50.8503, 4.3517),
    "NATO": (50.8760, 4.3052),
    "United Nations": (40.7489, -73.9680),
    "UN": (40.7489, -73.9680),
    "Kabul": (34.5553, 69.2075),
    "Afghanistan": (33.9391, 67.7100),
    "Baghdad": (33.3152, 44.3661),
    "Iraq": (33.2232, 43.6793),
    "Damascus": (33.5138, 36.2765),
    "Syria": (34.8021, 38.9968),
    "Beirut": (33.8886, 35.4955),
    "Lebanon": (33.8547, 35.8623),
    "Sanaa": (15.3694, 44.1910),
    "Yemen": (15.5527, 48.5164),
    "Cairo": (30.0444, 31.2357),
    "Egypt": (26.8206, 30.8025),
    "Doha": (25.2854, 51.5310),
    "Qatar": (25.3548, 51.1839),
    "Abu Dhabi": (24.4539, 54.3773),
    "UAE": (23.4241, 53.8478),
    "Amman": (31.9454, 35.9284),
    "Jordan": (30.5852, 36.2384),
    "Addis Ababa": (9.0320, 38.7469),
    "Ethiopia": (9.1450, 40.4897),
    "Nairobi": (1.2921, 36.8219),
    "Kenya": (-0.0236, 37.9062),
    "Pretoria": (-25.7479, 28.2293),
    "South Africa": (-30.5595, 22.9375),
    "Brasilia": (-15.7801, -47.9292),
    "Brazil": (-14.2350, -51.9253),
    "Ottawa": (45.4215, -75.6919),
    "Canada": (56.1304, -106.3468),
    "Mexico City": (19.4326, -99.1332),
    "Mexico": (23.6345, -102.5528),
    # 重要地缘战略地点
    "Taiwan Strait": (24.5, 120.0),
    "South China Sea": (12.0, 115.0),
    "East China Sea": (28.0, 125.0),
    "Strait of Hormuz": (26.5, 56.3),
    "Black Sea": (43.0, 34.0),
    "Baltic Sea": (58.0, 20.0),
    "Arctic": (90.0, 0.0),
    "Crimea": (45.3479, 34.0285),
    "Donbas": (48.0, 38.0),
    "Zaporizhzhia": (47.8388, 35.1396),
    "Kherson": (46.6354, 32.6169),
    "Natanz": (33.7222, 51.7269),
    "Busan": (35.1796, 129.0756),
    "Okinawa": (26.5013, 127.9454),
    "Guam": (13.4443, 144.7937),
    "Diego Garcia": (-7.3195, 72.4204),
    "Strait of Malacca": (2.5, 101.0),
    "Suez Canal": (30.5234, 32.2802),
    "Global": (20.0, 0.0),
}

# 运行时内存缓存，重启清空
_runtime_cache: Dict[str, Optional[Tuple[float, float]]] = {}

# 未解析地名队列
_unresolved_queue: List[Dict] = []

# Nominatim限速 1req/s
_last_nominatim_call: float = 0.0
NOMINATIM_MIN_INTERVAL = 1.1


def get_coordinates(
    location_name: str,
    use_nominatim: bool = True,
    cache_file: Optional[str] = None,
) -> Optional[Dict]:
    """获取地名坐标，顺序：内置→内存缓存→文件缓存→Nominatim"""
    if not location_name or len(location_name.strip()) < 2:
        return None

    name = location_name.strip()

    # 内置库最快，无网络
    builtin = _lookup_builtin(name)
    if builtin:
        return {"lat": builtin[0], "lng": builtin[1], "source": "builtin"}

    # 内存缓存
    cache_key = name.lower()
    if cache_key in _runtime_cache:
        cached = _runtime_cache[cache_key]
        if cached:
            return {"lat": cached[0], "lng": cached[1], "source": "memory_cache"}
        return None  # 已知无法解析

    # 文件缓存
    if cache_file:
        file_result = _lookup_file_cache(name, cache_file)
        if file_result is not None:
            if file_result:
                _runtime_cache[cache_key] = file_result
                return {"lat": file_result[0], "lng": file_result[1], "source": "file_cache"}
            else:
                _runtime_cache[cache_key] = None
                return None

    # Nominatim API（限速）
    if use_nominatim:
        coords = _call_nominatim(name)
        _runtime_cache[cache_key] = coords
        if cache_file and coords:
            _save_to_file_cache(name, coords, cache_file)
        if coords:
            return {"lat": coords[0], "lng": coords[1], "source": "nominatim"}

    # 记录未解析
    _add_to_unresolved(name)
    _runtime_cache[cache_key] = None
    return None


def get_coordinates_for_event(
    key_locations: List[str],
    region: str,
    use_nominatim: bool = True,
) -> Optional[Dict]:
    """为事件取坐标，多个地点依次试，取第一个成功的"""
    candidates = list(key_locations or []) + [region or ""]

    for candidate in candidates:
        if not candidate:
            continue
        result = get_coordinates(candidate, use_nominatim=use_nominatim)
        if result:
            return result

    # 回退到区域中心
    region_centers = {
        "Middle East": {"lat": 26.0, "lng": 44.0, "source": "region_fallback"},
        "East Asia": {"lat": 35.0, "lng": 110.0, "source": "region_fallback"},
        "Europe": {"lat": 52.0, "lng": 15.0, "source": "region_fallback"},
        "South Asia": {"lat": 25.0, "lng": 73.0, "source": "region_fallback"},
        "Americas": {"lat": 20.0, "lng": -80.0, "source": "region_fallback"},
        "Africa": {"lat": 5.0, "lng": 20.0, "source": "region_fallback"},
        "Southeast Asia": {"lat": 10.0, "lng": 110.0, "source": "region_fallback"},
        "Central Asia": {"lat": 43.0, "lng": 67.0, "source": "region_fallback"},
    }
    return region_centers.get(region)


# --- 内部函数 ---

def _lookup_builtin(name: str) -> Optional[Tuple[float, float]]:
    """查内置坐标库，支持模糊匹配"""
    if name in BUILTIN_COORDINATES:
        return BUILTIN_COORDINATES[name]
    name_lower = name.lower()
    for key, coords in BUILTIN_COORDINATES.items():
        if key.lower() == name_lower:
            return coords
    # 包含匹配，如 "Gaza Strip" → "Gaza"
    for key, coords in BUILTIN_COORDINATES.items():
        if key.lower() in name_lower or name_lower in key.lower():
            return coords
    return None


def _lookup_file_cache(name: str, cache_file: str) -> Optional[Optional[Tuple[float, float]]]:
    """读文件缓存，None=未缓存，False=已知无法解析"""
    try:
        if not os.path.exists(cache_file):
            return None
        with open(cache_file, "r", encoding="utf-8") as f:
            cache = json.load(f)
        key = name.lower()
        if key in cache:
            entry = cache[key]
            if entry is None:
                return False
            return (entry["lat"], entry["lng"])
    except Exception:
        pass
    return None


def _save_to_file_cache(name: str, coords: Tuple[float, float], cache_file: str):
    """写文件缓存"""
    try:
        cache = {}
        if os.path.exists(cache_file):
            with open(cache_file, "r", encoding="utf-8") as f:
                cache = json.load(f)
        cache[name.lower()] = {"lat": coords[0], "lng": coords[1], "cached_at": datetime.now(timezone.utc).isoformat()}
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(cache, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.warning(f"[geocoding] 缓存写入失败: {e}")


def _call_nominatim(name: str) -> Optional[Tuple[float, float]]:
    """调Nominatim，带限速"""
    global _last_nominatim_call
    try:
        from geopy.geocoders import Nominatim

        elapsed = time.time() - _last_nominatim_call
        if elapsed < NOMINATIM_MIN_INTERVAL:
            time.sleep(NOMINATIM_MIN_INTERVAL - elapsed)

        geolocator = Nominatim(user_agent="IRPlatform/1.0")
        _last_nominatim_call = time.time()

        location = geolocator.geocode(name, timeout=10, language="en")
        if location:
            logger.info(f"[geocoding] Nominatim 解析 '{name}' → ({location.latitude:.4f}, {location.longitude:.4f})")
            return (location.latitude, location.longitude)

    except ImportError:
        logger.debug("[geocoding] geopy 未安装，跳过 Nominatim")
    except Exception as e:
        logger.warning(f"[geocoding] Nominatim 调用失败 '{name}': {e}")

    return None


def _add_to_unresolved(name: str):
    """记未解析地名"""
    _unresolved_queue.append({
        "name": name,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })
    if len(_unresolved_queue) % 10 == 0:
        logger.info(f"[geocoding] 未解析地名队列: {len(_unresolved_queue)} 条")


def get_unresolved_locations() -> List[Dict]:
    """获取未解析地名列表，方便人工补充"""
    return list(_unresolved_queue)


def get_cache_stats() -> Dict:
    """缓存统计"""
    return {
        "builtin_count": len(BUILTIN_COORDINATES),
        "memory_cache_count": len(_runtime_cache),
        "resolved_count": sum(1 for v in _runtime_cache.values() if v is not None),
        "unresolved_count": len(_unresolved_queue),
    }
