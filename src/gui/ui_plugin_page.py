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
from PySide6.QtWidgets import (QAbstractItemView, QApplication, QHBoxLayout, QListView,
    QPushButton, QScrollArea, QSizePolicy, QVBoxLayout,
    QWidget)

class Ui_PluginPage(object):
    def setupUi(self, PluginPage):
        if not PluginPage.objectName():
            PluginPage.setObjectName(u"PluginPage")
        PluginPage.resize(400, 300)
        self.horizontalLayout = QHBoxLayout(PluginPage)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.vl = QVBoxLayout()
        self.vl.setObjectName(u"vl")
        self.pluginNameList = QListView(PluginPage)
        self.pluginNameList.setObjectName(u"pluginNameList")
        self.pluginNameList.setMaximumSize(QSize(200, 16777215))
        self.pluginNameList.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)

        self.vl.addWidget(self.pluginNameList)

        self.disposeModifiedConfigBtn = QPushButton(PluginPage)
        self.disposeModifiedConfigBtn.setObjectName(u"disposeModifiedConfigBtn")

        self.vl.addWidget(self.disposeModifiedConfigBtn)

        self.saveConfigBtn = QPushButton(PluginPage)
        self.saveConfigBtn.setObjectName(u"saveConfigBtn")

        self.vl.addWidget(self.saveConfigBtn)


        self.horizontalLayout.addLayout(self.vl)

        self.scrollArea = QScrollArea(PluginPage)
        self.scrollArea.setObjectName(u"scrollArea")
        self.scrollArea.setWidgetResizable(True)
        self.scrollWidget = QWidget()
        self.scrollWidget.setObjectName(u"scrollWidget")
        self.pluginConfigContent = QVBoxLayout(self.scrollWidget)
        self.pluginConfigContent.setObjectName(u"pluginConfigContent")
        self.scrollArea.setWidget(self.scrollWidget)

        self.horizontalLayout.addWidget(self.scrollArea)

        self.horizontalLayout.setStretch(0, 1)
        self.horizontalLayout.setStretch(1,  2)

        self.retranslateUi(PluginPage)

        QMetaObject.connectSlotsByName(PluginPage)
    # setupUi

    def retranslateUi(self, PluginPage):
        PluginPage.setWindowTitle(QCoreApplication.translate("PluginPage", u"\u63d2\u4ef6\u914d\u7f6e", None))
        self.disposeModifiedConfigBtn.setText(QCoreApplication.translate("PluginPage", u"\u4e22\u5f03\u672a\u4fdd\u5b58\u4fee\u6539", None))
        self.saveConfigBtn.setText(QCoreApplication.translate("PluginPage", u"\u4fdd\u5b58\u63d2\u4ef6\u914d\u7f6e", None))
    # retranslateUi

