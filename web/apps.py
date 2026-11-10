from django.apps import AppConfig


class WebConfig(AppConfig):
    name = 'web'

    def ready(self):
        """
        把后台下拉框的空白占位项改成中文。

        Django 6.1 的 `zh_Hans` 语言包未收录 `BLANK_CHOICE_LABEL`
        （"- Select an option -"）这条文案，后台下拉框会显示英文。
        Django 官方给出的覆盖方式就是在应用的 ready() 里改写它，
        这样整个后台的所有下拉框都会生效，而不只是某一个模型。
        """
        from django.db.models import fields

        fields.BLANK_CHOICE_LABEL = '请选择'

        # SimpleUI 启动时会移除此中间件；生产环境恢复同源 iframe 保护。
        from django.conf import settings
        frame_middleware = 'django.middleware.clickjacking.XFrameOptionsMiddleware'
        if getattr(settings, 'RESTORE_FRAME_MIDDLEWARE', False) and frame_middleware not in settings.MIDDLEWARE:
            settings.MIDDLEWARE.append(frame_middleware)
