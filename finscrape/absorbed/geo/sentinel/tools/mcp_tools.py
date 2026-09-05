# tools/mcp_tools.py
import os
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".env"))

import yfinance as yf
import requests
import json
from datetime import datetime

# ─────────────────────────────────────────────────────────────────────────────
# GLOBAL DEFENSE COMPANY UNIVERSE
# Organised by country. Public companies have exchange-qualified ticker symbols.
# Private companies (no public listing) are included for research/risk-scoring
# context but excluded from live price feeds.
# ─────────────────────────────────────────────────────────────────────────────

DEFENSE_UNIVERSE = {
    # ── UNITED STATES ────────────────────────────────────────────────────────
    "US": {
        "public": {
            "LMT":  "Lockheed Martin",
            "RTX":  "RTX Corp (Raytheon)",
            "NOC":  "Northrop Grumman",
            "GD":   "General Dynamics",
            "BA":   "Boeing",
            "HII":  "Huntington Ingalls",
            "LHX":  "L3Harris Technologies",
            "TXT":  "Textron (Bell/Cessna)",
            "LDOS": "Leidos Holdings",
            "BAH":  "Booz Allen Hamilton",
            "BWXT": "BWX Technologies",
            "KTOS": "Kratos Defense",
            "AVAV": "AeroVironment",
            "PLTR": "Palantir Technologies",
            "CACI": "CACI International",
            "MANT": "ManTech International",
            "DRS":  "Leonardo DRS",
            "AXON": "Axon Enterprise",
        },
        "private": {
            "SAIC":      "Science Applications International (SAIC)",
            "LEIDOS":    "Leidos (legacy)",
            "MITRE":     "MITRE Corporation",
            "DRAPER":    "Draper Laboratory",
            "AMSYS":     "AM General (vehicles)",
            "SIKORSKY":  "Sikorsky Aircraft (Lockheed sub.)",
            "DYNETICS":  "Dynetics (Leidos sub.)",
            "SIERRA_NV": "Sierra Nevada Corporation",
            "ANDURIL":   "Anduril Industries",
            "SHIELD_AI": "Shield AI",
            "TRUE_ANOM": "True Anomaly",
        }
    },
    # ── RUSSIA ───────────────────────────────────────────────────────────────
    "RU": {
        "public": {
            "RSTLD":  "Rostec State Corporation (OTC)",
            "UWGN.ME":"United Wagon Company (MOEX)",
        },
        "private": {
            "ROSTEC":          "Rostec (state conglomerate)",
            "ALMAZ-ANTEY":     "Almaz-Antey (S-300/S-400 systems)",
            "TACTICAL_MISS":   "Tactical Missiles Corporation",
            "ROSOBORONEXPORT": "Rosoboronexport (export arm)",
            "SUKHOI":          "Sukhoi (Su-27/35/57 jets)",
            "MIKOYAN":         "Mikoyan (MiG jets)",
            "TUPOLEV":         "Tupolev (bombers)",
            "KALASHNIKOV":     "Kalashnikov Concern",
            "UEC":             "United Engine Corporation",
            "URALVAGONZAVOD":  "Uralvagonzavod (T-72/T-90 tanks)",
            "NPO_MASH":        "NPO Mashinostroyeniya (hypersonics)",
            "IRKUT":           "Irkut Corporation (MC-21/Su-30)",
            "KAMOV":           "Kamov (Ka-52 helicopters)",
        }
    },
    # ── CHINA ────────────────────────────────────────────────────────────────
    "CN": {
        "public": {
            "600760.SS": "AVIC Chengdu Aircraft (SSE)",
            "000768.SZ": "AVIC Aviation Engine (SZSE)",
            "601989.SS": "China Shipbuilding Industry (SSE)",
            "600893.SS": "AVIC Aero-Engine Holdings (SSE)",
            "002013.SZ": "AVIC High Technology (SZSE)",
            "600550.SS": "Poly Technologies (SSE)",
            "000630.SZ": "NORINCO International (SZSE)",
        },
        "private": {
            "NORINCO":    "China North Industries Group (NORINCO)",
            "CASIC":      "China Aerospace Science and Industry Corp",
            "CASC":       "China Aerospace Science and Technology Corp",
            "AVIC":       "Aviation Industry Corporation of China (AVIC)",
            "CSSC":       "China State Shipbuilding Corp",
            "CETC":       "China Electronics Technology Group",
            "POLY_TECH":  "Poly Technologies",
            "DJI":        "SZ DJI Technology (drones)",
            "CNSI":       "China National South Industries Group",
        }
    },
    # ── INDIA ────────────────────────────────────────────────────────────────
    "IN": {
        "public": {
            "HAL.NS":   "Hindustan Aeronautics Ltd",
            "BEL.NS":   "Bharat Electronics Ltd",
            "BHEL.NS":  "Bharat Heavy Electricals",
            "SOL.NS":   "Solar Industries India (munitions)",
            "ASTRA.NS": "Astra Microwave Products",
            "MTAR.NS":  "MTAR Technologies (propulsion)",
            "PARAS.NS": "Paras Defence and Space Technologies",
            "DCX.NS":   "DCX Systems (aerospace assemblies)",
            "BEML.NS":  "BEML Ltd (military vehicles)",
            "ZEN.NS":   "Zen Technologies (defence simulation)",
        },
        "private": {
            "DRDO":        "Defence Research & Development Organisation",
            "OFB":         "Ordnance Factory Board",
            "BRAHMOS":     "BrahMos Aerospace (joint RU/IN)",
            "TATA_ADV":    "Tata Advanced Systems",
            "L_T_DEF":     "Larsen & Toubro Defence",
            "MAHINDRA_DEF":"Mahindra Defence Systems",
            "ADANI_DEF":   "Adani Defence & Aerospace",
            "RELIANCE_DEF":"Reliance Defence Ltd",
        }
    },
    # ── ISRAEL ───────────────────────────────────────────────────────────────
    "IL": {
        "public": {
            "ESLT":    "Elbit Systems (NASDAQ)",
            "RRPBY":   "Rafael Advanced Defence Systems (OTC)",
        },
        "private": {
            "IAI":          "Israel Aerospace Industries",
            "RAFAEL":       "Rafael Advanced Defence Systems",
            "IMI":          "Israel Military Industries (Elbit sub.)",
            "ELTA":         "Elta Systems (IAI sub. — radar)",
            "TADIRAN":      "Tadiran Electronic Systems",
            "SOLTAM":       "Soltam Systems (artillery)",
            "AERONAUTICS":  "Aeronautics Ltd (drones)",
            "ORBITER":      "Orbiter (loitering munitions)",
            "IRON_DOME_OP": "Iron Dome operated by IAI/Rafael",
        }
    },
    # ── FRANCE ───────────────────────────────────────────────────────────────
    "FR": {
        "public": {
            "AIR.PA": "Airbus SE",
            "SAF.PA": "Safran SA",
            "HO.PA":  "Thales SA",
            "AM.PA":  "Dassault Aviation",
        },
        "private": {
            "MBDA":      "MBDA (missile systems joint venture)",
            "NEXTER":    "Nexter Systems (KNDS — tanks)",
            "ARQUUS":    "Arquus (military vehicles)",
            "NAVAL_GRP": "Naval Group (warships)",
            "KNDS":      "KNDS (Krauss-Maffei Wegmann + Nexter)",
        }
    },
    # ── UNITED KINGDOM ───────────────────────────────────────────────────────
    "UK": {
        "public": {
            "BA.L":    "BAE Systems plc (LSE)",
            "RR.L":    "Rolls-Royce Holdings (LSE)",
            "QQ.L":    "QinetiQ Group (LSE)",
            "COBR.L":  "Cobham plc (LSE)",
            "ULE.L":   "Ultra Electronics (LSE)",
        },
        "private": {
            "MBDA_UK":    "MBDA UK",
            "THALES_UK":  "Thales UK",
            "MARSHALL_AD":"Marshall Aerospace and Defence",
            "SERCO_DEF":  "Serco Defence",
            "CHEMRING":   "Chemring Group (explosives/countermeasures)",
        }
    },
    # ── GERMANY ──────────────────────────────────────────────────────────────
    "DE": {
        "public": {
            "RHM.DE":  "Rheinmetall AG (XETRA)",
            "HEN3.DE": "Hensoldt AG (XETRA)",
            "AIR.DE":  "Airbus SE (XETRA)",
        },
        "private": {
            "KMW":       "Krauss-Maffei Wegmann (Leopard tanks)",
            "DIEHL_DEF": "Diehl Defence (IRIS-T missiles)",
            "MBDA_DE":   "MBDA Deutschland",
            "THALES_DE": "Thales Deutschland",
            "ROHDE_S":   "Rohde & Schwarz (comms/EW)",
            "ATLAS_ELK": "Atlas Elektronik (naval systems)",
        }
    },
    # ── IRAN ─────────────────────────────────────────────────────────────────
    "IR": {
        "public": {},   # All state entities, no exchange listings
        "private": {
            "IRGC_AEO":   "IRGC Aerospace Organization",
            "IRAN_ELECTR":"Iran Electronics Industries",
            "DEF_IND_ORG":"Defence Industries Organisation (DIO)",
            "SHAHID_HEM": "Shahid Hemmat Industrial Group (ballistic missiles)",
            "QODS_AV":    "Qods Aviation Industries (drones/Shahed)",
            "IRGC_NAVY":  "IRGC Naval Forces (fast-boat doctrine)",
            "MALEK_ASHTAR":"Malek Ashtar University (weapons R&D)",
        }
    },
    # ── SOUTH KOREA ──────────────────────────────────────────────────────────
    "KR": {
        "public": {
            "047810.KS": "Korea Aerospace Industries (KRX)",
            "012450.KS": "Hanwha Aerospace (KRX)",
            "064350.KS": "Hyundai Rotem (KRX — K2 tanks)",
            "015760.KS": "Korea Electric Power (defense grid)",
        },
        "private": {
            "LIG_NEX1":   "LIG Nex1 (missiles/radar)",
            "KAI_PRIV":   "Korea Aerospace Industries (private arm)",
            "POONGSAN":   "Poongsan Corporation (ammunition)",
            "HANWHA_SYS": "Hanwha Systems (defense electronics)",
        }
    },
    # ── JAPAN ────────────────────────────────────────────────────────────────
    "JP": {
        "public": {
            "7011.T":  "Mitsubishi Heavy Industries (TSE)",
            "7012.T":  "Kawasaki Heavy Industries (TSE)",
            "6952.T":  "Fujitsu Ltd (defense systems, TSE)",
            "6501.T":  "Hitachi (defense electronics, TSE)",
            "7016.T":  "Subaru Corporation (aerospace, TSE)",
        },
        "private": {
            "IHI_DEF":     "IHI Corporation (jet engines)",
            "NEC_DEF":     "NEC Defense & Space",
            "TOSHIBA_DEF": "Toshiba Defense & Electronic Systems",
            "MELCO_DEF":   "Mitsubishi Electric (radar/missiles)",
        }
    },
    # ── TURKEY ───────────────────────────────────────────────────────────────
    "TR": {
        "public": {
            "ASELS.IS": "Aselsan (BIST)",
            "TSKB.IS":  "TSKB (defense finance, BIST)",
        },
        "private": {
            "BAYKAR":    "Baykar Makina (Bayraktar drones)",
            "ROKETSAN":  "Roketsan (missiles/rockets)",
            "MKEK":      "MKEK (munitions factory)",
            "STM":       "STM (defense engineering)",
            "TAI":       "TAI — Turkish Aerospace Industries",
            "BMC":       "BMC (military vehicles)",
        }
    },
    # ── PAKISTAN ─────────────────────────────────────────────────────────────
    "PK": {
        "public": {},
        "private": {
            "KRL":       "Khan Research Laboratories (nuclear)",
            "POF":       "Pakistan Ordnance Factories",
            "PAEC":      "Pakistan Atomic Energy Commission",
            "HAL_PK":    "Heavy Industries Taxila (tanks)",
            "PAC":       "Pakistan Aeronautical Complex",
            "GIDS":      "Global Industrial & Defence Solutions",
        }
    },
    # ── SWEDEN ───────────────────────────────────────────────────────────────
    "SE": {
        "public": {
            "SAAB-B.ST": "Saab AB (Stockholm)",
        },
        "private": {
            "FMV":      "Swedish Defence Material Administration",
            "BOFORS":   "Bofors (now BAE Systems Bofors)",
            "NAMMO_SE": "NAMMO (Norway/Sweden — ammunition)",
        }
    },
    # ── ITALY ────────────────────────────────────────────────────────────────
    "IT": {
        "public": {
            "LDO.MI": "Leonardo SpA (Borsa Italiana)",
        },
        "private": {
            "OTO_MEL":  "OTO Melara (artillery, Leonardo sub.)",
            "MBDA_IT":  "MBDA Italia",
            "IVECO_DEF":"Iveco Defence Vehicles",
            "AVIO":     "Avio (space/military propulsion)",
        }
    },
    # ── BRAZIL ───────────────────────────────────────────────────────────────
    "BR": {
        "public": {
            "EMBR3.SA": "Embraer SA (B3)",
        },
        "private": {
            "TAURUS":   "Taurus Armas (small arms)",
            "AVIBRAS":  "Avibras (rockets/missiles)",
            "ENGESA":   "Engesa (legacy armored vehicles)",
            "CBC":      "CBC (Companhia Brasileira de Cartuchos — ammo)",
        }
    },
    # ── AUSTRALIA ────────────────────────────────────────────────────────────
    "AU": {
        "public": {
            "EOS.AX": "Electro Optic Systems (ASX)",
        },
        "private": {
            "ASC":         "ASC Pty Ltd (submarines)",
            "THALES_AU":   "Thales Australia",
            "BAE_AU":      "BAE Systems Australia",
            "AUSTAL":      "Austal (naval vessels)",
            "DEFENDTEX":   "DefendTex (drone munitions)",
        }
    },
    # ── SAUDI ARABIA ─────────────────────────────────────────────────────────
    "SA": {
        "public": {
            "2380.SR": "Saudi Arabian Military Industries (SAMI) — Tadawul",
        },
        "private": {
            "SAMI":     "Saudi Arabian Military Industries",
            "KACST":    "King Abdulaziz City for Science and Technology",
            "GAMI":     "General Authority for Military Industries",
        }
    },
}

