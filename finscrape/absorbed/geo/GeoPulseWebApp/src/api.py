import json
import os
from src.utils import _make_client, clean_json, sanitize_input

try:
    from camel.societies import RolePlaying
    from camel.models import ModelFactory
    from camel.types import ModelPlatformType, ModelType
    CAMEL_AVAILABLE = True
except ImportError:
    CAMEL_AVAILABLE = False

def fetch_analysis(c1, c2, key, base_url, model):
    if not key: return {"error": "API Key is missing."}
    client = _make_client(key, base_url)
    
    system_prompt = """
    You are a Strategic Intelligence Algorithm. Return STRICT JSON.
    
    TASK:
    Analyze the relationship between two nations at TWO points in time:
    1. CURRENT (Now)
    2. PAST (Exactly 1 Year Ago)
    
    SCORING (0-100):
    0-20: Alliance | 21-40: Neutral | 41-60: Strained | 61-80: Hostile | 81-100: Conflict
    
    REQUIRED JSON STRUCTURE:
    {
        "c1_flag": "Emoji", "c2_flag": "Emoji",
        "score_current": Integer (0-100),
        "score_past": Integer (0-100),
        "status_label": "String (e.g. Deteriorating, Improving, Stable)",
        "change_reason": "String (Why did the score change from last year? Max 1 sentence)",
        "summary": "String (Executive summary of current situation)",
        "main_driver": "String (Current primary conflict driver)",
        "trade_deficit": "Float OR String (e.g. 15.2 or 'No Data')",
        "trade_context": "String (e.g. 'US deficit with China')",
        "news": [{"date": "YYYY-MM-DD", "title": "Headline", "source": "Source"}]
    }
    """
    
    clean_c1 = sanitize_input(c1)
    clean_c2 = sanitize_input(c2)
    user_prompt = (
        f"Analyze {clean_c1} vs {clean_c2}. compare TODAY vs 1 YEAR AGO. "
        "Provide specific tension scores for both timeframes. "
        "For trade_deficit, provide a single number in Billions (USD)."
    )
    
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
        )
        data = clean_json(response.choices[0].message.content)
        if not data: return {"error": "Failed to parse AI response."}
        return data
    except Exception as e:
        return {"error": str(e)}

def fetch_global_rankings(key, base_url, model):
    if not key: return None
    client = _make_client(key, base_url)
    
    system_prompt = """
    Return STRICT JSON with 'highest_pressure' and 'lowest_pressure' (10 items each).
    Item: {"pair": "Name vs Name", "score": Int (0-100), "reason": "Context"}
    """
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": "Global Geopolitical Rankings 2025"}]
        )
        return clean_json(response.choices[0].message.content)
    except Exception as e: return {"error": str(e)}

