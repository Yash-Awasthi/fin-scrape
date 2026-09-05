from dataclasses import dataclass


@dataclass(frozen=True)
class Role:
    name: str
    model: str
    lineage: str = ""


DEFAULT_COUNCIL_HEAD = Role("Council_Head", "anthropic/claude-sonnet-4.6", "Anthropic")

DEFAULT_COUNCIL_MEMBERS: list[Role] = [
    Role("Council_Member_Claude", "anthropic/claude-sonnet-4.6", "Anthropic"),
    Role("Council_Member_Kimi", "moonshotai/kimi-k2.5", "Moonshot"),
    Role("Council_Member_Grok", "x-ai/grok-4.20", "xAI"),
]

DEFAULT_REPORT_AUTHOR = Role("Report_Author", "anthropic/claude-sonnet-4.6", "Anthropic")

DEFAULT_HORIZONS: list[str] = ["24h", "1w", "1m"]

DEFAULT_RSS_FEEDS: list[str] = [
    "https://www.timesofisrael.com/feed/",
    "https://www.aljazeera.com/xml/rss/all.xml",
    "https://feeds.bbci.co.uk/news/world/rss.xml",
    "https://www.maariv.co.il/rss/rsschadashot",
    "https://en.mehrnews.com/rss",
    "https://www.centcom.mil/DesktopModules/ArticleCS/RSS.ashx?ContentType=1&Site=1075&max=10",
    "https://www.twz.com/feed",
]

PREDICTIONS_PER_HORIZON = 3

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

GROUNDING_DOMAINS_IRAN_ISRAEL: list[str] = [
    "idf.il", "mfa.gov.il", "state.gov", "centcom.mil", "nato.int",
    "mfa.ir", "irna.ir", "tasnimnews.com", "almasirah.net.ye", "almanar.com.lb",
    "lebarmy.gov.lb", "unifil.unmissions.org", "iaea.org", "news.un.org", "un.org",
    "timesofisrael.com", "haaretz.com", "aljazeera.com", "alarabiya.net",
    "arabnews.com", "israelnationalnews.com",
    "understandingwar.org", "bellingcat.com", "acleddata.com",
    "longwarjournal.org", "iransitrep.com",
    "washingtoninstitute.org", "inss.org.il", "fdd.org", "crisisgroup.org",
    "responsiblestatecraft.org",
    "iranintl.com", "iranwire.com", "syriahr.com",
    "reuters.com", "apnews.com", "afp.com", "bloomberg.com",
    "nytimes.com", "washingtonpost.com", "wsj.com", "ft.com",
    "bbc.com", "bbc.co.uk", "cnn.com", "theguardian.com", "economist.com",
    "axios.com", "politico.com", "foreignpolicy.com",
]