# ── FLAT TICKER LISTS FOR LIVE DATA ──────────────────────────────────────────
# Only publicly listed tickers with reliable yfinance support
LIVE_PRICE_TICKERS = [
    # US
    "LMT", "RTX", "NOC", "GD", "BA", "HII", "LHX", "TXT",
    "LDOS", "BAH", "BWXT", "KTOS", "AVAV", "PLTR", "CACI",
    # Israel
    "ESLT",
    # Europe
    "AIR.PA", "SAF.PA", "HO.PA", "AM.PA",   # France
    "BA.L", "RR.L", "QQ.L",                  # UK
    "RHM.DE", "HEN3.DE",                     # Germany
    "LDO.MI",                                # Italy
    "SAAB-B.ST",                             # Sweden
    # India
    "HAL.NS", "BEL.NS", "SOL.NS", "ASTRA.NS",
    # South Korea
    "047810.KS", "012450.KS",
    # Japan
    "7011.T", "7012.T",
    # Turkey
    "ASELS.IS",
    # Brazil
    "EMBR3.SA",
    # Australia
    "EOS.AX",
]

# Default portfolio shown in the UI (trimmed to most liquid/tracked)
DEFAULT_PORTFOLIO = [
    "LMT", "RTX", "NOC", "GD", "BA", "HII", "LHX",
    "KTOS", "AVAV", "PLTR", "ESLT",
    "BA.L", "RR.L", "AIR.PA", "SAF.PA", "RHM.DE",
    "HAL.NS", "BEL.NS", "SAAB-B.ST", "LDO.MI",
]


