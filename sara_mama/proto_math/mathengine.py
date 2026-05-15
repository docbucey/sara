# mathengine.py
"""
Mathematics Engine Pointer Hub
- Auto-discovers math layer files named layer_<number>_<domain>.py
- Dynamically imports them and exposes their functions
"""

import importlib
import pkgutil
import os

class MathematicsEngine:
    def __init__(self, layers_package="layers"):
        self.layers = {}
        package_path = os.path.join(os.path.dirname(__file__), layers_package)

        # Auto-discover all modules starting with "layer_"
        for _, module_name, _ in pkgutil.iter_modules([package_path]):
            if module_name.startswith("layer_"):
                module = importlib.import_module(f"{layers_package}.{module_name}")
                self.layers[module_name] = module

    def get_layer(self, layer_name):
        """
        Retrieve a layer module by name.
        Example: engine.get_layer("layer_10_business_economics")
        """
        return self.layers.get(layer_name)

    def list_layers(self):
        """
        List all available math layers.
        """
        return list(self.layers.keys())
