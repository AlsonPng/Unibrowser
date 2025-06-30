import sys
import os
import json
from PyQt5.QtCore import Qt, QUrl, QPoint, QTimer, pyqtSlot
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, QLineEdit, QPushButton, QAction, QLabel, QDialog, QMenu)
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEngineProfile, QWebEngineSettings
from PyQt5.QtGui import QPalette, QColor, QKeySequence, QIcon
from PyQt5.QtWebEngineCore import QWebEngineUrlRequestInterceptor

DUCKDUCKGO_URL = "https://duckduckgo.com/?q="
BOOKMARKS_FILE = os.path.join(os.path.expanduser("~"), ".unibrowser_bookmarks.json")
CONFIG_FILE = os.path.join(os.path.expanduser("~"), ".unibrowser_config.json")

# Set user agent and enable Widevine before QApplication is created
os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = "--enable-widevine-cdm"

CHROME_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)

class BrowserTab(QWidget):
    def __init__(self, parent=None, private_profile=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        self.webview = QWebEngineView()
        # Set user agent for this tab
        if private_profile:
            self.webview.setPage(self.webview.page().__class__(private_profile, self.webview))
        profile = self.webview.page().profile()
        profile.setHttpUserAgent(CHROME_USER_AGENT)
        self.layout.addWidget(self.webview)
        self.setLayout(self.layout)
        self.webview.setUrl(QUrl("https://duckduckgo.com"))
        # Error handling: show error page if load fails
        self.webview.loadFinished.connect(self.handle_load_finished)
        # Custom context menu
        self.webview.setContextMenuPolicy(Qt.CustomContextMenu)
        self.webview.customContextMenuRequested.connect(self.show_context_menu)

    def show_context_menu(self, pos):
        menu = QMenu()
        back = menu.addAction("Back")
        forward = menu.addAction("Forward")
        reload = menu.addAction("Reload")
        menu.addSeparator()
        copy = menu.addAction("Copy")
        paste = menu.addAction("Paste")
        menu.addSeparator()
        select_all = menu.addAction("Select All")
        # Enable/disable actions
        back.setEnabled(self.webview.history().canGoBack())
        forward.setEnabled(self.webview.history().canGoForward())
        # Connect actions
        action = menu.exec_(self.webview.mapToGlobal(pos))
        if action == back:
            self.webview.back()
        elif action == forward:
            self.webview.forward()
        elif action == reload:
            self.webview.reload()
        elif action == copy:
            self.webview.triggerPageAction(QWebEnginePage.Copy)
        elif action == paste:
            self.webview.triggerPageAction(QWebEnginePage.Paste)
        elif action == select_all:
            self.webview.triggerPageAction(QWebEnginePage.SelectAll)

    def handle_load_finished(self, ok):
        if not ok:
            self.webview.setHtml("""
                <html style='background:#fff;'><body style='font-family:sans-serif;text-align:center;padding:60px;'>
                <h2>Page failed to load</h2>
                <p>Check your internet connection or the URL and try again.</p>
                </body></html>""")

class UniBrowser(QMainWindow):
    def __init__(self, private=False):
        super().__init__()
        self.private = private
        # Enable PDF viewer globally (correct attribute)
        QWebEngineProfile.defaultProfile().settings().setAttribute(QWebEngineSettings.PdfViewerEnabled, True)
        self.setWindowTitle("Unibrowser" + (" (Private)" if self.private else ""))
        self.setMinimumSize(1200, 800)
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.old_pos = None
        self.downloads = []  # Track downloads
        self.init_history()  # Ensure history is initialized before anything else
        self.bookmarks = self.load_bookmarks() if not self.private else []
        self.config = self.load_config() if not self.private else {}
        self.dark_mode = self.load_dark_mode()  # Load dark mode preference
        self.init_ui()
        if self.dark_mode:
            self.apply_dark_mode()
        self.show()

    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def save_config(self):
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(self.config, f, indent=2)
        except Exception:
            pass

    def get_homepage(self):
        return self.config.get("homepage", DUCKDUCKGO_URL)

    def set_homepage(self, url):
        self.config["homepage"] = url
        self.save_config()

    def load_dark_mode(self):
        # Persist dark mode in a config file in user home
        config_path = os.path.join(os.path.expanduser("~"), ".unibrowser_config.json")
        if os.path.exists(config_path):
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    cfg = json.load(f)
                    return cfg.get("dark_mode", False)
            except Exception:
                return False
        return False

    def save_dark_mode(self, enabled):
        config_path = os.path.join(os.path.expanduser("~"), ".unibrowser_config.json")
        try:
            cfg = {}
            if os.path.exists(config_path):
                with open(config_path, "r", encoding="utf-8") as f:
                    cfg = json.load(f)
            cfg["dark_mode"] = enabled
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(cfg, f, indent=2)
        except Exception:
            pass

    def toggle_dark_mode(self):
        self.dark_mode = not self.dark_mode
        if self.dark_mode:
            self.apply_dark_mode()
        else:
            self.apply_light_mode()
        self.save_dark_mode(self.dark_mode)
        self.show_toast("Dark mode {}".format("enabled" if self.dark_mode else "disabled"), success=True)

    def apply_dark_mode(self):
        dark_palette = QPalette()
        dark_palette.setColor(QPalette.Window, QColor(36, 37, 43))
        dark_palette.setColor(QPalette.WindowText, Qt.white)
        dark_palette.setColor(QPalette.Base, QColor(28, 29, 34))
        dark_palette.setColor(QPalette.AlternateBase, QColor(36, 37, 43))
        dark_palette.setColor(QPalette.ToolTipBase, Qt.white)
        dark_palette.setColor(QPalette.ToolTipText, Qt.white)
        dark_palette.setColor(QPalette.Text, Qt.white)
        dark_palette.setColor(QPalette.Button, QColor(44, 45, 51))
        dark_palette.setColor(QPalette.ButtonText, Qt.white)
        dark_palette.setColor(QPalette.BrightText, Qt.red)
        dark_palette.setColor(QPalette.Link, QColor(42, 130, 218))
        dark_palette.setColor(QPalette.Highlight, QColor(60, 120, 200))
        dark_palette.setColor(QPalette.HighlightedText, Qt.white)
        QApplication.instance().setPalette(dark_palette)
        # Update stylesheets for dark mode
        self.setStyleSheet('''
            QWebEngineView { border-radius: 0px; background: #23242a; }
            QMainWindow, QWidget { background: #23242a; color: #f2f2f2; }
            QLineEdit { background: #23242a; color: #f2f2f2; border: 1.5px solid #444; border-radius: 8px; selection-background-color: #4285f4; }
            QLineEdit:focus { border-color: #4285f4; }
            QPushButton { background: #23242a; color: #f2f2f2; border: 1.5px solid #444; border-radius: 6px; }
            QPushButton:hover { background: #35363c; border-color: #888; }
            QPushButton:pressed { background: #18191c; }
            QTabBar::tab { background: #23242a; color: #f2f2f2; border: 1.5px solid #444; }
            QTabBar::tab:selected { background: #35363c; color: #1a73e8; border-color: #888; }
            QTabBar::tab:hover:!selected { background: #35363c; }
            QDialog#unibrowser_bookmarks_dialog { background: #23242a; color: #f2f2f2; border: 1.5px solid #444; }
            QListWidget { background: #23242a; color: #f2f2f2; }
            QListWidget::item:selected { background: #35363c; color: #1a73e8; }
            QLabel#bookmarks_title { color: #1a73e8; }
            QDialog#unibrowser_toast QLabel { background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #23242a, stop:1 #35363c); color: #f2f2f2; border: 1.5px solid #444; }
            QMenu { background: #23242a; color: #f2f2f2; border: 1.5px solid #444; }
        ''')
        # Update find bar
        self.find_bar.setStyleSheet('background: #23242a; border: 1.5px solid #444; border-radius: 8px;')
        self.find_input.setStyleSheet('font-size:15px; padding:4px 8px; border-radius:6px; border:1px solid #444; background: #23242a; color: #f2f2f2;')
        self.find_count_label.setStyleSheet('font-size:13px; color:#aaa; padding-left:8px;')
        for btn in (self.find_prev_btn, self.find_next_btn, self.find_close_btn):
            btn.setStyleSheet('border:none; background:transparent; font-size:16px; color:#f2f2f2; border-radius:6px;')

    def apply_light_mode(self):
        QApplication.instance().setPalette(QApplication.style().standardPalette())
        self.setStyleSheet('''
            QWebEngineView { border-radius: 0px; background: white; }
        ''')
        self.find_bar.setStyleSheet('background: #f7f7fa; border: 1.5px solid #b0b0b0; border-radius: 8px;')
        self.find_input.setStyleSheet('font-size:15px; padding:4px 8px; border-radius:6px; border:1px solid #d0d0d0;')
        self.find_count_label.setStyleSheet('font-size:13px; color:#888; padding-left:8px;')
        for btn in (self.find_prev_btn, self.find_next_btn, self.find_close_btn):
            btn.setStyleSheet('border:none; background:transparent; font-size:16px; color:#444; border-radius:6px;')

    def load_bookmarks(self):
        if os.path.exists(BOOKMARKS_FILE):
            try:
                with open(BOOKMARKS_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return []
        return []

    def save_bookmarks(self):
        try:
            with open(BOOKMARKS_FILE, "w", encoding="utf-8") as f:
                json.dump(self.bookmarks, f, indent=2)
        except Exception:
            pass

    def add_bookmark(self):
        current_tab = self.tab_widget.currentWidget()
        if current_tab:
            url = current_tab.webview.url().toString()
            title = current_tab.webview.page().title() or url
            if not any(b["url"] == url for b in self.bookmarks):
                self.bookmarks.append({"title": title, "url": url})
                self.save_bookmarks()
                self.show_toast("★ Bookmarked!", success=True)
            else:
                self.show_toast("Already bookmarked.", success=False)

    def show_toast(self, message, success=True):
        # Modern, minimal, professional toast notification with reliable fade in/out
        toast = QDialog(self)
        toast.setWindowFlags(Qt.FramelessWindowHint | Qt.Tool | Qt.WindowStaysOnTopHint)
        toast.setAttribute(Qt.WA_TranslucentBackground)
        toast.setObjectName("unibrowser_toast")
        toast.setStyleSheet('''
            QDialog#unibrowser_toast { background: transparent; }
            QLabel {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 %s, stop:1 %s);
                color: %s;
                border-radius: 12px;
                padding: 14px 32px;
                font-size: 17px;
                font-weight: 500;
                border: 1.5px solid #d0d0d0;
                min-width: 180px;
                max-width: 340px;
                text-align: center;
                letter-spacing: 0.5px;
            }
        ''' % (
            "#f5f7fa" if success else "#fffbe6",
            "#e3e8ee" if success else "#ffe6b6",
            "#222" if success else "#b8860b"
        ))
        label = QLabel(message, toast)
        label.setAlignment(Qt.AlignCenter)
        layout = QVBoxLayout(toast)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(label)
        toast.setLayout(layout)
        toast.adjustSize()
        # Center above nav bar
        geo = self.geometry()
        x = geo.x() + (geo.width() - toast.width()) // 2
        y = geo.y() + 80
        toast.move(x, y)
        toast.show()
        # Fade in, then fade out after 2.5s, keep animation refs
        from PyQt5.QtCore import QPropertyAnimation
        toast.setWindowOpacity(0.0)
        fade_in = QPropertyAnimation(toast, b"windowOpacity")
        fade_in.setDuration(220)
        fade_in.setStartValue(0.0)
        fade_in.setEndValue(1.0)
        fade_in.start()
        toast._fade_in = fade_in  # keep ref
        def fade_out():
            fade_out_anim = QPropertyAnimation(toast, b"windowOpacity")
            fade_out_anim.setDuration(400)
            fade_out_anim.setStartValue(1.0)
            fade_out_anim.setEndValue(0.0)
            def close_toast():
                toast.done(0)
                toast.deleteLater()
            fade_out_anim.finished.connect(close_toast)
            fade_out_anim.start()
            toast._fade_out = fade_out_anim  # keep ref
        QTimer.singleShot(2500, fade_out)

    def show_bookmarks(self):
        from PyQt5.QtWidgets import QDialog, QVBoxLayout, QListWidget, QPushButton, QHBoxLayout, QLabel, QAbstractItemView, QInputDialog, QFileDialog, QMessageBox
        from PyQt5.QtGui import QIcon
        dlg = QDialog(self)
        dlg.setWindowTitle("Bookmarks")
        dlg.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        dlg.setObjectName("unibrowser_bookmarks_dialog")
        dlg.setStyleSheet('''
            QDialog#unibrowser_bookmarks_dialog {
                background: #fff;
                border-radius: 18px;
                border: 1.5px solid #e0e0e0;
                box-shadow: 0 8px 32px 0 rgba(60,60,80,0.16);
            }
            QListWidget {
                background: transparent;
                border: none;
                font-size: 16px;
                color: #222;
                padding: 0 0 8px 0;
            }
            QListWidget::item {
                padding: 12px 12px 12px 0px;
                border-radius: 10px;
                margin-bottom: 2px;
            }
            QListWidget::item:selected {
                background: #e3e8ee;
                color: #1a73e8;
            }
            QPushButton {
                background: #f5f7fa;
                border: 1.5px solid #d0d0d0;
                border-radius: 8px;
                padding: 7px 22px;
                font-size: 15px;
                color: #333;
                min-width: 80px;
            }
            QPushButton:hover {
                background: #ececf2;
                border-color: #b0b0b0;
            }
            QPushButton:pressed {
                background: #e0e0e0;
            }
            QLabel#bookmarks_title {
                font-size: 20px;
                font-weight: 600;
                color: #1a73e8;
                padding: 10px 0 18px 0;
                letter-spacing: 0.5px;
            }
        ''')
        layout = QVBoxLayout(dlg)
        layout.setContentsMargins(28, 18, 28, 18)
        layout.setSpacing(0)
        title = QLabel("★ Bookmarks", dlg)
        title.setObjectName("bookmarks_title")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        listw = QListWidget()
        listw.setSelectionMode(QAbstractItemView.SingleSelection)
        for b in self.bookmarks:
            listw.addItem(f'{b["title"]}  |  {b["url"]}')
        layout.addWidget(listw)
        btn_layout = QHBoxLayout()
        open_btn = QPushButton("Open")
        del_btn = QPushButton("Delete")
        edit_btn = QPushButton("Edit")
        import_btn = QPushButton("Import")
        export_btn = QPushButton("Export")
        close_btn = QPushButton("Close")
        btn_layout.addWidget(open_btn)
        btn_layout.addWidget(edit_btn)
        btn_layout.addWidget(del_btn)
        btn_layout.addWidget(import_btn)
        btn_layout.addWidget(export_btn)
        btn_layout.addWidget(close_btn)
        layout.addLayout(btn_layout)
        def open_selected():
            idx = listw.currentRow()
            if idx >= 0:
                self.load_url_from_string(self.bookmarks[idx]["url"])
                dlg.accept()
        def delete_selected():
            idx = listw.currentRow()
            if idx >= 0:
                del self.bookmarks[idx]
                self.save_bookmarks()
                listw.takeItem(idx)
        def edit_selected():
            idx = listw.currentRow()
            if idx >= 0:
                b = self.bookmarks[idx]
                new_title, ok1 = QInputDialog.getText(dlg, "Edit Title", "Title:", text=b["title"])
                if not ok1:
                    return
                new_url, ok2 = QInputDialog.getText(dlg, "Edit URL", "URL:", text=b["url"])
                if not ok2:
                    return
                self.bookmarks[idx] = {"title": new_title, "url": new_url}
                self.save_bookmarks()
                listw.item(idx).setText(f'{new_title}  |  {new_url}')
        def import_bookmarks():
            path, _ = QFileDialog.getOpenFileName(dlg, "Import Bookmarks", "", "JSON Files (*.json)")
            if path:
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        imported = json.load(f)
                        if isinstance(imported, list):
                            self.bookmarks.extend(imported)
                            self.save_bookmarks()
                            listw.clear()
                            for b in self.bookmarks:
                                listw.addItem(f'{b["title"]}  |  {b["url"]}')
                            QMessageBox.information(dlg, "Import", "Bookmarks imported.")
                except Exception as e:
                    QMessageBox.warning(dlg, "Import Failed", str(e))
        def export_bookmarks():
            path, _ = QFileDialog.getSaveFileName(dlg, "Export Bookmarks", "bookmarks.json", "JSON Files (*.json)")
            if path:
                try:
                    with open(path, "w", encoding="utf-8") as f:
                        json.dump(self.bookmarks, f, indent=2)
                    QMessageBox.information(dlg, "Export", "Bookmarks exported.")
                except Exception as e:
                    QMessageBox.warning(dlg, "Export Failed", str(e))
        open_btn.clicked.connect(open_selected)
        del_btn.clicked.connect(delete_selected)
        edit_btn.clicked.connect(edit_selected)
        import_btn.clicked.connect(import_bookmarks)
        export_btn.clicked.connect(export_bookmarks)
        close_btn.clicked.connect(dlg.accept)
        dlg.setFixedWidth(900)
        dlg.exec_()

    def load_url_from_string(self, url):
        current_tab = self.tab_widget.currentWidget()
        if current_tab:
            current_tab.webview.setUrl(QUrl(url))

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
        
        # Navigation buttons
        button_style = '''
            QPushButton { background: #fff; border: 1.5px solid #d0d0d0; border-radius: 6px; padding: 4px 14px; font-size: 15px; color: #333; min-width: 28px; }
            QPushButton:hover { background: #f0f0f0; border-color: #b0b0b0; }
            QPushButton:pressed { background: #e0e0e0; }
            QPushButton:disabled { color: #bbb; background: #f5f5f5; }
        '''
        # Home button
        self.home_btn = QPushButton("🏠")
        self.home_btn.setToolTip('Home')
        self.home_btn.clicked.connect(self.go_home)
        self.home_btn.setStyleSheet(button_style)
        nav_layout.addWidget(self.home_btn)
        
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
            QLineEdit { background: #fff; color: #222; border: 1.5px solid #d0d0d0; border-radius: 8px; padding: 4px 16px; font-size: 15px; selection-background-color: #4285f4; }
            QLineEdit:focus { border-color: #4285f4; outline: none; }
        ''')
        self.url_bar.returnPressed.connect(self.load_url)
        self.url_bar.setPlaceholderText("Search or enter address")
        nav_layout.addWidget(self.url_bar, 1)
        
        # Bookmarks button
        self.bookmark_btn = QPushButton("★")
        self.bookmark_btn.setToolTip('Add Bookmark')
        self.bookmark_btn.clicked.connect(self.add_bookmark)
        self.bookmark_btn.setStyleSheet(button_style)
        nav_layout.addWidget(self.bookmark_btn)
        
        self.show_bookmarks_btn = QPushButton("☰")
        self.show_bookmarks_btn.setToolTip('Show Bookmarks')
        self.show_bookmarks_btn.clicked.connect(self.show_bookmarks)
        self.show_bookmarks_btn.setStyleSheet(button_style)
        nav_layout.addWidget(self.show_bookmarks_btn)
        
        # Add settings button to nav bar
        self.settings_btn = QPushButton("⚙️")
        self.settings_btn.setToolTip('Settings')
        self.settings_btn.clicked.connect(self.show_settings)
        self.settings_btn.setStyleSheet(button_style)
        nav_layout.addWidget(self.settings_btn)
        
        main_layout.addWidget(nav_bar)
        
        # Add the tab widget directly after the nav bar, no extra container
        main_layout.addWidget(self.tab_widget)
        self.setCentralWidget(main_widget)

        # URL bar context menu
        self.url_bar.setContextMenuPolicy(Qt.CustomContextMenu)
        self.url_bar.customContextMenuRequested.connect(self.show_urlbar_context_menu)

        # Find-in-page bar (hidden by default)
        self.find_bar = QWidget(self)
        self.find_bar.setStyleSheet('background: #f7f7fa; border: 1.5px solid #b0b0b0; border-radius: 8px;')
        find_layout = QHBoxLayout(self.find_bar)
        find_layout.setContentsMargins(8, 4, 8, 4)
        self.find_input = QLineEdit(self.find_bar)
        self.find_input.setPlaceholderText("Find in page...")
        self.find_input.setFixedWidth(220)
        self.find_input.setStyleSheet('font-size:15px; padding:4px 8px; border-radius:6px; border:1px solid #d0d0d0;')
        find_layout.addWidget(self.find_input)
        self.find_prev_btn = QPushButton("◀", self.find_bar)
        self.find_next_btn = QPushButton("▶", self.find_bar)
        self.find_close_btn = QPushButton("✕", self.find_bar)
        for btn in (self.find_prev_btn, self.find_next_btn, self.find_close_btn):
            btn.setFixedSize(28, 28)
            btn.setStyleSheet('border:none; background:transparent; font-size:16px; color:#444; border-radius:6px;')
        find_layout.addWidget(self.find_prev_btn)
        find_layout.addWidget(self.find_next_btn)
        find_layout.addWidget(self.find_close_btn)
        self.find_count_label = QLabel("", self.find_bar)
        self.find_count_label.setStyleSheet('font-size:13px; color:#888; padding-left:8px;')
        find_layout.addWidget(self.find_count_label)
        self.find_bar.setFixedHeight(38)
        self.find_bar.setVisible(False)
        self.centralWidget().layout().insertWidget(0, self.find_bar)
        # Find-in-page logic
        self.find_input.textChanged.connect(self.find_text)
        self.find_next_btn.clicked.connect(lambda: self.find_text(forward=True))
        self.find_prev_btn.clicked.connect(lambda: self.find_text(forward=False))
        self.find_close_btn.clicked.connect(self.hide_find_bar)
        self.find_input.returnPressed.connect(lambda: self.find_text(forward=True))
        self.find_input.installEventFilter(self)

        # Global styles
        self.setStyleSheet('''
            QWebEngineView { border-radius: 0px; background: white; }
        ''')
        
        # Shortcuts
        self.add_shortcuts()
        # Add dark mode toggle shortcut
        dark_mode_action = QAction("Toggle Dark Mode", self)
        dark_mode_action.setShortcut(QKeySequence(Qt.CTRL + Qt.SHIFT + Qt.Key_D))
        dark_mode_action.triggered.connect(self.toggle_dark_mode)
        self.addAction(dark_mode_action)

        # Start with one tab
        self.add_tab()
        self.enable_tab_reordering()
        # Connect download handling for all tabs
        self.tab_widget.currentChanged.connect(self._connect_download_signals)

        # Add menu for new private window
        menu = QMenu(self)
        private_action = QAction("New Private Window", self)
        private_action.setShortcut(QKeySequence(Qt.CTRL + Qt.SHIFT + Qt.Key_N))
        private_action.triggered.connect(self.open_private_window)
        menu.addAction(private_action)
        self.menuBar = menu
        # Add to window (hidden, but shortcuts work)
        self.addAction(private_action)

    def _connect_download_signals(self, idx):
        tab = self.tab_widget.widget(idx)
        if hasattr(tab, 'webview'):
            tab.webview.page().profile().downloadRequested.connect(self.handle_download)

    def handle_download(self, download):
        url_str = download.url().toString()
        if url_str.lower().endswith('.pdf'):
            self.show_toast("PDF navigation allowed: " + url_str, success=True)
            print("[DEBUG] PDF navigation allowed:", url_str)
            return  # Do not intercept, let QWebEngineView handle
        # Save download info and show notification
        info = {
            'url': download.url().toString(),
            'path': download.path(),
            'state': 'in progress',
            'download': download
        }
        self.downloads.append(info)
        download.finished.connect(lambda: self._on_download_finished(info))
        self.show_toast(f"⬇ Download started: {os.path.basename(download.path())}", success=True)
        print("[DEBUG] Download intercepted:", url_str)

    def _on_download_finished(self, info):
        info['state'] = 'finished'
        self.show_toast(f"✔ Download finished: {os.path.basename(info['path'])}", success=True)
        # Fallback: open PDF in system viewer if it's a PDF
        if info['path'].lower().endswith('.pdf'):
            try:
                os.startfile(info['path'])
            except Exception:
                self.show_toast("Failed to open PDF in system viewer.", success=False)

    def show_downloads(self):
        from PyQt5.QtWidgets import QDialog, QVBoxLayout, QListWidget, QPushButton, QHBoxLayout, QLabel, QFileDialog, QMessageBox
        import subprocess
        dlg = QDialog(self)
        dlg.setWindowTitle("Downloads")
        dlg.setFixedWidth(700)
        layout = QVBoxLayout(dlg)
        title = QLabel("⬇ Downloads", dlg)
        title.setStyleSheet("font-size:20px;font-weight:600;color:#1a73e8;padding:10px 0 18px 0;letter-spacing:0.5px;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        listw = QListWidget()
        for d in self.downloads:
            state = "(done)" if d['state'] == 'finished' else "(in progress)"
            listw.addItem(f'{os.path.basename(d["path"])}  |  {d["url"]}  {state}')
        layout.addWidget(listw)
        btn_layout = QHBoxLayout()
        open_file_btn = QPushButton("Open File")
        open_folder_btn = QPushButton("Open Folder")
        close_btn = QPushButton("Close")
        btn_layout.addWidget(open_file_btn)
        btn_layout.addWidget(open_folder_btn)
        btn_layout.addWidget(close_btn)
        layout.addLayout(btn_layout)
        def open_file():
            idx = listw.currentRow()
            if idx >= 0 and self.downloads[idx]['state'] == 'finished':
                path = self.downloads[idx]['path']
                if os.path.exists(path):
                    os.startfile(path)
        def open_folder():
            idx = listw.currentRow()
            if idx >= 0:
                path = self.downloads[idx]['path']
                folder = os.path.dirname(path)
                if os.path.exists(folder):
                    os.startfile(folder)
        open_file_btn.clicked.connect(open_file)
        open_folder_btn.clicked.connect(open_folder)
        close_btn.clicked.connect(dlg.accept)
        dlg.exec_()

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

        reopen_tab_action = QAction("Reopen Closed Tab", self)
        reopen_tab_action.setShortcut(QKeySequence(Qt.CTRL + Qt.SHIFT + Qt.Key_T))
        reopen_tab_action.triggered.connect(self.reopen_closed_tab)
        self.addAction(reopen_tab_action)

        duplicate_tab_action = QAction("Duplicate Tab", self)
        duplicate_tab_action.setShortcut(QKeySequence(Qt.CTRL + Qt.ALT + Qt.Key_D))
        duplicate_tab_action.triggered.connect(self.duplicate_tab)
        self.addAction(duplicate_tab_action)

        show_history_action = QAction("Show History", self)
        show_history_action.setShortcut(QKeySequence(Qt.CTRL + Qt.Key_H))
        show_history_action.triggered.connect(self.show_history)
        self.addAction(show_history_action)

        show_downloads_action = QAction("Show Downloads", self)
        show_downloads_action.setShortcut(QKeySequence(Qt.CTRL + Qt.Key_J))
        show_downloads_action.triggered.connect(self.show_downloads)
        self.addAction(show_downloads_action)

        find_action = QAction("Find in Page", self)
        find_action.setShortcut(QKeySequence(Qt.CTRL + Qt.Key_F))
        find_action.triggered.connect(self.show_find_bar)
        self.addAction(find_action)

        settings_action = QAction("Settings", self)
        settings_action.setShortcut(QKeySequence(Qt.CTRL + Qt.Key_Comma))
        settings_action.triggered.connect(self.show_settings)
        self.addAction(settings_action)

        print_action = QAction("Print Page", self)
        print_action.setShortcut(QKeySequence(Qt.CTRL + Qt.Key_P))
        print_action.triggered.connect(self.print_page)
        self.addAction(print_action)

    def print_page(self):
        current_tab = self.tab_widget.currentWidget()
        if current_tab:
            try:
                current_tab.webview.page().printToPdf(self._handle_pdf_print)
            except Exception:
                # Fallback: try to open print dialog (if available)
                try:
                    current_tab.webview.page().triggerAction(QWebEnginePage.Print)
                except Exception:
                    self.show_toast("Print not supported on this page.", success=False)

    def _handle_pdf_print(self, pdf_data):
        from PyQt5.QtWidgets import QFileDialog
        if not pdf_data:
            self.show_toast("Failed to generate PDF.", success=False)
            return
        path, _ = QFileDialog.getSaveFileName(self, "Save PDF", "page.pdf", "PDF Files (*.pdf)")
        if path:
            try:
                with open(path, "wb") as f:
                    f.write(pdf_data)
                self.show_toast("PDF saved.", success=True)
            except Exception:
                self.show_toast("Failed to save PDF.", success=False)

    def show_find_bar(self):
        self.find_bar.setVisible(True)
        self.find_input.setFocus()
        self.find_input.selectAll()

    def hide_find_bar(self):
        self.find_bar.setVisible(False)
        self.find_input.clear()
        self.find_count_label.setText("")
        current_tab = self.tab_widget.currentWidget()
        if current_tab:
            current_tab.webview.findText("")

    def eventFilter(self, obj, event):
        # ESC closes find bar
        if obj == self.find_input and event.type() == event.KeyPress and event.key() == Qt.Key_Escape:
            self.hide_find_bar()
            return True
        return super().eventFilter(obj, event)

    @pyqtSlot()
    def find_text(self, forward=True):
        text = self.find_input.text()
        current_tab = self.tab_widget.currentWidget()
        if not current_tab or not text:
            self.find_count_label.setText("")
            if current_tab:
                current_tab.webview.findText("")
            return
        flags = QWebEnginePage.FindFlags()
        if not forward:
            flags |= QWebEnginePage.FindBackward
        def found_callback(found_count):
            if found_count == 0:
                self.find_count_label.setText("No matches")
            else:
                self.find_count_label.setText(f"{found_count} match{'es' if found_count != 1 else ''}")
        current_tab.webview.findText(text, flags, found_callback)

    def add_tab(self, url=None):
        tab = BrowserTab()
        idx = self.tab_widget.addTab(tab, "New Tab")
        self.tab_widget.setCurrentIndex(idx)
        tab.webview.urlChanged.connect(self.update_url_bar)
        tab.webview.loadFinished.connect(self.update_tab_title)
        self.update_navigation_buttons()
        if url:
            tab.webview.setUrl(QUrl(url))
        else:
            tab.webview.setUrl(QUrl(self.get_homepage()))
        return idx

    def close_tab(self, idx=None):
        if self.tab_widget.count() <= 1:
            return
        if idx is None:
            idx = self.tab_widget.currentIndex()
        # Save closed tab info for reopening
        tab = self.tab_widget.widget(idx)
        url = tab.webview.url().toString()
        title = tab.webview.page().title() or url
        if not hasattr(self, 'closed_tabs'):
            self.closed_tabs = []
        self.closed_tabs.append({'url': url, 'title': title})
        self.tab_widget.removeTab(idx)

    def reopen_closed_tab(self):
        if hasattr(self, 'closed_tabs') and self.closed_tabs:
            tabinfo = self.closed_tabs.pop()
            self.add_tab(tabinfo['url'])

    def duplicate_tab(self):
        current_tab = self.tab_widget.currentWidget()
        if current_tab:
            url = current_tab.webview.url().toString()
            self.add_tab(url)

    def enable_tab_reordering(self):
        self.tab_widget.setMovable(True)

    def init_history(self):
        self.history = []

    def add_history_entry(self, url, title):
        self.history.append({'url': url, 'title': title})
        if len(self.history) > 200:
            self.history.pop(0)

    def show_history(self):
        from PyQt5.QtWidgets import QDialog, QVBoxLayout, QListWidget, QPushButton, QHBoxLayout, QLabel, QAbstractItemView
        dlg = QDialog(self)
        dlg.setWindowTitle("History")
        dlg.setFixedWidth(600)
        layout = QVBoxLayout(dlg)
        title = QLabel("🕑 History", dlg)
        title.setStyleSheet("font-size:20px;font-weight:600;color:#1a73e8;padding:10px 0 18px 0;letter-spacing:0.5px;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        listw = QListWidget()
        listw.setSelectionMode(QAbstractItemView.SingleSelection)
        for h in reversed(self.history):
            listw.addItem(f'{h["title"]}  |  {h["url"]}')
        layout.addWidget(listw)
        btn_layout = QHBoxLayout()
        open_btn = QPushButton("Open")
        clear_btn = QPushButton("Clear History")
        close_btn = QPushButton("Close")
        btn_layout.addWidget(open_btn)
        btn_layout.addWidget(clear_btn)
        btn_layout.addWidget(close_btn)
        layout.addLayout(btn_layout)
        def open_selected():
            idx = listw.currentRow()
            if idx >= 0:
                self.load_url_from_string(self.history[::-1][idx]["url"])
                dlg.accept()
        def clear_history():
            self.history.clear()
            listw.clear()
        open_btn.clicked.connect(open_selected)
        clear_btn.clicked.connect(clear_history)
        close_btn.clicked.connect(dlg.accept)
        dlg.exec_()

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
        # Save closed tab info for reopening
        tab = self.tab_widget.widget(idx)
        url = tab.webview.url().toString()
        title = tab.webview.page().title() or url
        if not hasattr(self, 'closed_tabs'):
            self.closed_tabs = []
        self.closed_tabs.append({'url': url, 'title': title})
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

    def go_home(self):
        current_tab = self.tab_widget.currentWidget()
        if current_tab:
            current_tab.webview.setUrl(QUrl(self.get_homepage()))

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
            # Add to history
            url = current_tab.webview.url().toString()
            self.add_history_entry(url, title)

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

    def open_private_window(self):
        import subprocess, sys
        # Launch a new process in private mode
        subprocess.Popen([sys.executable, __file__, "--private"])

    def show_urlbar_context_menu(self, pos):
        menu = QMenu()
        copy = menu.addAction("Copy")
        paste = menu.addAction("Paste")
        cut = menu.addAction("Cut")
        select_all = menu.addAction("Select All")
        menu.addSeparator()
        clear = menu.addAction("Clear")
        action = menu.exec_(self.url_bar.mapToGlobal(pos))
        if action == copy:
            self.url_bar.copy()
        elif action == paste:
            self.url_bar.paste()
        elif action == cut:
            self.url_bar.cut()
        elif action == select_all:
            self.url_bar.selectAll()
        elif action == clear:
            self.url_bar.clear()

    def show_settings(self):
        from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLineEdit, QPushButton, QLabel, QHBoxLayout, QMessageBox
        dlg = QDialog(self)
        dlg.setWindowTitle("Settings")
        dlg.setFixedWidth(420)
        layout = QVBoxLayout(dlg)
        title = QLabel("⚙️ Settings", dlg)
        title.setStyleSheet("font-size:20px;font-weight:600;color:#1a73e8;padding:10px 0 18px 0;letter-spacing:0.5px;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        home_label = QLabel("Home page URL:")
        home_edit = QLineEdit(self.get_homepage())
        home_edit.setPlaceholderText("https://duckduckgo.com")
        home_edit.setStyleSheet('font-size:15px; padding:4px 8px; border-radius:6px; border:1px solid #d0d0d0;')
        layout.addWidget(home_label)
        layout.addWidget(home_edit)
        btn_layout = QHBoxLayout()
        save_btn = QPushButton("Save")
        close_btn = QPushButton("Close")
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(close_btn)
        layout.addLayout(btn_layout)
        def save():
            url = home_edit.text().strip()
            if url:
                self.set_homepage(url)
                QMessageBox.information(dlg, "Settings", "Homepage saved.")
                dlg.accept()
        save_btn.clicked.connect(save)
        close_btn.clicked.connect(dlg.reject)
        dlg.exec_()

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--private", action="store_true", help="Start in private/incognito mode")
    args = parser.parse_args()
    app = QApplication(sys.argv)
    browser = UniBrowser(private=args.private)
    sys.exit(app.exec_())