def get_stock_data(tickers: list[str] = None) -> dict:
    if tickers is None:
        tickers = DEFAULT_PORTFOLIO
    results = {}
    for ticker in tickers:
        try:
            stock = yf.Ticker(ticker)
            info  = stock.info
            hist  = stock.history(period="5d")

            if hist.empty:
                continue

            current_price = hist["Close"].iloc[-1]
            prev_price    = hist["Close"].iloc[-2] if len(hist) > 1 else current_price
            change_pct    = ((current_price - prev_price) / prev_price) * 100

            # Get country from universe map
            country = "GLOBAL"
            for cc, data in DEFENSE_UNIVERSE.items():
                if ticker in data.get("public", {}):
                    country = cc
                    break

            results[ticker] = {
                "name":       info.get("longName") or _ticker_display_name(ticker),
                "price":      round(current_price, 2),
                "change_pct": round(change_pct, 2),
                "market_cap": info.get("marketCap", 0),
                "sector":     info.get("sector", "Defense"),
                "summary":    info.get("longBusinessSummary", "")[:300],
                "52w_high":   info.get("fiftyTwoWeekHigh", 0),
                "52w_low":    info.get("fiftyTwoWeekLow", 0),
                "volume":     info.get("volume", 0),
                "history_5d": hist["Close"].tolist(),
                "country":    country,
                "currency":   info.get("currency", "USD"),
            }
        except Exception as e:
            results[ticker] = {"error": str(e)}

    return results


