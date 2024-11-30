from src.config import logger
from src.plugin import register_plugin, Plugin, PluginContext, PluginConfig, TextItem


@register_plugin(name="simple_demo",
                 configuration=PluginConfig().add(TextItem("username", "admin")))
class SimpleDemoPlugin(Plugin):
    def on_register(self, ctx: PluginContext):
        logger.info("simple demo known it's registered")
