# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'plugin_page.ui'
##
## Created by: Qt User Interface Compiler version 6.8.1
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QApplication, QHBoxLayout, QListView, QSizePolicy,
    QVBoxLayout, QWidget)

class Ui_PluginPage(object):
    def setupUi(self, PluginPage):
        if not PluginPage.objectName():
            PluginPage.setObjectName(u"PluginPage")
        PluginPage.resize(400, 300)
        self.horizontalLayout = QHBoxLayout(PluginPage)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.pluginNameList = QListView(PluginPage)
        self.pluginNameList.setObjectName(u"pluginNameList")

        self.horizontalLayout.addWidget(self.pluginNameList)

        self.pluginConfigContent = QVBoxLayout()
        self.pluginConfigContent.setObjectName(u"pluginConfigContent")

        self.horizontalLayout.addLayout(self.pluginConfigContent)


        self.retranslateUi(PluginPage)

        QMetaObject.connectSlotsByName(PluginPage)
    # setupUi

    def retranslateUi(self, PluginPage):
        PluginPage.setWindowTitle(QCoreApplication.translate("PluginPage", u"\u63d2\u4ef6\u914d\u7f6e", None))
    # retranslateUi