def fetch_market_risk(commodity, key, base_url, model):
    if not key: return {"error": "API Key Missing"}
    client = _make_client(key, base_url)
    
    # Load verified data
    verified_data = {}
    producer_source = "Unknown Source"
    refiner_source = "Unknown Source"
    choke_point_source = "Unknown Source"
    verified_producers_str = "No verified data found. Use your own knowledge."
    verified_refiners_str = "No verified data found. Use your own knowledge."
    verified_choke_points_str = "No verified data found. Use your own knowledge."
    try:
        file_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'verified_production.json')
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                verified_data = json.load(f)
            
            if commodity in verified_data:
                item = verified_data[commodity]
                producer_source = item.get("producer_source", item.get("source", "Unknown Source"))
                refiner_source = item.get("refiner_source", "Unknown Source")
                choke_point_source = item.get("choke_point_source", "Unknown Source")
                
                producers = item.get("producers", [])
                verified_producers_str = f"VERIFIED PRODUCERS FOR {commodity} (Source: {producer_source}):\n"
                for p in producers:
                    verified_producers_str += f"- {p['country']} (Share: {p['share']})\n"
                    
                refiners = item.get("refiners", [])
                verified_refiners_str = f"VERIFIED REFINERS/PROCESSORS FOR {commodity} (Source: {refiner_source}):\n"
                for r in refiners:
                    verified_refiners_str += f"- {r['country']} (Share: {r['share']})\n"
                    
                choke_points = item.get("choke_points", [])
                verified_choke_points_str = f"VERIFIED CHOKE POINTS FOR {commodity} (Source: {choke_point_source}):\n"
                for c in choke_points:
                    verified_choke_points_str += f"- {c['name']} (Volume: {c['volume_flow']}, Reliance: {c['reliance_level']})\n"
    except Exception as e:
        pass
        
    system_prompt = f"""
    You are a Global Commodity Risk Analyst. Return STRICT JSON.
    
    TASK:
    1. A list of VERIFIED top producing countries and their production shares is provided below. You MUST use EXACTLY these countries and production shares.
    2. A list of VERIFIED top refining/processing countries and their shares is provided below. You MUST use EXACTLY these countries and shares.
    3. Analyze the CURRENT geopolitical tension/conflict level for each of these provided producer and refiner countries.
    4. Calculate a "Supply Chain Risk Score" (0-100) for that commodity based on the stability of these key producers and refiners.
    5. Predict price impact purely based on geopolitical risk (Bullish=Prices Up/Risk High, Bearish=Prices Down/Oversupply).
    6. A list of VERIFIED critical logistical shipping routes or "Choke Points" is provided below. You MUST use EXACTLY these choke points. Evaluate the current threat to each.
    
    {verified_producers_str}
    
    {verified_refiners_str}
    
    {verified_choke_points_str}
    
    REQUIRED JSON STRUCTURE:
    {{
        "commodity": "String",
        "global_risk_score": Integer (0-100),
        "price_outlook": "String (e.g. 'Bullish', 'Bearish', 'Volatile')",
        "outlook_reason": "String (Short explanation of price prediction)",
        "top_producers": [
            {{
                "country": "String (Must match provided list exactly)",
                "production_share": "String (Must match provided list exactly)",
                "tension_index": Integer (0-100),
                "risk_note": "String (Specific conflict impacting supply, e.g. 'Red Sea shipping attacks')"
            }}
        ],
        "top_refiners": [
            {{
                "country": "String (Must match provided list exactly)",
                "production_share": "String (Must match provided list exactly)",
                "tension_index": Integer (0-100),
                "risk_note": "String (Specific conflict impacting refining/processing)"
            }}
        ],
        "choke_points": [
            {{
                "name": "String (Must match provided list exactly)",
                "reliance_level": "String (Must match provided list exactly)",
                "volume_flow": "String (Must match provided list exactly)",
                "current_threat": "String (Context of risk to this route)",
                "threat_score": Integer (0-100)
            }}
        ]
    }}
    """
    
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Analyze Supply Chain Risk for: {sanitize_input(commodity, 100)}"}
            ]
        )
        result = clean_json(response.choices[0].message.content)
        if isinstance(result, dict):
            result["producer_source"] = producer_source
            result["refiner_source"] = refiner_source
            result["choke_point_source"] = choke_point_source
        return result
    except Exception as e:
        return {"error": str(e)}

def generate_dynamic_graph_data(event_description, key, base_url, model):
    if not key: return {"error": "API Key is missing."}
    client = _make_client(key, base_url)
    
    system_prompt = """
    You are an expert supply chain analyst and systems dynamics modeler. Return STRICT JSON.
    
    TASK:
    Given a Black Swan event description, map out a complex, multi-tiered supply chain reaction network.
    Show how the event cascades through different entities (Logistics, Industry, Sellers, Consumers, Governments, Commodities).
    
    Generate at least 12-15 interconnected nodes and edges.
    
    REQUIRED JSON STRUCTURE:
    {
        "nodes": [
            {
                "id": "String (Unique identifier, e.g. 'Event', 'Maersk', 'EU_Auto', 'Consumers')",
                "label": "String (Display name, e.g. 'Suez Blockage', 'Global Shippers')",
                "group": "String (Must be one of: 'Event', 'Logistics', 'Industry', 'Retail', 'Consumer', 'Commodity', 'Government')"
            }
        ],
        "edges": [
            {
                "source": "String (Must match a node id)",
                "target": "String (Must match a node id)",
                "label": "String (Action/Reaction, e.g. 'HALTS', 'DELAYS_PARTS', 'PANIC_BUYS', 'INCREASES_COST')"
            }
        ]
    }
    """
    
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Map the cascading supply chain reactions for this event: {sanitize_input(event_description, 200)}"}
            ]
        )
        return clean_json(response.choices[0].message.content)
    except Exception as e:
        return {"error": str(e)}

