"""
Government RSS feed collectors for various federal agencies.

All feeds are public, no authentication required.
"""

import requests
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
import logging
import re

try:
    import feedparser
    HAS_FEEDPARSER = True
except ImportError:
    HAS_FEEDPARSER = False

from .base import BaseCollector


class SECFilingsCollector(BaseCollector):
    """Tracks SEC 8-K filings (material events) from major companies."""

    # SEC EDGAR RSS for 8-K filings
    RSS_URL = "https://www.sec.gov/cgi-bin/browse-edgar?action=getcurrent&type=8-K&company=&dateb=&owner=include&count=100&output=atom"

    def __init__(self, config):
        super().__init__(config)
        self._name = "SECFilings"
        self.logger = logging.getLogger(__name__)

    def collect(self) -> Dict[str, Any]:
        if not HAS_FEEDPARSER:
            return self._get_mock_data()

        try:
            data = self._fetch_filings()
            if data:
                return data
        except Exception as e:
            self.logger.error(f"SEC RSS collection failed: {e}")

        return self._get_mock_data()

    def _fetch_filings(self) -> Optional[Dict[str, Any]]:
        """Fetch recent 8-K filings from SEC."""
        try:
            feed = feedparser.parse(self.RSS_URL)

            if feed.bozo and not feed.entries:
                self.logger.warning("SEC RSS feed parsing failed")
                return None

            # Count filings from last 24 hours
            now = datetime.now()
            recent_count = 0
            material_events = []

            for entry in feed.entries[:100]:
                try:
                    # Check if recent
                    published = entry.get("published_parsed") or entry.get("updated_parsed")
                    if published:
                        pub_date = datetime(*published[:6])
                        if now - pub_date < timedelta(hours=24):
                            recent_count += 1
                            title = entry.get("title", "")
                            material_events.append(title[:100])
                except:
                    continue

            self.logger.info(f"SEC: {recent_count} 8-K filings in last 24h")

            return self._create_reading(
                value=recent_count,
                metadata={
                    "unit": "filings",
                    "source": "SEC EDGAR",
                    "filing_type": "8-K",
                    "recent_filings": material_events[:5],
                    "threshold_amber": 50,
                    "threshold_red": 100,
                    "data_source": "LIVE",
                }
            )

        except Exception as e:
            self.logger.error(f"SEC RSS error: {e}")
            return None

    def _get_mock_data(self) -> Dict[str, Any]:
        return self._create_reading(
            value=35,
            metadata={
                "unit": "filings",
                "source": "mock_data",
                "data_source": "MOCK",
            }
        )

    def validate_data(self, data: Dict[str, Any]) -> bool:
        return data and isinstance(data.get("value"), (int, float))


class FederalRegisterCollector(BaseCollector):
    """Tracks significant federal regulations from Federal Register."""

    # Federal Register API (free, no auth)
    API_URL = "https://www.federalregister.gov/api/v1/documents.json"

    def __init__(self, config):
        super().__init__(config)
        self._name = "FederalRegister"
        self.logger = logging.getLogger(__name__)

    def collect(self) -> Dict[str, Any]:
        try:
            data = self._fetch_regulations()
            if data:
                return data
        except Exception as e:
            self.logger.error(f"Federal Register collection failed: {e}")

        return self._get_mock_data()

    def _fetch_regulations(self) -> Optional[Dict[str, Any]]:
        """Fetch recent significant regulations."""
        try:
            # Get rules from last 7 days
            week_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")

            params = {
                "conditions[publication_date][gte]": week_ago,
                "conditions[type][]": ["RULE", "PRORULE"],  # Final and proposed rules
                "conditions[significant]": 1,  # Significant rules only
                "per_page": 100,
                "order": "newest",
            }

            response = requests.get(self.API_URL, params=params, timeout=15)

            if response.status_code == 200:
                data = response.json()
                results = data.get("results", [])

                # Count by agency
                agency_counts = {}
                for doc in results:
                    agencies = doc.get("agencies", [])
                    for agency in agencies:
                        name = agency.get("name", "Unknown")
                        agency_counts[name] = agency_counts.get(name, 0) + 1

                # Look for DHS/DOJ rules (more concerning for civil liberties)
                dhs_doj_count = sum(
                    1 for doc in results
                    if any("homeland" in str(a).lower() or "justice" in str(a).lower()
                           for a in doc.get("agencies", []))
                )

                self.logger.info(f"Federal Register: {len(results)} significant rules, {dhs_doj_count} DHS/DOJ")

                return self._create_reading(
                    value=len(results),
                    metadata={
                        "unit": "regulations",
                        "source": "Federal Register",
                        "dhs_doj_count": dhs_doj_count,
                        "top_agencies": dict(sorted(agency_counts.items(), key=lambda x: -x[1])[:5]),
                        "threshold_amber": 10,
                        "threshold_red": 25,
                        "data_source": "LIVE",
                    }
                )

            return None

        except Exception as e:
            self.logger.error(f"Federal Register API error: {e}")
            return None

    def _get_mock_data(self) -> Dict[str, Any]:
        return self._create_reading(
            value=5,
            metadata={
                "unit": "regulations",
                "source": "mock_data",
                "data_source": "MOCK",
            }
        )

    def validate_data(self, data: Dict[str, Any]) -> bool:
        return data and isinstance(data.get("value"), (int, float))