def _ticker_display_name(ticker: str) -> str:
    """Fallback display name from the universe map."""
    for cc, data in DEFENSE_UNIVERSE.items():
        if ticker in data.get("public", {}):
            return data["public"][ticker]
    return ticker


# ─────────────────────────────────────────────────────────────────────────────
# EXPOSURE MAP — keyword → per-ticker risk scores (0–100)
# Extended to cover the full global ticker universe.
# US tickers: original scale preserved.
# Non-US tickers: calibrated by export dependency, geographic proximity,
# and historical contract exposure.
# ─────────────────────────────────────────────────────────────────────────────

EXPOSURE_MAP = {
    # ── GEOGRAPHIES ──────────────────────────────────────────────────────────
    "china": {
        # US — tech/supply chain exposure
        "LMT": 70, "RTX": 75, "NOC": 45, "GD": 40, "BA": 65, "KTOS": 30, "AVAV": 25, "PLTR": 20,
        "HII": 35, "LHX": 50, "BWXT": 30,
        # Israel — direct competitor/client
        "ESLT": 60,
        # Europe — Airbus supply chain
        "AIR.PA": 70, "SAF.PA": 55, "HO.PA": 50, "RHM.DE": 30, "HEN3.DE": 45,
        "BA.L": 55, "RR.L": 60, "LDO.MI": 40, "SAAB-B.ST": 35,
        # India — border conflict
        "HAL.NS": 85, "BEL.NS": 80, "SOL.NS": 75, "ASTRA.NS": 70,
        # South Korea
        "047810.KS": 70, "012450.KS": 65,
        # Japan
        "7011.T": 75, "7012.T": 70,
        # Turkey
        "ASELS.IS": 40,
        # Brazil/Australia
        "EMBR3.SA": 30, "EOS.AX": 45,
    },
    "taiwan": {
        "LMT": 80, "RTX": 75, "NOC": 70, "GD": 55, "BA": 50, "KTOS": 40, "AVAV": 35, "PLTR": 25,
        "HII": 60, "LHX": 65,
        "AIR.PA": 65, "SAF.PA": 50, "RHM.DE": 35,
        "BA.L": 60, "RR.L": 55,
        "HAL.NS": 50, "BEL.NS": 45,
        "047810.KS": 80, "012450.KS": 75,
        "7011.T": 85, "7012.T": 80,
        "ASELS.IS": 35, "EMBR3.SA": 20, "EOS.AX": 50,
    },
    "russia": {
        "LMT": 85, "RTX": 80, "NOC": 70, "GD": 65, "BA": 40, "KTOS": 55, "AVAV": 60, "PLTR": 55,
        "HII": 50, "LHX": 70,
        "ESLT": 65,
        "AIR.PA": 70, "SAF.PA": 60, "HO.PA": 55, "AM.PA": 65,
        "BA.L": 75, "RR.L": 65, "QQ.L": 60,
        "RHM.DE": 85, "HEN3.DE": 80, "LDO.MI": 70, "SAAB-B.ST": 75,
        "HAL.NS": 50, "BEL.NS": 45,
        "047810.KS": 55, "7011.T": 45,
        "ASELS.IS": 50, "EMBR3.SA": 20,
    },
    "ukraine": {
        "LMT": 85, "RTX": 80, "NOC": 70, "GD": 65, "BA": 40, "KTOS": 55, "AVAV": 60, "PLTR": 55,
        "HII": 50, "LHX": 70,
        "ESLT": 60,
        "AIR.PA": 65, "HO.PA": 55, "RHM.DE": 90, "HEN3.DE": 85,
        "BA.L": 75, "SAAB-B.ST": 80, "LDO.MI": 65,
        "047810.KS": 50, "ASELS.IS": 55,
    },
    "iran": {
        "LMT": 80, "RTX": 75, "NOC": 70, "GD": 65, "BA": 40, "KTOS": 65, "AVAV": 70, "PLTR": 50,
        "HII": 55, "LHX": 60,
        "ESLT": 90,
        "AIR.PA": 50, "SAF.PA": 45, "HO.PA": 55, "AM.PA": 60,
        "BA.L": 65, "RR.L": 50,
        "RHM.DE": 60, "LDO.MI": 55, "SAAB-B.ST": 45,
        "HAL.NS": 60, "BEL.NS": 55,
        "047810.KS": 40, "7011.T": 35,
        "ASELS.IS": 70,
    },
    "israel": {
        "LMT": 80, "RTX": 75, "NOC": 65, "GD": 60, "BA": 45, "KTOS": 70, "AVAV": 75, "PLTR": 50,
        "HII": 50, "LHX": 65,
        "ESLT": 95,
        "AIR.PA": 55, "HO.PA": 60, "AM.PA": 65,
        "BA.L": 60, "RHM.DE": 55, "LDO.MI": 60,
        "ASELS.IS": 65,
    },
    "india": {
        "HAL.NS": 90, "BEL.NS": 85, "SOL.NS": 80, "ASTRA.NS": 85, "MTAR.NS": 80,
        "LMT": 55, "RTX": 50, "NOC": 45, "GD": 40, "BA": 45,
        "ESLT": 65,
        "AIR.PA": 50, "SAF.PA": 45, "AM.PA": 55,
        "BA.L": 55, "RR.L": 50, "RHM.DE": 45, "SAAB-B.ST": 60, "LDO.MI": 50,
        "7011.T": 40, "7012.T": 35,
    },
    "pakistan": {
        "HAL.NS": 80, "BEL.NS": 75, "SOL.NS": 70,
        "LMT": 40, "RTX": 35, "NOC": 30,
        "ESLT": 55,
        "047810.KS": 45, "012450.KS": 40,
        "ASELS.IS": 60,
    },
    "middle east": {
        "LMT": 80, "RTX": 75, "NOC": 65, "GD": 60, "BA": 45, "KTOS": 65, "AVAV": 70, "PLTR": 50,
        "ESLT": 85,
        "AIR.PA": 60, "SAF.PA": 55, "HO.PA": 60,
        "BA.L": 65, "RR.L": 55, "RHM.DE": 50, "LDO.MI": 55,
        "ASELS.IS": 75,
    },
    "north korea": {
        "LMT": 75, "RTX": 70, "NOC": 65, "GD": 60, "BA": 40, "HII": 55,
        "047810.KS": 90, "012450.KS": 85,
        "7011.T": 80, "7012.T": 75,
        "ESLT": 50,
    },
    "korea":        {"LMT": 70, "RTX": 65, "NOC": 60, "GD": 55, "BA": 40, "KTOS": 45, "AVAV": 40, "PLTR": 30,
                     "047810.KS": 85, "012450.KS": 80, "7011.T": 70, "HII": 60, "LHX": 65},
    "nato":         {"LMT": 85, "RTX": 80, "NOC": 70, "GD": 65, "BA": 45, "KTOS": 50, "AVAV": 55, "PLTR": 60,
                     "RHM.DE": 90, "HEN3.DE": 85, "SAAB-B.ST": 80, "BA.L": 85, "RR.L": 75,
                     "AIR.PA": 70, "LDO.MI": 70, "HII": 65, "LHX": 75},
    "europe":       {"AIR.PA": 85, "SAF.PA": 80, "HO.PA": 75, "AM.PA": 80,
                     "BA.L": 85, "RR.L": 80, "QQ.L": 70,
                     "RHM.DE": 90, "HEN3.DE": 85, "LDO.MI": 80, "SAAB-B.ST": 85,
                     "LMT": 60, "RTX": 55, "NOC": 50},
    "syria":        {"LMT": 70, "RTX": 65, "NOC": 55, "GD": 50, "BA": 30, "KTOS": 55, "AVAV": 60, "PLTR": 40,
                     "ESLT": 70, "ASELS.IS": 65},
    "africa":       {"LMT": 40, "RTX": 35, "BA": 30, "BA.L": 55, "LDO.MI": 60, "EMBR3.SA": 50},
    "gulf":         {"LMT": 80, "RTX": 75, "NOC": 65, "GD": 60, "BA": 55,
                     "ESLT": 75, "ASELS.IS": 70, "BA.L": 70, "AIR.PA": 65},

    # ── EVENT TYPES ──────────────────────────────────────────────────────────
    "attack": {
        "LMT": 85, "RTX": 80, "NOC": 75, "GD": 70, "BA": 45, "KTOS": 70, "AVAV": 75, "PLTR": 55,
        "ESLT": 90, "RHM.DE": 80, "BA.L": 75, "SAAB-B.ST": 70,
        "HAL.NS": 70, "BEL.NS": 65, "047810.KS": 75, "7011.T": 65,
    },
    "war": {
        "LMT": 90, "RTX": 85, "NOC": 80, "GD": 75, "BA": 55, "KTOS": 75, "AVAV": 80, "PLTR": 65,
        "ESLT": 90, "RHM.DE": 90, "HEN3.DE": 85, "BA.L": 85, "SAAB-B.ST": 85,
        "HAL.NS": 80, "BEL.NS": 75, "047810.KS": 80, "7011.T": 75,
        "ASELS.IS": 80, "LDO.MI": 75, "AIR.PA": 70,
    },
    "conflict": {
        "LMT": 85, "RTX": 80, "NOC": 75, "GD": 70, "BA": 50, "KTOS": 70, "AVAV": 75, "PLTR": 55,
        "ESLT": 85, "RHM.DE": 85, "BA.L": 80,
        "HAL.NS": 75, "047810.KS": 75, "ASELS.IS": 75,
    },
    "missile": {
        "LMT": 85, "RTX": 95, "NOC": 75, "GD": 65, "BA": 50, "KTOS": 65, "AVAV": 60, "PLTR": 45,
        "ESLT": 85,
        "AIR.PA": 70, "SAF.PA": 75, "HO.PA": 70, "RHM.DE": 75,
        "BA.L": 75, "LDO.MI": 70, "SAAB-B.ST": 65,
        "HAL.NS": 70, "ASTRA.NS": 80, "047810.KS": 70,
        "ASELS.IS": 80,
    },
    "strike": {
        "LMT": 80, "RTX": 75, "NOC": 70, "GD": 65, "BA": 45, "KTOS": 70, "AVAV": 75, "PLTR": 50,
        "ESLT": 85, "ASELS.IS": 75, "BA.L": 70, "RHM.DE": 70,
    },
    "military": {
        "LMT": 80, "RTX": 75, "NOC": 70, "GD": 65, "BA": 45, "KTOS": 65, "AVAV": 65, "PLTR": 55,
        "ESLT": 80, "RHM.DE": 80, "BA.L": 75, "HAL.NS": 75, "047810.KS": 70,
        "7011.T": 65, "SAAB-B.ST": 70, "LDO.MI": 65, "ASELS.IS": 70,
    },
    "sanctions": {
        "RTX": 65, "BA": 60, "LMT": 50, "GD": 40, "NOC": 35, "KTOS": 25, "AVAV": 25, "PLTR": 20,
        "AIR.PA": 70, "SAF.PA": 60, "RR.L": 65, "BA.L": 55,
        "7011.T": 55, "7012.T": 50,
        "EMBR3.SA": 45,
    },
    "nuclear": {
        "LMT": 75, "RTX": 70, "NOC": 85, "GD": 65, "BA": 55, "KTOS": 60, "AVAV": 50, "PLTR": 45,
        "BWXT": 95,
        "ESLT": 60, "HAL.NS": 55, "BEL.NS": 50,
        "BA.L": 70, "RR.L": 75, "RHM.DE": 65,
    },
    "cyber": {
        "PLTR": 95, "LMT": 70, "NOC": 70, "RTX": 60, "GD": 55, "BA": 35, "KTOS": 50, "AVAV": 35,
        "HO.PA": 80, "BAH": 85, "LDOS": 80, "CACI": 85,
        "ESLT": 75, "BEL.NS": 65, "HEN3.DE": 70,
        "047810.KS": 60, "7011.T": 55,
    },
    "drone": {
        "AVAV": 95, "KTOS": 90, "RTX": 55, "LMT": 50, "BA": 45, "NOC": 40, "GD": 30, "PLTR": 25,
        "ESLT": 80,
        "ASELS.IS": 85,  # Bayraktar adjacent
        "HAL.NS": 65, "ASTRA.NS": 70,
        "EOS.AX": 60,
        "047810.KS": 55, "7011.T": 50,
    },
    "hypersonic": {
        "RTX": 90, "LMT": 85, "NOC": 80, "GD": 65, "BA": 60, "KTOS": 55, "AVAV": 45, "PLTR": 35,
        "HAL.NS": 70,  # BrahMos-II
        "MTAR.NS": 75,
        "7011.T": 60, "012450.KS": 55,
        "AIR.PA": 55, "SAF.PA": 60,
    },
    "loitering": {
        "AVAV": 90, "KTOS": 85, "ESLT": 90,
        "ASELS.IS": 85, "LMT": 45, "RTX": 40,
        "HAL.NS": 55, "ASTRA.NS": 60,
    },
    "naval": {
        "HII": 95, "GD": 80, "BA": 50, "LMT": 55, "RTX": 50, "NOC": 60,
        "BA.L": 70, "RR.L": 75,
        "7011.T": 75, "7012.T": 80,
        "LDO.MI": 70, "SAAB-B.ST": 65,
        "012450.KS": 70, "EMBR3.SA": 40,
    },
    "submarine": {
        "HII": 95, "GD": 90, "RTX": 55, "NOC": 60,
        "BA.L": 75, "RR.L": 80,
        "7011.T": 70, "LDO.MI": 65, "SAAB-B.ST": 70,
    },
    "fighter jet": {
        "LMT": 95, "BA": 70, "NOC": 65, "GD": 60, "RTX": 75,
        "AIR.PA": 85, "AM.PA": 90, "SAF.PA": 80,
        "BA.L": 85, "RR.L": 80,
        "SAAB-B.ST": 85,
        "HAL.NS": 80, "047810.KS": 75, "7011.T": 70,
        "ESLT": 55,
    },
    "artillery": {
        "GD": 80, "RTX": 70, "LMT": 65, "NOC": 55, "BA": 30,
        "RHM.DE": 90, "LDO.MI": 75, "SAAB-B.ST": 65,
        "012450.KS": 80, "7012.T": 70,
        "HAL.NS": 60, "SOL.NS": 70,
    },
    "tank": {
        "GD": 85, "BAH": 45, "RTX": 55,
        "RHM.DE": 90, "LDO.MI": 65,
        "012450.KS": 80, "7012.T": 75,
        "HAL.NS": 55,
    },
    "radar": {
        "RTX": 85, "LMT": 75, "NOC": 80, "GD": 60, "KTOS": 55,
        "HO.PA": 85, "HEN3.DE": 90, "ESLT": 80,
        "BEL.NS": 80, "ASTRA.NS": 85,
        "ASELS.IS": 80, "047810.KS": 70,
    },
    "air defense": {
        "RTX": 90, "LMT": 85, "NOC": 80, "GD": 65, "BA": 50,
        "ESLT": 95,  # Iron Dome/Arrow
        "RHM.DE": 80, "HEN3.DE": 85,
        "SAF.PA": 75, "SAAB-B.ST": 80,
        "HAL.NS": 70, "ASTRA.NS": 75, "047810.KS": 80,
        "ASELS.IS": 80,
    },

    # ── STRATEGIC TOPICS ─────────────────────────────────────────────────────
    "semiconductor":  {"LMT": 70, "RTX": 65, "NOC": 60, "GD": 50, "BA": 45, "KTOS": 35, "AVAV": 30, "PLTR": 20,
                       "HO.PA": 65, "HEN3.DE": 70, "BEL.NS": 60, "7011.T": 65},
    "rare earth":     {"LMT": 75, "RTX": 70, "NOC": 65, "GD": 60, "BA": 55, "KTOS": 45, "AVAV": 40, "PLTR": 15,
                       "RHM.DE": 50, "7011.T": 60, "HAL.NS": 50},
    "contract":       {"LMT": 65, "RTX": 65, "NOC": 65, "GD": 65, "BA": 65, "KTOS": 60, "AVAV": 60, "PLTR": 60,
                       "RHM.DE": 65, "BA.L": 65, "HAL.NS": 65, "ESLT": 65, "SAAB-B.ST": 65},
    "pentagon":       {"LMT": 80, "RTX": 75, "NOC": 70, "GD": 65, "BA": 60, "KTOS": 55, "AVAV": 50, "PLTR": 70,
                       "HII": 65, "LHX": 70, "LDOS": 65, "BAH": 70},
    "budget":         {"LMT": 70, "RTX": 65, "NOC": 65, "GD": 60, "BA": 55, "KTOS": 55, "AVAV": 50, "PLTR": 55,
                       "RHM.DE": 70, "BA.L": 70, "HAL.NS": 70, "SAAB-B.ST": 65},
    "oil":            {"BA": 60, "GD": 55, "LMT": 45, "RTX": 40, "NOC": 35, "KTOS": 30, "AVAV": 25, "PLTR": 20,
                       "ESLT": 50, "ASELS.IS": 45},
    "space":          {"NOC": 85, "LMT": 80, "RTX": 70, "BA": 75, "GD": 50, "PLTR": 65,
                       "AIR.PA": 80, "SAF.PA": 70, "LDO.MI": 65, "SAAB-B.ST": 60,
                       "HAL.NS": 65, "MTAR.NS": 75, "7011.T": 60},
    "ai":             {"PLTR": 95, "NOC": 70, "LMT": 65, "RTX": 60, "BAH": 80, "LDOS": 75,
                       "HO.PA": 70, "HEN3.DE": 65, "BEL.NS": 60, "ESLT": 70},
}


