import sys
from PyQt5.QtCore import Qt, QUrl, QPoint
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, QLineEdit, QPushButton, QAction, QLabel)
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtGui import QPalette, QColor, QKeySequence, QIcon

DUCKDUCKGO_URL = "https://duckduckgo.com/?q="

class BrowserTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        self.webview = QWebEngineView()
        self.layout.addWidget(self.webview)
        self.setLayout(self.layout)
        self.webview.setUrl(QUrl("https://duckduckgo.com"))

class UniBrowser(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Unibrowser")
        self.setMinimumSize(1200, 800)
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.old_pos = None
        self.init_ui()
        self.show()

    def init_ui(self):
        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Custom title bar
        self.title_bar = QWidget()
        self.title_bar.setFixedHeight(44)
        self.title_bar.setStyleSheet('''
            QWidget { 
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #f7f7fa, stop:1 #e3e3e8);
                border-bottom: 1px solid #d0d0d0; 
            }
        ''')
        title_layout = QHBoxLayout(self.title_bar)
        title_layout.setContentsMargins(16, 0, 12, 0)
        title_layout.setSpacing(8)
        
        # Tabs in title bar
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.tabCloseRequested.connect(self.close_tab)
        self.tab_widget.currentChanged.connect(self.update_url_bar)
        self.tab_widget.setStyleSheet('''
            QTabWidget::pane { border: none; background: transparent; }
            QTabWidget::tab-bar { alignment: left; }
            QTabBar::tab {
                background: #f8f8fa;
                color: #333;
                border: 1.5px solid #d0d0d0;
                border-bottom: none;
                border-radius: 8px 8px 0px 0px;
                min-width: 110px;
                max-width: 140px;
                width: 120px;
                height: 32px;
                padding: 6px 18px 6px 18px;
                margin-right: 4px;
                font-size: 15px;
                font-weight: 500;
                transition: background 0.2s;
            }
            QTabBar::tab:selected {
                background: #fff;
                color: #1a73e8;
                border-color: #b0b0b0;
                border-bottom: 1.5px solid #fff;
            }
            QTabBar::tab:hover:!selected {
                background: #ececf2;
            }
            QTabBar::close-button {
                image: none;
                background: transparent;
                subcontrol-position: right;
                width: 14px;
                height: 14px;
                margin: 2px;
            }
            QTabBar::close-button:hover {
                background: #ff6b6b;
                border-radius: 7px;
            }
        ''')
        
        title_layout.addWidget(self.tab_widget.tabBar())
        title_layout.addStretch()
        
        # Window controls
        controls_widget = QWidget()
        controls_layout = QHBoxLayout(controls_widget)
        controls_layout.setContentsMargins(0, 0, 0, 0)
        controls_layout.setSpacing(0)
        
        min_btn = QPushButton("−")
        min_btn.setFixedSize(40, 32)
        min_btn.setStyleSheet('''
            QPushButton { background: transparent; border: none; font-size: 18px; color: #888; font-weight: bold; border-radius: 6px; }
            QPushButton:hover { background: #e5e5e5; color: #222; }
        ''')
        min_btn.clicked.connect(self.showMinimized)
        controls_layout.addWidget(min_btn)
        
        self.max_btn = QPushButton("□")
        self.max_btn.setFixedSize(40, 32)
        self.max_btn.setStyleSheet('''
            QPushButton { background: transparent; border: none; font-size: 16px; color: #888; font-weight: bold; border-radius: 6px; }
            QPushButton:hover { background: #e5e5e5; color: #222; }
        ''')
        self.max_btn.clicked.connect(self.toggle_max_restore)
        controls_layout.addWidget(self.max_btn)
        
        close_btn = QPushButton("×")
        close_btn.setFixedSize(40, 32)
        close_btn.setStyleSheet('''
            QPushButton { background: transparent; border: none; font-size: 20px; color: #e81123; font-weight: bold; border-radius: 6px; }
            QPushButton:hover { background: #e81123; color: #fff; }
        ''')
        close_btn.clicked.connect(self.close)
        controls_layout.addWidget(close_btn)
        
        title_layout.addWidget(controls_widget)
        
        # Enable window dragging
        self.title_bar.mousePressEvent = self.title_mouse_press
        self.title_bar.mouseMoveEvent = self.title_mouse_move
        main_layout.addWidget(self.title_bar)
        
        # Navigation bar
        nav_bar = QWidget()
        nav_bar.setStyleSheet('QWidget { background: #f8f8fa; border-bottom: 1px solid #e0e0e0; }')
        nav_layout = QHBoxLayout(nav_bar)
        nav_layout.setContentsMargins(16, 8, 16, 8)
        nav_layout.setSpacing(10)
        
        # Navigation buttons
        button_style = '''
            QPushButton { background: #fff; border: 1.5px solid #d0d0d0; border-radius: 6px; padding: 6px 14px; font-size: 15px; color: #333; min-width: 28px; }
            QPushButton:hover { background: #f0f0f0; border-color: #b0b0b0; }
            QPushButton:pressed { background: #e0e0e0; }
            QPushButton:disabled { color: #bbb; background: #f5f5f5; }
        '''
        
        self.back_btn = QPushButton("◀")
        self.back_btn.setToolTip('Back')
        self.back_btn.clicked.connect(self.go_back)
        self.back_btn.setStyleSheet(button_style)
        nav_layout.addWidget(self.back_btn)
        
        self.forward_btn = QPushButton("▶")
        self.forward_btn.setToolTip('Forward')
        self.forward_btn.clicked.connect(self.go_forward)
        self.forward_btn.setStyleSheet(button_style)
        nav_layout.addWidget(self.forward_btn)
        
        self.reload_btn = QPushButton("⟳")
        self.reload_btn.setToolTip('Reload')
        self.reload_btn.clicked.connect(self.reload_page)
        self.reload_btn.setStyleSheet(button_style)
        nav_layout.addWidget(self.reload_btn)
        
        # URL bar
        self.url_bar = QLineEdit()
        self.url_bar.setStyleSheet('''
            QLineEdit { background: #fff; color: #222; border: 1.5px solid #d0d0d0; border-radius: 8px; padding: 8px 16px; font-size: 15px; selection-background-color: #4285f4; }
            QLineEdit:focus { border-color: #4285f4; outline: none; }
        ''')
        self.url_bar.returnPressed.connect(self.load_url)
        self.url_bar.setPlaceholderText("Search or enter address")
        nav_layout.addWidget(self.url_bar, 1)
        main_layout.addWidget(nav_bar)
        # Add the tab widget directly after the nav bar, no extra container
        main_layout.addWidget(self.tab_widget)
        self.setCentralWidget(main_widget)

        # Global styles
        self.setStyleSheet('''
            QWebEngineView { border-radius: 0px; background: white; }
        ''')
        
        # Shortcuts
        self.add_shortcuts()
        
        # Start with one tab
        self.add_tab()

    def add_shortcuts(self):
        new_tab_action = QAction("New Tab", self)
        new_tab_action.setShortcut(QKeySequence(Qt.CTRL + Qt.Key_T))
        new_tab_action.triggered.connect(self.add_tab)
        self.addAction(new_tab_action)

        close_tab_action = QAction("Close Tab", self)
        close_tab_action.setShortcut(QKeySequence(Qt.CTRL + Qt.Key_W))
        close_tab_action.triggered.connect(self.close_current_tab)
        self.addAction(close_tab_action)

        focus_url_action = QAction("Focus URL Bar", self)
        focus_url_action.setShortcut(QKeySequence(Qt.CTRL + Qt.Key_L))
        focus_url_action.triggered.connect(self.focus_url_bar)
        self.addAction(focus_url_action)

    def add_tab(self):
        tab = BrowserTab()
        idx = self.tab_widget.addTab(tab, "New Tab")
        self.tab_widget.setCurrentIndex(idx)
        tab.webview.urlChanged.connect(self.update_url_bar)
        tab.webview.loadFinished.connect(self.update_tab_title)
        self.update_navigation_buttons()

    def close_tab(self, idx=None):
        if self.tab_widget.count() <= 1:
            return
        if idx is None:
            idx = self.tab_widget.currentIndex()
        self.tab_widget.removeTab(idx)

    def close_current_tab(self):
        self.close_tab(self.tab_widget.currentIndex())

    def go_back(self):
        current_tab = self.tab_widget.currentWidget()
        if current_tab and current_tab.webview.history().canGoBack():
            current_tab.webview.back()
        self.update_navigation_buttons()

    def go_forward(self):
        current_tab = self.tab_widget.currentWidget()
        if current_tab and current_tab.webview.history().canGoForward():
            current_tab.webview.forward()
        self.update_navigation_buttons()

    def reload_page(self):
        current_tab = self.tab_widget.currentWidget()
        if current_tab:
            current_tab.webview.reload()

    def update_navigation_buttons(self):
        current_tab = self.tab_widget.currentWidget()
        if current_tab:
            self.back_btn.setEnabled(current_tab.webview.history().canGoBack())
            self.forward_btn.setEnabled(current_tab.webview.history().canGoForward())

    def load_url(self):
        url = self.url_bar.text().strip()
        if not url:
            return
            
        # Improved URL detection
        if url.startswith("http://") or url.startswith("https://") or url.startswith("file://"):
            final_url = url
        elif url.startswith("www.") or ("." in url and " " not in url and len(url.split(".")) >= 2):
            final_url = "https://" + url
        else:
            # Search DuckDuckGo
            final_url = DUCKDUCKGO_URL + url.replace(" ", "+")
        
        current_tab = self.tab_widget.currentWidget()
        if current_tab:
            current_tab.webview.setUrl(QUrl(final_url))

    def update_url_bar(self, url=None):
        current_tab = self.tab_widget.currentWidget()
        if current_tab:
            if url is None or isinstance(url, int):
                # Handle case where url is None or an index from currentChanged signal
                url = current_tab.webview.url()
            self.url_bar.setText(url.toString())
        self.update_navigation_buttons()

    def update_tab_title(self):
        current_tab = self.tab_widget.currentWidget()
        if current_tab:
            idx = self.tab_widget.currentIndex()
            title = current_tab.webview.page().title()
            if not title or title.strip() == "":
                title = "Loading..."
            # Truncate for fixed width tabs
            if len(title) > 15:
                title = title[:12] + "..."
            self.tab_widget.setTabText(idx, title)

    def focus_url_bar(self):
        self.url_bar.setFocus()
        self.url_bar.selectAll()

    def toggle_max_restore(self):
        if self.isMaximized():
            self.showNormal()
            self.max_btn.setText("□")
        else:
            self.showMaximized()
            self.max_btn.setText("❐")

    def title_mouse_press(self, event):
        if event.button() == Qt.LeftButton:
            self.old_pos = event.globalPos()

    def title_mouse_move(self, event):
        if self.old_pos is not None and event.buttons() == Qt.LeftButton:
            delta = QPoint(event.globalPos() - self.old_pos)
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.old_pos = event.globalPos()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    browser = UniBrowser()
    sys.exit(app.exec_())