class FEMADisasterCollector(BaseCollector):
    """Tracks FEMA disaster declarations."""

    API_URL = "https://www.fema.gov/api/open/v2/DisasterDeclarationsSummaries"

    def __init__(self, config):
        super().__init__(config)
        self._name = "FEMADisaster"
        self.logger = logging.getLogger(__name__)

    def collect(self) -> Dict[str, Any]:
        try:
            data = self._fetch_disasters()
            if data:
                return data
        except Exception as e:
            self.logger.error(f"FEMA collection failed: {e}")

        return self._get_mock_data()

    def _fetch_disasters(self) -> Optional[Dict[str, Any]]:
        """Fetch recent disaster declarations."""
        try:
            # Get disasters from last 30 days
            month_ago = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")

            params = {
                "$filter": f"declarationDate ge '{month_ago}'",
                "$orderby": "declarationDate desc",
                "$top": 100,
            }

            response = requests.get(self.API_URL, params=params, timeout=15)

            if response.status_code == 200:
                data = response.json()
                declarations = data.get("DisasterDeclarationsSummaries", [])

                # Count by type
                type_counts = {}
                states_affected = set()

                for dec in declarations:
                    dec_type = dec.get("incidentType", "Unknown")
                    type_counts[dec_type] = type_counts.get(dec_type, 0) + 1
                    states_affected.add(dec.get("state", ""))

                self.logger.info(f"FEMA: {len(declarations)} disasters in {len(states_affected)} states")

                return self._create_reading(
                    value=len(declarations),
                    metadata={
                        "unit": "declarations",
                        "source": "FEMA",
                        "states_affected": len(states_affected),
                        "by_type": type_counts,
                        "threshold_amber": 10,
                        "threshold_red": 25,
                        "data_source": "LIVE",
                    }
                )

            return None

        except Exception as e:
            self.logger.error(f"FEMA API error: {e}")
            return None

    def _get_mock_data(self) -> Dict[str, Any]:
        return self._create_reading(
            value=5,
            metadata={
                "unit": "declarations",
                "source": "mock_data",
                "data_source": "MOCK",
            }
        )

    def validate_data(self, data: Dict[str, Any]) -> bool:
        return data and isinstance(data.get("value"), (int, float))


class CDCHealthAlertsCollector(BaseCollector):
    """Tracks CDC health alerts and outbreak notices."""

    RSS_URL = "https://tools.cdc.gov/api/v2/resources/media/403372.rss"  # CDC Health Alert Network

    def __init__(self, config):
        super().__init__(config)
        self._name = "CDCHealthAlerts"
        self.logger = logging.getLogger(__name__)

    def collect(self) -> Dict[str, Any]:
        if not HAS_FEEDPARSER:
            return self._get_mock_data()

        try:
            data = self._fetch_alerts()
            if data:
                return data
        except Exception as e:
            self.logger.error(f"CDC RSS collection failed: {e}")

        return self._get_mock_data()

    def _fetch_alerts(self) -> Optional[Dict[str, Any]]:
        """Fetch CDC health alerts."""
        try:
            # Try multiple CDC RSS feeds
            feeds = [
                "https://tools.cdc.gov/api/v2/resources/media/403372.rss",
                "https://www.cdc.gov/media/rss/mmwr.xml",
            ]

            total_alerts = 0
            recent_alerts = []

            for feed_url in feeds:
                try:
                    feed = feedparser.parse(feed_url)
                    for entry in feed.entries[:20]:
                        try:
                            published = entry.get("published_parsed")
                            if published:
                                pub_date = datetime(*published[:6])
                                if datetime.now() - pub_date < timedelta(days=30):
                                    total_alerts += 1
                                    recent_alerts.append(entry.get("title", "")[:100])
                        except:
                            continue
                except:
                    continue

            self.logger.info(f"CDC: {total_alerts} health alerts in last 30d")

            return self._create_reading(
                value=total_alerts,
                metadata={
                    "unit": "alerts",
                    "source": "CDC",
                    "recent": recent_alerts[:3],
                    "threshold_amber": 5,
                    "threshold_red": 15,
                    "data_source": "LIVE",
                }
            )

        except Exception as e:
            self.logger.error(f"CDC RSS error: {e}")
            return None

    def _get_mock_data(self) -> Dict[str, Any]:
        return self._create_reading(
            value=2,
            metadata={
                "unit": "alerts",
                "source": "mock_data",
                "data_source": "MOCK",
            }
        )

    def validate_data(self, data: Dict[str, Any]) -> bool:
        return data and isinstance(data.get("value"), (int, float))