def calculate_risk_scores(tickers: list[str], event_keywords: list[str]) -> dict:
    """
    Calculate exposure risk scores for tickers based on event keywords.
    Supports multi-word keywords (e.g. 'middle east', 'air defense', 'north korea').
    """
    scores           = {ticker: 0 for ticker in tickers}
    matched_keywords = []

    full_query = " ".join(kw.lower() for kw in event_keywords)

    for keyword, exposures in EXPOSURE_MAP.items():
        if keyword in full_query:
            matched_keywords.append(keyword)
            for ticker in tickers:
                if ticker in exposures:
                    scores[ticker] = max(scores[ticker], exposures[ticker])

    results = {}
    for ticker, score in scores.items():
        results[ticker] = {
            "score":            score,
            "risk_level":       "HIGH" if score >= 60 else "MEDIUM" if score >= 30 else "LOW",
            "matched_keywords": matched_keywords
        }

    return results


def get_defense_universe_summary() -> dict:
    """Return a summary of the full defense company universe by country."""
    summary = {}
    for country, data in DEFENSE_UNIVERSE.items():
        summary[country] = {
            "public_count":  len(data.get("public", {})),
            "private_count": len(data.get("private", {})),
            "public_tickers": list(data.get("public", {}).keys()),
            "notable_private": list(data.get("private", {}).keys())[:5],
        }
    return summary


