class PluginContext:
    def __init__(self, name: str):
        self.__name = name

    def get_plugin_dir(self):
        """
        获取插件自身用于保存数据的文件夹.

        插件不应在此处保存配置文件, 因为这样用户无法感知和设置这些配置.
        """
        pass

    def get_logger(self):
        """获取插件专属的 logger"""
        pass

    # todo
