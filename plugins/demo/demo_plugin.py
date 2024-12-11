from src.plugin import (register_plugin, PluginConfig, Routine,
                        TextItem, NumberItem,
                        Plugin, PluginContext)


@register_plugin(name="demo",
                 configuration=PluginConfig()
                 .add(TextItem("family_name", "Tom"))
                 .add(TextItem("first_name", "Cherry"))
                 .add(NumberItem("age", 18)),
                 routine=Routine.SECONDLY)
class DemoPlugin(Plugin):
    def on_load(self, ctx: PluginContext):
        ctx.get_logger().info("demo plugin known it is loaded.")

    def on_unload(self, ctx: PluginContext):
        pass

    def on_register(self, ctx: PluginContext):
        ctx.get_logger().info("demo plugin known it is registered.")

    def on_config_load(self, ctx: PluginContext, cfg: PluginConfig):
        ctx.get_logger().info("demo cfg: {}".format(cfg.serialize()))

    def on_config_save(self, ctx: PluginContext, cfg: PluginConfig):
        pass

    def on_routine(self, ctx: PluginContext):
        ctx.get_logger().info("demo plugin routine.")
