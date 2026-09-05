"""Accuracy evaluation & self-healing subsystem.

Walks checkpointed forecast runs, records each prediction with its absolute
horizon target timestamp, and — once the horizon has elapsed — asks an
evaluator model (default Gemini Flash) to verdict the prediction against
fresh grounding. Aggregates per-model accuracy and calibration over time.
"""
