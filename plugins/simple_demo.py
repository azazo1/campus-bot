from src.config import logger
from src.plugin import register_plugin, Plugin, PluginContext


@register_plugin(name="simple_demo")
class SimpleDemoPlugin(Plugin):
    def on_register(self, ctx: PluginContext):
        logger.info()
