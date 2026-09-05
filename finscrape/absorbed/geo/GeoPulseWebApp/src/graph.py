import os
import tempfile
from pyvis.network import Network

def generate_impact_network(scenario_name, graph_data):
    if not graph_data or not isinstance(graph_data, dict):
        raise ValueError("generate_impact_network received invalid graph_data (None or non-dict).")
    # Clean off-white professional background
    net = Network(height="850px", width="100%", bgcolor="#f4f6f8", font_color="#2c3e50", select_menu=False, cdn_resources='remote')
    
    # Well-spaced, stable physics layout
    net.force_atlas_2based(gravity=-55, central_gravity=0.012, spring_length=200, spring_strength=0.055, damping=0.5, overlap=0.8)
    
    # Professional color palette (bg, border)
    group_colors = {
        "Event":      ("#c0392b", "#922b21"),
        "Logistics":  ("#2471a3", "#1a5276"),
        "Industry":   ("#ca6f1e", "#a04000"),
        "Retail":     ("#b7950b", "#9a7d0a"),
        "Consumer":   ("#7d3c98", "#6c3483"),
        "Commodity":  ("#1e8449", "#196f3d"),
        "Government": ("#566573", "#4d5656"),
    }
    
    if "nodes" in graph_data and "edges" in graph_data:
        # Pre-compute degree for proportional node sizing
        degree = {}
        for edge in graph_data["edges"]:
            for key in ("source", "target"):
                nid = edge.get(key)
                if nid:
                    degree[nid] = degree.get(nid, 0) + 1

        for node in graph_data["nodes"]:
            n_id  = node.get("id", "")
            label = node.get("label", n_id)
            group = node.get("group", "Industry")
            bg, border = group_colors.get(group, ("#95a5a6", "#7f8c8d"))
            node_degree = degree.get(n_id, 1)
            
            if group == "Event":
                # Prominent labeled box for the root event
                net.add_node(
                    n_id,
                    label=f"⚡  {label}",
                    title=f"ROOT EVENT: {label}",
                    shape="box",
                    color={"background": bg, "border": border,
                           "highlight": {"background": "#e74c3c", "border": border},
                           "hover":     {"background": "#e74c3c", "border": border}},
                    font={"size": 15, "face": "Segoe UI, sans-serif", "color": "#ffffff", "bold": True},
                    margin={"top": 12, "bottom": 12, "left": 16, "right": 16},
                    borderWidth=3,
                    shadow={"enabled": True, "color": "rgba(192,57,43,0.4)", "size": 12, "x": 3, "y": 3}
                )
            else:
                # Degree-proportional dots; label floats neatly beneath
                size = max(18, min(48, 16 + node_degree * 5))
                net.add_node(
                    n_id,
                    label=label,
                    title=f"{group}  |  {node_degree} connection{'s' if node_degree != 1 else ''}",
                    shape="dot",
                    size=size,
                    color={"background": bg, "border": border,
                           "highlight": {"background": bg,     "border": "#2c3e50"},
                           "hover":     {"background": border, "border": "#2c3e50"}},
                    font={"size": 12, "face": "Segoe UI, sans-serif", "color": "#1a1a2e",
                          "bold": True, "vadjust": size + 10},
                    borderWidth=2,
                    shadow={"enabled": True, "color": "rgba(0,0,0,0.10)", "size": 5, "x": 2, "y": 2}
                )
            
        for edge in graph_data["edges"]:
            src = edge.get("source")
            tgt = edge.get("target")
            lbl = edge.get("label", "")
            if src and tgt:
                # Labels in tooltip — keeps the canvas completely clean
                net.add_edge(
                    src, tgt,
                    label="",
                    title=lbl,
                    color={"color": "#c5cdd2", "highlight": "#566573", "hover": "#566573"},
                    arrows={"to": {"enabled": True, "scaleFactor": 0.55, "type": "arrow"}},
                    smooth={"type": "dynamic"},
                    width=1.5,
                    hoverWidth=3
                )
                
    # Write to a temporary file, read into memory, then delete immediately.
    # This avoids persistent HTML artifacts accumulating in the temp directory.
    with tempfile.NamedTemporaryFile(suffix=".html", delete=False, mode="w", encoding="utf-8") as tmp:
        tmp_path = tmp.name
    net.save_graph(tmp_path)
    with open(tmp_path, "r", encoding="utf-8") as f:
        html_content = f.read()
    try:
        os.remove(tmp_path)
    except OSError:
        pass  # Non-critical if cleanup fails
    return html_content