def get_defense_news() -> list[dict]:
    return [
        {"source": "REUTERS",   "time": "2m ago",  "severity": "HIGH", "title": "US Treasury expands OFAC list with Chinese drone component manufacturers",        "tags": ["CHINA","DRONES","OFAC","SANCTIONS"],         "tickers": ["AVAV","KTOS"]},
        {"source": "FT",        "time": "8m ago",  "severity": "MED",  "title": "European defense ministers convene on Baltic sea incidents",                      "tags": ["NATO","EUROPE","DEFENSE"],                   "tickers": ["BA.L","RHM.DE","SAAB-B.ST"]},
        {"source": "HAARETZ",   "time": "11m ago", "severity": "HIGH", "title": "Elbit Systems wins $500M Iron Dome replenishment contract",                       "tags": ["ISRAEL","AIR DEFENSE","CONTRACT"],           "tickers": ["ESLT"]},
        {"source": "ECONOMIC T","time": "15m ago", "severity": "MED",  "title": "HAL delivers 12 Tejas Mk1A jets to Indian Air Force amid border tensions",        "tags": ["INDIA","CHINA","FIGHTER JET"],               "tickers": ["HAL.NS"]},
        {"source": "WSJ",       "time": "18m ago", "severity": "MED",  "title": "Lockheed Martin warns of supply chain disruptions in Q3 earnings",                 "tags": ["LMT","SUPPLY-CHAIN","EARNINGS"],             "tickers": ["LMT"]},
        {"source": "BLOOMBERG", "time": "24m ago", "severity": "LOW",  "title": "Taiwan defense budget to increase 15% amid strait tensions",                      "tags": ["TAIWAN","DEFENSE","BUDGET"],                 "tickers": ["LMT","RTX","NOC","047810.KS"]},
        {"source": "DEFNEWS",   "time": "31m ago", "severity": "HIGH", "title": "Pentagon awards $4.2B JADC2 contract — Palantir, RTX primary vendors",            "tags": ["PLTR","RTX","PENTAGON","CONTRACT"],          "tickers": ["PLTR","RTX"]},
        {"source": "JANE'S",    "time": "38m ago", "severity": "HIGH", "title": "Rheinmetall secures €2.8B German Bundeswehr artillery modernisation contract",     "tags": ["GERMANY","NATO","CONTRACT","ARTILLERY"],     "tickers": ["RHM.DE"]},
        {"source": "NDTV DEF",  "time": "45m ago", "severity": "MED",  "title": "India approves $1.7B BrahMos export deal with Southeast Asian nation",            "tags": ["INDIA","MISSILE","EXPORT"],                 "tickers": ["HAL.NS","BEL.NS"]},
        {"source": "AL MONITOR","time": "52m ago", "severity": "HIGH", "title": "IRGC announces new Shahed-238 jet drone operational deployment",                  "tags": ["IRAN","DRONE","IRGC","THREAT"],             "tickers": ["ESLT","RTX","LMT","AVAV"]},
    ]


