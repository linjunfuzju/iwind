from pydantic import BaseModel, Field
from typing import Optional
from deepwind_app.tool.base import BaseTool

class OpenSeesTrussAnalysis(BaseTool):
    name: str = "opensees_truss_analysis"
    description: str = """Run a 2D truss nonlinear analysis with OpenSeesPy."""
    parameters: dict = {
        "type": "object",
        "properties": {
            "A": {
                "type": "number",
                "description": "Cross-sectional area (default: 4.0 in²)"
            },
            "E": {
                "type": "number",
                "description": "Elastic modulus (default: 29000.0 ksi)"
            },
            "alpha": {
                "type": "number",
                "description": "Hardening parameter (default: 0.05)",
                "minimum": 0.01,
                "maximum": 0.2
            },
            "sY": {
                "type": "number",
                "description": "Yield stress (default: 36.0 ksi)"
            },
            "udisp": {
                "type": "number",
                "description": "Maximum displacement (default: 2.5 in)"
            },
            "Nsteps": {
                "type": "integer",
                "description": "Number of analysis steps (default: 1000)"
            },
            "Px": {
                "type": "number",
                "description": "Horizontal load (default: 160.0 kips)"
            },
            "Py": {
                "type": "number",
                "description": "Vertical load (default: 0.0 kips)"
            }
        }
    }