def expand_dynamic_graph_data(existing_graph_json, key, base_url, model):
    if not key: return {"error": "API Key is missing."}
    client = _make_client(key, base_url)
    
    system_prompt = """
    You are an expert supply chain analyst and systems dynamics modeler. Return STRICT JSON.
    
    TASK:
    You will be provided with an existing JSON graph of a supply chain reaction network.
    Your job is to ITERATE and EXPAND the graph by identifying the "leaf nodes" (nodes that don't have many outgoing edges) and generating 5-10 NEW cascading consequences that stem from them.
    
    Do NOT return the old nodes and edges. Return ONLY the NEW nodes and NEW edges.
    Make sure the 'source' of your new edges exactly matches the 'id' of existing nodes in the provided graph, or the 'id' of new nodes you create.
    
    REQUIRED JSON STRUCTURE:
    {
        "nodes": [
            {
                "id": "String",
                "label": "String",
                "group": "String (Must be one of: 'Event', 'Logistics', 'Industry', 'Retail', 'Consumer', 'Commodity', 'Government')"
            }
        ],
        "edges": [
            {
                "source": "String",
                "target": "String",
                "label": "String"
            }
        ]
    }
    """
    
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Here is the existing graph. Expand it by adding new cascading reactions:\n{json.dumps(existing_graph_json)}"}
            ]
        )
        return clean_json(response.choices[0].message.content)
    except Exception as e:
        return {"error": str(e)}

def run_oasis_panic_simulation(scenario, api_key, model_choice, base_url=None):
    if not CAMEL_AVAILABLE:
        return [{"role": "System", "content": "CAMEL-AI library is not installed."}]
    if not api_key:
        return [{"role": "System", "content": "API Key is missing."}]
        
    try:
        if "gemini" in model_choice.lower():
            camel_model_type = ModelType.GEMINI_2_5_FLASH
            if "pro" in model_choice.lower() and "2.5" in model_choice.lower():
                camel_model_type = ModelType.GEMINI_2_5_PRO
            model = ModelFactory.create(
                model_platform=ModelPlatformType.GEMINI,
                model_type=camel_model_type,
                api_key=api_key,
                model_config_dict={"temperature": 0.7}
            )
        else:
            # Route all other providers (Perplexity, DeepSeek, OpenAI) through the OpenAI-compatible default platform
            kwargs = {
                "model_platform": ModelPlatformType.DEFAULT,
                "model_type": model_choice, # CAMEL accepts raw model strings for custom endpoints
                "api_key": api_key,
                "model_config_dict": {"temperature": 0.7}
            }
            if base_url:
                kwargs["url"] = base_url
            model = ModelFactory.create(**kwargs)
            
    except Exception as e:
        return [{"role": "System", "content": f"Failed to init model: {str(e)}"}]

    task_prompt = (
        f"A major global crisis has occurred: {scenario}. "
        "Discuss the immediate impact on local supply chains, what items will run out first, and how consumers are reacting."
    )
    
    try:
        role_play_session = RolePlaying(
            assistant_role_name="Local Retail Store Manager",
            user_role_name="Anxious Consumer",
            assistant_agent_kwargs=dict(model=model),
            user_agent_kwargs=dict(model=model),
            task_prompt=task_prompt,
            with_task_specify=False
        )
        
        chat_history = []
        input_msg = role_play_session.init_chat()
        
        chat_turn_limit = 3
        for _ in range(chat_turn_limit):
            assistant_response, user_response = role_play_session.step(input_msg)
            
            # Record user (Consumer)
            chat_history.append({
                "role": "Consumer", 
                "content": user_response.msg.content.replace("Instruction:", "").strip()
            })
            
            # Record assistant (Manager)
            chat_history.append({
                "role": "Manager", 
                "content": assistant_response.msg.content
            })
            
            input_msg = assistant_response.msg
            
            if "TERMINATE" in assistant_response.msg.content:
                break
                
        return chat_history
    except Exception as e:
        return [{"role": "System", "content": f"Simulation Error: {str(e)}"}]
