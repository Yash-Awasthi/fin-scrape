# reranker/model.py - PyTorch re-ranker trained on REAL document pairs

import torch
import torch.nn as nn
import os, json

MODEL_PATH = "./reranker/reranker_weights.pt"

class ReRanker(nn.Module):
    def __init__(self, input_dim=18):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, 64), nn.ReLU(), nn.Dropout(0.1),
            nn.Linear(64, 32), nn.ReLU(),
            nn.Linear(32, 1), nn.Sigmoid()
        )
    def forward(self, x):
        return self.net(x)

DEFENSE_TERMS = ["lockheed","raytheon","northrop","boeing","general dynamics","missile","aircraft","drone","uav","weapon","radar","f-35","patriot","himars","javelin","abrams","submarine","contract","award","pentagon","dod","department of defense","10-k","annual report","revenue","segment","backlog"]
SANCTIONS_TERMS = ["ofac","sdn","sanction","restrict","ban","export control","entity list","blocked","designated","treasury","compliance"]
GEO_TERMS = ["china","chinese","russia","russian","iran","north korea","taiwan","ukraine","nato","indo-pacific","europe","middle east"]
FINANCE_TERMS = ["stock","equity","share","market cap","earnings","revenue","exposure","risk","portfolio","etf","sector","valuation"]
TICKERS = ["LMT","RTX","NOC","GD","BA","KTOS","AVAV","PLTR","HII"]

def extract_features(query, document):
    q, d = query.lower(), document.lower()
    q_words, d_words = set(q.split()), set(d.split())
    def overlap(terms, text): return sum(1 for t in terms if t in text)/max(len(terms),1)
    def shared(s1, s2): return len(s1&s2)/max(len(s1),1)
    return torch.tensor([
        overlap(DEFENSE_TERMS,q)*overlap(DEFENSE_TERMS,d), overlap(DEFENSE_TERMS,d),
        overlap(SANCTIONS_TERMS,q)*overlap(SANCTIONS_TERMS,d), overlap(SANCTIONS_TERMS,d),
        overlap(GEO_TERMS,q)*overlap(GEO_TERMS,d), overlap(GEO_TERMS,d),
        overlap(FINANCE_TERMS,q)*overlap(FINANCE_TERMS,d),
        sum(1 for t in TICKERS if t in query.upper() and t in document.upper())/len(TICKERS),
        sum(1 for t in TICKERS if t in document.upper())/len(TICKERS),
        float("sec edgar" in d or "10-k" in d), float("ofac" in d or "sdn" in d),
        float("federal register" in d), shared(q_words,d_words),
        min(len(d.split())/150,1.0), min(len(q.split())/30,1.0),
        float(any(t in query.upper() for t in TICKERS)),
        float("%" in d or "$" in d), float(any(y in d for y in ["2023","2024","2025"]))
    ], dtype=torch.float32)

def generate_real_training_data():
    from tools.data_fetcher import fetch_all_sec_filings, fetch_ofac_sanctions, fetch_federal_register_notices
    pairs = []
    for f in fetch_all_sec_filings():
        text = f"{f['company']} ({f['ticker']}) {f['description']}"
        pairs += [
            {"query":f"{f['ticker']} defense stock exposure risk","doc":text,"label":0.95},
            {"query":f"{f['company']} annual report defense contracts","doc":text,"label":0.90},
            {"query":"defense spending NATO military contracts","doc":text,"label":0.60},
            {"query":"cryptocurrency bitcoin blockchain","doc":text,"label":0.05},
        ]
    for s in fetch_ofac_sanctions(max_entries=15):
        text = f"OFAC SDN: {s['name']}. Type: {s['type']}. {s['detail']}"
        pairs += [
            {"query":"OFAC sanctions list China Russia defense","doc":text,"label":0.92},
            {"query":"sanctioned entities export control compliance","doc":text,"label":0.88},
            {"query":"stock price earnings revenue growth","doc":text,"label":0.10},
        ]
    for n in fetch_federal_register_notices(max_results=10):
        text = f"{n['title']}. {n['abstract']}"
        if len(text.strip()) < 20: continue
        pairs += [
            {"query":"Pentagon defense procurement contract award","doc":text,"label":0.85},
            {"query":"government defense spending military budget","doc":text,"label":0.80},
            {"query":"Chinese drone sanctions stock market","doc":text,"label":0.30},
        ]
    print(f"[PyTorch] Generated {len(pairs)} real training pairs")
    return pairs

def train_reranker(epochs=200):
    print("[PyTorch] Training re-ranker on real defense-finance data...")
    pairs = generate_real_training_data()
    if not pairs:
        return ReRanker(input_dim=18)
    os.makedirs("./reranker", exist_ok=True)
    with open("./reranker/training_data.json","w") as f:
        json.dump(pairs[:20],f,indent=2)
    model = ReRanker(input_dim=18)
    opt = torch.optim.Adam(model.parameters(), lr=0.001, weight_decay=1e-4)
    crit = nn.BCELoss()
    sched = torch.optim.lr_scheduler.StepLR(opt, step_size=50, gamma=0.5)
    X = torch.stack([extract_features(p["query"],p["doc"]) for p in pairs])
    y = torch.tensor([[p["label"]] for p in pairs], dtype=torch.float32)
    model.train()
    for epoch in range(epochs):
        opt.zero_grad()
        loss = crit(model(X), y)
        loss.backward(); opt.step(); sched.step()
        if (epoch+1)%50==0: print(f"[PyTorch] Epoch {epoch+1}/{epochs} Loss:{loss.item():.4f}")
    torch.save(model.state_dict(), MODEL_PATH)
    print(f"[PyTorch] Saved to {MODEL_PATH}")
    return model

_model = None
def load_model():
    global _model
    if _model is None:
        _model = ReRanker(input_dim=18)
        if os.path.exists(MODEL_PATH):
            _model.load_state_dict(torch.load(MODEL_PATH, weights_only=True))
            print("[PyTorch] Re-ranker loaded")
        else:
            _model = train_reranker()
        _model.eval()
    return _model

def rerank(query, documents):
    if not documents: return documents
    model = load_model()
    scored = []
    with torch.no_grad():
        for doc in documents:
            score = model(extract_features(query,doc["text"]).unsqueeze(0)).item()
            scored.append({**doc,"rerank_score":round(score,4)})
    scored.sort(key=lambda x:x["rerank_score"],reverse=True)
    for i,doc in enumerate(scored): doc["rank"]=i+1
    return scored
