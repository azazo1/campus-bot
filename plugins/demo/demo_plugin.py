from seleniumwire.webdriver import Edge

from src.plugin import (register_plugin, PluginConfig, Routine,
                        TextItem, NumberItem,
                        Plugin, PluginContext)


class MyCache:
    def __init__(self, window_name: str):
        self.window_name = window_name


def grabber(edge: Edge):
    return MyCache(edge.title)


@register_plugin(name="demo",
                 configuration=PluginConfig()
                 .add(TextItem("family_name", "Tom"))
                 .add(TextItem("first_name", "Cherry"))
                 .add(NumberItem("age", 18)),
                 routine=Routine.SECONDLY,
                 uia_cache_grabber=grabber)
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

    def on_uia_login(self, ctx: PluginContext):
        logger = ctx.get_logger()
        logger.info("demo plugin UIA login.")
        my_cache = ctx.get_uia_cache().get_cache(MyCache)  # 获取通过 grabber 得到的 cache.
        logger.info("demo plugin cache: {}".format(my_cache.window_name))
