#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Masaüstü Menü Ekleyici ve Yöneticisi (Desktop Entry Creator & Manager)
Linux (GNOME / Wayland) için AppImage, Binary ve Java (.jar) uygulamalarını 
sistem menüsüne (~/.local/share/applications/) ekleme ve silme GUI uygulaması.
"""

import os
import sys
import stat
import re
import subprocess
import pathlib
import argparse
import tkinter as tk
from tkinter import ttk, filedialog, messagebox


class MenuEkleyiciApp(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Menü Ekleyici - Masaüstü Kısayolu Oluşturucu ve Yöneticisi")
        self.geometry("720x800")
        self.minsize(680, 740)

        # Temayı ve Stilleri Yapılandır
        self._setup_styles()

        # Ana konteyner
        main_container = ttk.Frame(self, padding="15 15 15 15", style="Main.TFrame")
        main_container.pack(fill=tk.BOTH, expand=True)

        # Başlık Paneli
        self._build_header(main_container)

        # Sekmeli Yapı (Notebook)
        self.notebook = ttk.Notebook(main_container)
        self.notebook.pack(fill=tk.BOTH, expand=True, pady=(10, 10))

        # Sekme 1: Kısayol Oluştur
        self.tab_create = ttk.Frame(self.notebook, padding="15", style="Main.TFrame")
        self.notebook.add(self.tab_create, text=" ✨ Kısayol Oluştur ")
        self._build_create_tab(self.tab_create)

        # Sekme 2: Kısayolları Yönet / Sil
        self.tab_manage = ttk.Frame(self.notebook, padding="15", style="Main.TFrame")
        self.notebook.add(self.tab_manage, text=" 🗑️ Kısayolları Yönet / Sil ")
        self._build_manage_tab(self.tab_manage)

        # Sekme Değiştiğinde Yönet Listesini Güncelle
        self.notebook.bind("<<NotebookTabChanged>>", self._on_tab_changed)

        # Alt Bilgi ve Kendini Ekleme Butonu
        self._build_footer(main_container)

    def _setup_styles(self):
        self.style = ttk.Style(self)
        
        available_themes = self.style.theme_names()
        if "clam" in available_themes:
            self.style.theme_use("clam")

        # Renk Paleti (GNOME modern koyu/açık uyumlu pastel tonlar)
        BG_COLOR = "#f6f8fa"
        CARD_BG = "#ffffff"
        PRIMARY_COLOR = "#3584e4"   # GNOME Mavi Accent
        PRIMARY_HOVER = "#1c71d8"
        SECONDARY_COLOR = "#2ec27e" # GNOME Yeşil Accent
        SECONDARY_HOVER = "#26a269"
        DANGER_COLOR = "#e01b24"    # GNOME Kırmızı Accent
        DANGER_HOVER = "#c01c28"
        TEXT_COLOR = "#2d3748"

        self.configure(bg=BG_COLOR)

        self.style.configure("Main.TFrame", background=BG_COLOR)
        self.style.configure("Card.TFrame", background=CARD_BG, relief="solid", borderwidth=1)
        
        # Sekme Stilleri
        self.style.configure("TNotebook", background=BG_COLOR, borderwidth=0)
        self.style.configure("TNotebook.Tab", font=("Cantarell", 10, "bold"), padding=(12, 6))
        self.style.map("TNotebook.Tab", background=[("selected", CARD_BG)])

        # Etiketler
        self.style.configure("HeaderTitle.TLabel", font=("Cantarell", 16, "bold"), foreground="#1a202c", background=BG_COLOR)
        self.style.configure("HeaderSubtitle.TLabel", font=("Cantarell", 10), foreground="#718096", background=BG_COLOR)
        
        self.style.configure("FieldLabel.TLabel", font=("Cantarell", 10, "bold"), foreground=TEXT_COLOR, background=CARD_BG)
        self.style.configure("SubLabel.TLabel", font=("Cantarell", 9), foreground="#718096", background=CARD_BG)

        # Giriş kutuları ve Butonlar
        self.style.configure("TEntry", padding=6, font=("Cantarell", 10))
        self.style.configure("Browse.TButton", font=("Cantarell", 9, "bold"), padding=(10, 5))
        
        self.style.configure(
            "Primary.TButton",
            font=("Cantarell", 11, "bold"),
            foreground="#ffffff",
            background=PRIMARY_COLOR,
            padding=(12, 8)
        )
        self.style.map("Primary.TButton", background=[("active", PRIMARY_HOVER)])

        self.style.configure(
            "Danger.TButton",
            font=("Cantarell", 10, "bold"),
            foreground="#ffffff",
            background=DANGER_COLOR,
            padding=(10, 6)
        )
        self.style.map("Danger.TButton", background=[("active", DANGER_HOVER)])

        self.style.configure(
            "SelfInstall.TButton",
            font=("Cantarell", 9, "bold"),
            foreground="#ffffff",
            background=SECONDARY_COLOR,
            padding=(8, 4)
        )
        self.style.map("SelfInstall.TButton", background=[("active", SECONDARY_HOVER)])

        self.style.configure("TRadiobutton", font=("Cantarell", 10), background=CARD_BG, foreground=TEXT_COLOR)
        self.style.configure("TCheckbutton", font=("Cantarell", 10), background=CARD_BG, foreground=TEXT_COLOR)

        # Treeview (Liste) Stili
        self.style.configure("Treeview", font=("Cantarell", 9), rowheight=28)
        self.style.configure("Treeview.Heading", font=("Cantarell", 10, "bold"))

    def _build_header(self, parent):
        header_frame = ttk.Frame(parent, style="Main.TFrame")
        header_frame.pack(fill=tk.X, pady=(0, 5))

        title_lbl = ttk.Label(
            header_frame, 
            text="🚀 Menü Kısayolu Oluşturucu ve Yöneticisi", 
            style="HeaderTitle.TLabel"
        )
        title_lbl.pack(anchor=tk.W)

        subtitle_lbl = ttk.Label(
            header_frame, 
            text="AppImage, Binary ve Java (.jar) uygulamalarınızı GNOME sistem menüsüne ekleyin veya yönetin.", 
            style="HeaderSubtitle.TLabel"
        )
        subtitle_lbl.pack(anchor=tk.W, pady=(2, 0))

    # ==================== SEKME 1: OLUŞTUR ====================
    def _build_create_tab(self, parent):
        card_frame = ttk.Frame(parent, padding="18", style="Card.TFrame")
        card_frame.pack(fill=tk.BOTH, expand=True)

        # 1. Uygulama Adı
        ttk.Label(card_frame, text="Uygulama Adı *", style="FieldLabel.TLabel").pack(anchor=tk.W, pady=(0, 2))
        self.name_var = tk.StringVar()
        self.name_entry = ttk.Entry(card_frame, textvariable=self.name_var)
        self.name_entry.pack(fill=tk.X, pady=(0, 10))

        # 2. Çalıştırılabilir Dosya Seçici
        ttk.Label(card_frame, text="Çalıştırılabilir Dosya (AppImage / Binary / .jar) *", style="FieldLabel.TLabel").pack(anchor=tk.W, pady=(0, 2))
        file_frame = ttk.Frame(card_frame, style="Card.TFrame")
        file_frame.pack(fill=tk.X, pady=(0, 10))

        self.file_var = tk.StringVar()
        self.file_entry = ttk.Entry(file_frame, textvariable=self.file_var)
        self.file_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))

        btn_browse_file = ttk.Button(
            file_frame, text="Gözat...", style="Browse.TButton", command=self._browse_executable
        )
        btn_browse_file.pack(side=tk.RIGHT)

        # 3. Çalışma Dizini (Path / Working Directory)
        ttk.Label(card_frame, text="Çalışma Dizini (Path=) [Otomatik Doldurulur]", style="FieldLabel.TLabel").pack(anchor=tk.W, pady=(0, 2))
        path_frame = ttk.Frame(card_frame, style="Card.TFrame")
        path_frame.pack(fill=tk.X, pady=(0, 10))

        self.path_var = tk.StringVar()
        self.path_entry = ttk.Entry(path_frame, textvariable=self.path_var)
        self.path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))

        btn_browse_path = ttk.Button(
            path_frame, text="Gözat...", style="Browse.TButton", command=self._browse_path
        )
        btn_browse_path.pack(side=tk.RIGHT)

        # 4. İkon Seçici (Opsiyonel)
        ttk.Label(card_frame, text="İkon Dosyası (Opsiyonel - PNG/SVG)", style="FieldLabel.TLabel").pack(anchor=tk.W, pady=(0, 2))
        icon_frame = ttk.Frame(card_frame, style="Card.TFrame")
        icon_frame.pack(fill=tk.X, pady=(0, 10))

        self.icon_var = tk.StringVar()
        self.icon_entry = ttk.Entry(icon_frame, textvariable=self.icon_var)
        self.icon_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))

        btn_browse_icon = ttk.Button(
            icon_frame, text="Gözat...", style="Browse.TButton", command=self._browse_icon
        )
        btn_browse_icon.pack(side=tk.RIGHT)

        # Ayırıcı Çizgi
        ttk.Separator(card_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=8)

        # 5. Uygulama Türü Seçimi
        ttk.Label(card_frame, text="Uygulama Türü *", style="FieldLabel.TLabel").pack(anchor=tk.W, pady=(0, 4))
        self.app_type_var = tk.StringVar(value="binary")

        radio_frame = ttk.Frame(card_frame, style="Card.TFrame")
        radio_frame.pack(fill=tk.X, pady=(0, 10))

        rb_binary = ttk.Radiobutton(
            radio_frame, text="AppImage / Binary (Doğrudan Çalıştırılabilir)",
            variable=self.app_type_var, value="binary", style="TRadiobutton"
        )
        rb_binary.pack(anchor=tk.W, pady=2)

        rb_jar = ttk.Radiobutton(
            radio_frame, text="Java Uygulaması (.jar -> java -jar ile çalıştırılır)",
            variable=self.app_type_var, value="jar", style="TRadiobutton"
        )
        rb_jar.pack(anchor=tk.W, pady=2)

        # 6. Ek Seçenekler
        ttk.Label(card_frame, text="Ek Seçenekler", style="FieldLabel.TLabel").pack(anchor=tk.W, pady=(4, 4))

        options_frame = ttk.Frame(card_frame, style="Card.TFrame")
        options_frame.pack(fill=tk.X, pady=(0, 10))

        self.wayland_var = tk.BooleanVar(value=False)
        cb_wayland = ttk.Checkbutton(
            options_frame, text="Wayland / Electron Desteği Bayrağı Ekle (--ozone-platform-hint=auto)",
            variable=self.wayland_var, style="TCheckbutton"
        )
        cb_wayland.pack(anchor=tk.W, pady=2)

        self.terminal_var = tk.BooleanVar(value=False)
        cb_terminal = ttk.Checkbutton(
            options_frame, text="Terminal Penceresinde Çalıştır (Terminal=true)",
            variable=self.terminal_var, style="TCheckbutton"
        )
        cb_terminal.pack(anchor=tk.W, pady=2)

        # Kategori Seçimi
        cat_frame = ttk.Frame(card_frame, style="Card.TFrame")
        cat_frame.pack(fill=tk.X, pady=(2, 8))
        
        ttk.Label(cat_frame, text="Kategori: ", style="SubLabel.TLabel").pack(side=tk.LEFT)
        self.category_var = tk.StringVar(value="Utility")
        categories = ["Utility", "Development", "Game", "Graphics", "Network", "Office", "AudioVideo"]
        cat_combo = ttk.Combobox(
            cat_frame, textvariable=self.category_var, values=categories, state="readonly", width=20
        )
        cat_combo.pack(side=tk.LEFT, padx=5)

        # Oluştur Butonu
        btn_create = ttk.Button(
            card_frame, text="✨ Kısayol Oluştur ve Menüye Ekle", style="Primary.TButton", command=self._create_desktop_shortcut
        )
        btn_create.pack(fill=tk.X, pady=(10, 0))

    # ==================== SEKME 2: YÖNET / SİL ====================
    def _build_manage_tab(self, parent):
        card_frame = ttk.Frame(parent, padding="15", style="Card.TFrame")
        card_frame.pack(fill=tk.BOTH, expand=True)

        # Üst Araç Çubuğu (Arama ve Yenile)
        toolbar = ttk.Frame(card_frame, style="Card.TFrame")
        toolbar.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(toolbar, text="🔍 Ara: ", style="FieldLabel.TLabel").pack(side=tk.LEFT)
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *args: self._filter_shortcuts_list())
        search_entry = ttk.Entry(toolbar, textvariable=self.search_var)
        search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 10))

        btn_refresh = ttk.Button(
            toolbar, text="🔄 Yenile", style="Browse.TButton", command=self._load_shortcuts_list
        )
        btn_refresh.pack(side=tk.RIGHT)

        # Tablo (Treeview) ve Kaydırma Çubuğu (Scrollbar)
        table_frame = ttk.Frame(card_frame, style="Card.TFrame")
        table_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        columns = ("name", "exec", "file")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", selectmode="browse")

        self.tree.heading("name", text="Uygulama Adı (Name)")
        self.tree.heading("exec", text="Komut / Dosya (Exec)")
        self.tree.heading("file", text="Kısayol Dosyası")

        self.tree.column("name", width=180, anchor=tk.W)
        self.tree.column("exec", width=260, anchor=tk.W)
        self.tree.column("file", width=160, anchor=tk.W)

        scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Alt İşlem Alanı (Sil Butonu)
        action_frame = ttk.Frame(card_frame, style="Card.TFrame")
        action_frame.pack(fill=tk.X)

        self.count_label = ttk.Label(
            action_frame, text="Toplam 0 kısayol bulundu.", style="SubLabel.TLabel"
        )
        self.count_label.pack(side=tk.LEFT)

        btn_delete = ttk.Button(
            action_frame, text="🗑️ Seçili Kısayolu Sil", style="Danger.TButton", command=self._delete_selected_shortcut
        )
        btn_delete.pack(side=tk.RIGHT)

    def _build_footer(self, parent):
        footer_frame = ttk.Frame(parent, style="Main.TFrame")
        footer_frame.pack(fill=tk.X, side=tk.BOTTOM, pady=(5, 0))

        footer_label = ttk.Label(
            footer_frame,
            text="Kısayol Dizin Konumu: ~/.local/share/applications/",
            style="HeaderSubtitle.TLabel"
        )
        footer_label.pack(side=tk.LEFT)

        btn_self_install = ttk.Button(
            footer_frame,
            text="📌 Menü Ekleyici'yi Menüye Ekle",
            style="SelfInstall.TButton",
            command=self._install_self_desktop_shortcut
        )
        btn_self_install.pack(side=tk.RIGHT)

    # ==================== YARDIMCI VE OLAY METOTLARI ====================
    def _on_tab_changed(self, event):
        selected_tab = self.notebook.index(self.notebook.select())
        if selected_tab == 1:  # Yönet Sekmesi
            self._load_shortcuts_list()

    def _browse_executable(self):
        file_path = filedialog.askopenfilename(
            title="Çalıştırılabilir Dosya Seç",
            filetypes=[
                ("Tüm Desteklenen Dosyalar", "*.AppImage *.appimage *.jar *"),
                ("AppImage Dosyaları", "*.AppImage *.appimage"),
                ("Java Uygulaması", "*.jar"),
                ("Tüm Dosyalar", "*")
            ]
        )
        if file_path:
            self.file_var.set(file_path)
            
            # Otomatik Çalışma Dizini (Path) Önerisi
            parent_dir = os.path.dirname(file_path)
            self.path_var.set(parent_dir)

            # Otomatik İsim Önerisi
            if not self.name_var.get().strip():
                stem = pathlib.Path(file_path).stem
                clean_name = stem.replace("-", " ").replace("_", " ").title()
                self.name_var.set(clean_name)

            # Otomatik Tür Algılama
            if file_path.lower().endswith(".jar"):
                self.app_type_var.set("jar")
            else:
                self.app_type_var.set("binary")

    def _browse_path(self):
        selected_dir = filedialog.askdirectory(title="Çalışma Dizinini Seç (Path)")
        if selected_dir:
            self.path_var.set(selected_dir)

    def _browse_icon(self):
        icon_path = filedialog.askopenfilename(
            title="İkon Dosyası Seç",
            filetypes=[
                ("Resim Dosyaları", "*.png *.svg *.xpm *.ico *.jpg *.jpeg"),
                ("PNG Resimleri", "*.png"),
                ("SVG Vektör", "*.svg"),
                ("Tüm Dosyalar", "*")
            ]
        )
        if icon_path:
            self.icon_var.set(icon_path)

    def _sanitize_filename(self, name):
        """Uygulama adından geçerli ve güvenli bir .desktop dosya adı üretir."""
        tr_map = str.maketrans("çğıöşüÇĞİÖŞÜ", "cgiosuCGIOSU")
        name_clean = name.translate(tr_map)
        name_clean = re.sub(r'[^a-zA-Z0-9_\-]', '-', name_clean.lower())
        name_clean = re.sub(r'-+', '-', name_clean).strip('-')
        return name_clean or "custom-app"

    def _create_desktop_shortcut(self):
        app_name = self.name_var.get().strip()
        file_path = self.file_var.get().strip()
        work_dir = self.path_var.get().strip()
        icon_path = self.icon_var.get().strip()
        app_type = self.app_type_var.get()
        add_wayland_flag = self.wayland_var.get()
        run_in_terminal = self.terminal_var.get()
        category = self.category_var.get() or "Utility"

        if not app_name:
            messagebox.showerror("Eksik Bilgi", "Lütfen bir Uygulama Adı girin.")
            self.name_entry.focus()
            return

        if not file_path:
            messagebox.showerror("Eksik Bilgi", "Lütfen bir çalıştırılabilir dosya seçin.")
            return

        if not os.path.exists(file_path):
            messagebox.showerror("Hata", f"Seçilen dosya bulunamadı:\n{file_path}")
            return

        if not work_dir:
            work_dir = os.path.dirname(file_path)

        try:
            # 1. Otomatik chmod +x verme işlemi
            try:
                current_stat = os.stat(file_path)
                os.chmod(file_path, current_stat.st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
            except Exception as e:
                print(f"Chmod uyarısı: {e}")

            # 2. Exec komut satırını oluşturma
            if app_type == "jar":
                exec_cmd = f'java -jar "{file_path}"'
            else:
                exec_cmd = f'"{file_path}"'

            if add_wayland_flag:
                exec_cmd += " --ozone-platform-hint=auto"

            # 3. .desktop İçeriğini Hazırlama
            desktop_entry_lines = [
                "[Desktop Entry]",
                "Version=1.0",
                "Type=Application",
                f"Name={app_name}",
                f"Exec={exec_cmd}",
                f"Path={work_dir}",
                f"Terminal={'true' if run_in_terminal else 'false'}",
                f"Categories={category};"
            ]

            if icon_path and os.path.exists(icon_path):
                desktop_entry_lines.append(f"Icon={icon_path}")
            else:
                desktop_entry_lines.append("Icon=application-x-executable")

            desktop_content = "\n".join(desktop_entry_lines) + "\n"

            # 4. ~/.local/share/applications/ dizinine yaz
            apps_dir = os.path.expanduser("~/.local/share/applications")
            os.makedirs(apps_dir, exist_ok=True)

            filename = f"{self._sanitize_filename(app_name)}.desktop"
            target_path = os.path.join(apps_dir, filename)

            with open(target_path, "w", encoding="utf-8") as f:
                f.write(desktop_content)

            os.chmod(target_path, 0o755)

            # 5. Arka planda veritabanını güncelle
            self._trigger_db_update(apps_dir)

            messagebox.showinfo(
                "Başarılı",
                f"Kısayol başarıyla oluşturuldu! 🎉\n\nUygulama: {app_name}\nKonum:\n{target_path}"
            )

        except Exception as err:
            messagebox.showerror("İşlem Başarısız", f"Kısayol oluşturulurken hata oluştu:\n\n{str(err)}")

    # ==================== KISAYOL LİSTELEME VE SİLME MANTIĞI ====================
    def _parse_desktop_file(self, file_path):
        """Bir .desktop dosyasından Name ve Exec değerlerini okur."""
        name = os.path.basename(file_path)
        exec_cmd = "-"
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("Name=") and name == os.path.basename(file_path):
                        name = line.split("=", 1)[1].strip()
                    elif line.startswith("Exec="):
                        exec_cmd = line.split("=", 1)[1].strip()
        except Exception:
            pass
        return name, exec_cmd

    def _load_shortcuts_list(self):
        """~/.local/share/applications/ dizinindeki .desktop dosyalarını listeye yükler."""
        for item in self.tree.get_children():
            self.tree.delete(item)

        apps_dir = os.path.expanduser("~/.local/share/applications")
        if not os.path.exists(apps_dir):
            self.count_label.config(text="Toplam 0 kısayol bulundu.")
            return

        self.all_shortcuts = []
        try:
            files = [f for f in os.listdir(apps_dir) if f.endswith(".desktop")]
            files.sort(key=str.lower)

            for filename in files:
                full_path = os.path.join(apps_dir, filename)
                app_name, exec_cmd = self._parse_desktop_file(full_path)
                self.all_shortcuts.append((app_name, exec_cmd, filename, full_path))

            self._filter_shortcuts_list()

        except Exception as e:
            messagebox.showerror("Hata", f"Kısayollar listelenirken bir hata oluştu:\n{e}")

    def _filter_shortcuts_list(self):
        """Arama kutusundaki metne göre tabloyu filtreler."""
        query = self.search_var.get().strip().lower()

        for item in self.tree.get_children():
            self.tree.delete(item)

        count = 0
        for app_name, exec_cmd, filename, full_path in getattr(self, "all_shortcuts", []):
            if not query or (query in app_name.lower() or query in exec_cmd.lower() or query in filename.lower()):
                self.tree.insert("", tk.END, values=(app_name, exec_cmd, filename), tags=(full_path,))
                count += 1

        self.count_label.config(text=f"Toplam {count} kısayol bulundu.")

    def _delete_selected_shortcut(self):
        """Seçilen .desktop dosyasını kullanıcı onayından sonra sistemden siler."""
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showwarning("Seçim Yapılmadı", "Lütfen silmek istediğiniz kısayolu listeden seçin.")
            return

        item_values = self.tree.item(selected_item[0], "values")
        app_name = item_values[0]
        filename = item_values[2]

        apps_dir = os.path.expanduser("~/.local/share/applications")
        target_path = os.path.join(apps_dir, filename)

        # Kullanıcı Onayı
        confirm = messagebox.askyesno(
            "Kısayol Silme Onayı",
            f"Aşağıdaki kısayol sistem menünüzden kalıcı olarak silinecek:\n\n"
            f"• Uygulama Adı: {app_name}\n"
            f"• Dosya: {filename}\n\n"
            f"Devam etmek istiyor musunuz?",
            icon="warning"
        )

        if not confirm:
            return

        try:
            if os.path.exists(target_path):
                os.remove(target_path)

            # Veritabanını Yenile
            self._trigger_db_update(apps_dir)

            messagebox.showinfo(
                "Silindi",
                f"'{app_name}' kısayolu başarıyla silindi ve sistem menünüz güncellendi. 🗑️"
            )

            # Listeyi Güncelle
            self._load_shortcuts_list()

        except Exception as e:
            messagebox.showerror("Silme Hatası", f"Kısayol silinirken bir hata oluştu:\n\n{e}")

    def _trigger_db_update(self, apps_dir):
        """update-desktop-database komutunu tetikler."""
        try:
            subprocess.run(
                ["update-desktop-database", apps_dir],
                check=False,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
        except Exception:
            pass

    def _install_self_desktop_shortcut(self):
        """Uygulamanın kendi .desktop dosyasını oluşturur."""
        try:
            create_self_desktop_file()
            messagebox.showinfo(
                "Başarılı",
                "Menü Ekleyici uygulaması sistem menünüze (~/.local/share/applications/menu-ekleyici.desktop) eklendi! 🎉"
            )
        except Exception as e:
            messagebox.showerror("Hata", f"Menü kısayolu oluşturulamadı:\n{e}")


def create_self_desktop_file():
    """Menü Ekleyici uygulamasının kendi .desktop dosyasını oluşturur."""
    script_path = os.path.abspath(__file__)
    script_dir = os.path.dirname(script_path)
    try:
        current_stat = os.stat(script_path)
        os.chmod(script_path, current_stat.st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    except Exception:
        pass

    python_executable = sys.executable or "python3"
    exec_command = f'{python_executable} "{script_path}"'
    
    apps_dir = os.path.expanduser("~/.local/share/applications")
    os.makedirs(apps_dir, exist_ok=True)
    
    target_path = os.path.join(apps_dir, "menu-ekleyici.desktop")

    desktop_content = (
        "[Desktop Entry]\n"
        "Version=1.0\n"
        "Type=Application\n"
        "Name=Menü Ekleyici\n"
        "Comment=AppImage, Binary ve Jar dosyalarını GNOME menüsüne ekleyin ve yönetin\n"
        f"Exec={exec_command}\n"
        f"Path={script_dir}\n"
        "Icon=preferences-desktop-peripherals\n"
        "Terminal=false\n"
        "Categories=Utility;Development;\n"
    )

    with open(target_path, "w", encoding="utf-8") as f:
        f.write(desktop_content)

    os.chmod(target_path, 0o755)

    try:
        subprocess.run(
            ["update-desktop-database", apps_dir],
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
    except Exception:
        pass


def main():
    parser = argparse.ArgumentParser(description="Menü Ekleyici - Linux Masaüstü Kısayolu Oluşturucu ve Yöneticisi")
    parser.add_argument("--install", action="store_true", help="Menü Ekleyici'nin kendisi için .desktop kısayolu oluşturur")
    args = parser.parse_args()

    if args.install:
        create_self_desktop_file()
        print("✓ Menü Ekleyici kısayolu ~/.local/share/applications/menu-ekleyici.desktop adresine başarıyla yazıldı.")
        sys.exit(0)

    app = MenuEkleyiciApp()
    app.mainloop()


if __name__ == "__main__":
    main()
