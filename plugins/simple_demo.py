from src.plugin import register_plugin, Plugin, PluginContext, PluginConfig, TextItem


@register_plugin(name="simple_demo",
                 configuration=PluginConfig().add(TextItem("username", "admin")))
class SimpleDemoPlugin(Plugin):
    def on_register(self, ctx: PluginContext):
        ctx.get_logger().info("simple demo known it's registered")