def get_active_sanctions() -> list[dict]:
    return [
        {"name": "Zhongshan Broad-Ocean Motor",    "detail": "Drone motor manufacturer, Tier-1 PLA supplier",    "date": "2024-01-15", "category": "DRONE"},
        {"name": "SZ DJI Technology",              "detail": "UAV systems, export controls expanded",            "date": "2024-01-15", "category": "DRONE"},
        {"name": "Fujian Jinhua",                  "detail": "Semiconductor manufacturer, DRAM supply",          "date": "2024-01-10", "category": "SEMICONDUCTOR"},
        {"name": "CNOOC Limited",                  "detail": "Energy sector, secondary sanctions risk",          "date": "2024-01-08", "category": "ENERGY"},
        {"name": "Huawei Technologies",            "detail": "Telecom/chips, all subsidiary entities",           "date": "2023-12-20", "category": "TECH"},
        {"name": "Mahan Air",                      "detail": "Iranian carrier, IRGC logistics support",          "date": "2023-11-05", "category": "IRAN"},
        {"name": "Shahid Hemmat Industrial Group", "detail": "Iranian ballistic missile program",                "date": "2023-10-22", "category": "MISSILE"},
        {"name": "Qods Aviation Industries",       "detail": "Shahed drone manufacturer",                        "date": "2023-10-15", "category": "DRONE"},
        {"name": "IRGC Aerospace Force",           "detail": "Iranian Revolutionary Guard missile/drone ops",    "date": "2023-09-30", "category": "IRAN"},
        {"name": "Rosoboronexport",                "detail": "Russian state arms exporter, full entity block",   "date": "2022-02-24", "category": "RUSSIA"},
        {"name": "Rostec",                         "detail": "Russian defense-industrial state conglomerate",    "date": "2022-02-24", "category": "RUSSIA"},
        {"name": "NORINCO International",          "detail": "Chinese arms exporter, dual-use proliferation",    "date": "2023-06-15", "category": "CHINA"},
        {"name": "Pakistan Ordnance Factories",    "detail": "Arms exports to sanctioned regimes",               "date": "2023-08-10", "category": "PAKISTAN"},
    ]