class FDAShortagesCollector(BaseCollector):
    """Tracks FDA drug shortage announcements."""

    API_URL = "https://api.fda.gov/drug/drugsfda.json"

    def __init__(self, config):
        super().__init__(config)
        self._name = "FDAShortages"
        self.logger = logging.getLogger(__name__)

    def collect(self) -> Dict[str, Any]:
        try:
            data = self._fetch_shortages()
            if data:
                return data
        except Exception as e:
            self.logger.error(f"FDA collection failed: {e}")

        return self._get_mock_data()

    def _fetch_shortages(self) -> Optional[Dict[str, Any]]:
        """Fetch FDA drug shortage data by scraping the shortage list."""
        try:
            # FDA drug shortage page
            response = requests.get(
                "https://www.accessdata.fda.gov/scripts/drugshortages/default.cfm",
                headers={"User-Agent": "Canairy/1.0"},
                timeout=15
            )

            if response.status_code == 200:
                text = response.text

                # Count shortage entries (rough estimate from page)
                shortage_count = text.lower().count("shortage") // 2  # Rough estimate
                shortage_count = min(shortage_count, 200)  # Cap

                # Look for critical shortages
                critical = text.lower().count("critical") + text.lower().count("discontinued")

                self.logger.info(f"FDA: ~{shortage_count} drug shortages, {critical} critical")

                return self._create_reading(
                    value=shortage_count,
                    metadata={
                        "unit": "shortages",
                        "source": "FDA",
                        "critical_count": critical,
                        "threshold_amber": 50,
                        "threshold_red": 100,
                        "data_source": "LIVE",
                    }
                )

            return None

        except Exception as e:
            self.logger.error(f"FDA scrape error: {e}")
            return None

    def _get_mock_data(self) -> Dict[str, Any]:
        return self._create_reading(
            value=45,
            metadata={
                "unit": "shortages",
                "source": "mock_data",
                "data_source": "MOCK",
            }
        )

    def validate_data(self, data: Dict[str, Any]) -> bool:
        return data and isinstance(data.get("value"), (int, float))


class GovTrackBillsCollector(BaseCollector):
    """Tracks congressional bill activity via GovTrack RSS."""

    RSS_URL = "https://www.govtrack.us/events/events.rss?feeds=misc%3Aallvotes"

    def __init__(self, config):
        super().__init__(config)
        self._name = "GovTrackBills"
        self.logger = logging.getLogger(__name__)

    def collect(self) -> Dict[str, Any]:
        if not HAS_FEEDPARSER:
            return self._get_mock_data()

        try:
            data = self._fetch_activity()
            if data:
                return data
        except Exception as e:
            self.logger.error(f"GovTrack collection failed: {e}")

        return self._get_mock_data()

    def _fetch_activity(self) -> Optional[Dict[str, Any]]:
        """Fetch congressional activity from GovTrack."""
        try:
            feed = feedparser.parse(self.RSS_URL)

            if feed.bozo and not feed.entries:
                return None

            # Count recent votes/actions
            now = datetime.now()
            recent_votes = 0
            recent_items = []

            for entry in feed.entries[:50]:
                try:
                    published = entry.get("published_parsed")
                    if published:
                        pub_date = datetime(*published[:6])
                        if now - pub_date < timedelta(days=7):
                            recent_votes += 1
                            recent_items.append(entry.get("title", "")[:100])
                except:
                    continue

            self.logger.info(f"GovTrack: {recent_votes} congressional actions in last 7d")

            return self._create_reading(
                value=recent_votes,
                metadata={
                    "unit": "actions",
                    "source": "GovTrack",
                    "recent": recent_items[:3],
                    "threshold_amber": 20,
                    "threshold_red": 50,
                    "data_source": "LIVE",
                }
            )

        except Exception as e:
            self.logger.error(f"GovTrack RSS error: {e}")
            return None

    def _get_mock_data(self) -> Dict[str, Any]:
        return self._create_reading(
            value=15,
            metadata={
                "unit": "actions",
                "source": "mock_data",
                "data_source": "MOCK",
            }
        )

    def validate_data(self, data: Dict[str, Any]) -> bool:
        return data and isinstance(data.get("value"), (int, float))
