from src.plugin import register_plugin, Plugin, PluginContext, PluginConfig, TextItem, NumberItem


@register_plugin(name="simple_demo",
                 configuration=PluginConfig()
                 .add(NumberItem("a", 1, "测试用"))
                 .add(NumberItem("b", 1))
                 .add(NumberItem("c", 1, "测试用"))
                 .add(NumberItem("d", 1, "测试用"))
                 .add(NumberItem("e", 1, "测试用"))
                 .add(NumberItem("f", 1, "测试用"))
                 .add(NumberItem("g", 1, "测试用"))
                 .add(NumberItem("h", 1, "测试用"))
                 .add(NumberItem("i", 1, "测试用"))
                 .add(NumberItem("j", 1, "测试用"))
                 .add(NumberItem("k", 1, "测试用"))
                 .add(NumberItem("l", 1, "测试用"))
                 .add(NumberItem("m", 1, "测试用"))
                 )
class SimpleDemoPlugin(Plugin):
    def on_register(self, ctx: PluginContext):
        ctx.get_logger().info("simple demo known it's registered")
