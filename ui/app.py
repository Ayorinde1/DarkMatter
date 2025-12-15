import customtkinter as ctk
import threading
import time
import os
import asyncio
import requests
from tkinter import filedialog
from core.models import TrafficConfig, ProxyConfig, TrafficStats, ProxyCheckResult
from core.engine import AsyncTrafficEngine
from core.proxy_manager import ThreadedProxyManager
from .utils import Utils
from .components import VirtualGrid
from .styles import COLORS

class ModernTrafficBot(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.settings = Utils.load_settings()
        self.title("DARKMATTER-TB")
        self.geometry("1100x750")
        self.iconbitmap(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "resources", "favicon.ico"))

        self.testing = False
        self.testing_paused = False
        self.running = False
        self.proxies = []
        self.active_proxy_count = 0
        self.buffer = []
        self.stats = {"req": 0, "success": 0, "fail": 0}
        self.engine: AsyncTrafficEngine = None
        self.engine_thread: threading.Thread = None

        try:
            self.real_ip = requests.get("https://api.ipify.org", timeout=2).text
        except:
            self.real_ip = "0.0.0.0"

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.setup_sidebar()
        self.setup_pages()
        self.select_page("run")
        self.update_gui_loop()

    def setup_sidebar(self):
        self.sidebar = ctk.CTkFrame(self, width=200, corner_radius=0, fg_color=COLORS["nav"])
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_rowconfigure(4, weight=1)

        ctk.CTkLabel(self.sidebar, text="DARKMATTER", font=("Roboto", 20, "bold"), text_color=COLORS["accent"]).grid(
            row=0, column=0, padx=20, pady=(20, 10))

        self.nav_btns = {}
        for i, (key, text) in enumerate(
                [("run", "🚀 Dashboard"), ("proxy", "🛡️ Proxy Manager"), ("settings", "⚙️ Settings")]):
            btn = ctk.CTkButton(self.sidebar, text=text, fg_color="transparent", text_color=COLORS["text_dim"],
                                anchor="w", hover_color=COLORS["card"], height=40,
                                command=lambda k=key: self.select_page(k))
            btn.grid(row=i + 1, column=0, sticky="ew", padx=10, pady=5)
            self.nav_btns[key] = btn

        ctk.CTkLabel(self.sidebar, text="v3.1.2 Stats", text_color=COLORS["text_dim"], font=("Roboto", 10)).grid(row=5,
                                                                                                                 column=0,
                                                                                                                 pady=20)

    def setup_pages(self):
        self.pages = {}
        self.pages["run"] = ctk.CTkFrame(self, fg_color="transparent")
        self.setup_run_ui(self.pages["run"])
        self.pages["proxy"] = ctk.CTkFrame(self, fg_color="transparent")
        self.setup_proxy_ui(self.pages["proxy"])
        self.pages["settings"] = ctk.CTkFrame(self, fg_color="transparent")
        self.setup_settings_ui(self.pages["settings"])

    def select_page(self, key):
        for k, p in self.pages.items(): p.grid_forget()
        for k, b in self.nav_btns.items(): b.configure(fg_color="transparent", text_color=COLORS["text_dim"])
        self.pages[key].grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        self.nav_btns[key].configure(fg_color=COLORS["card"], text_color=COLORS["text"])

    def setup_run_ui(self, parent):
        stats_frame = ctk.CTkFrame(parent, fg_color="transparent")
        stats_frame.pack(fill="x", pady=(0, 20))

        self.lbl_stats = {}
        for key, title in [("req", "Total Requests"), ("success", "Successful Visits"), ("fail", "Failed / Timeout"), ("proxies", "Proxies Loaded")]:
            card = ctk.CTkFrame(stats_frame, fg_color=COLORS["card"])
            card.pack(side="left", fill="x", expand=True, padx=5)
            ctk.CTkLabel(card, text=title, font=("Roboto", 12), text_color=COLORS["text_dim"]).pack(pady=(15, 0))
            l = ctk.CTkLabel(card, text="0", font=("Roboto", 28, "bold"), text_color=COLORS["accent"])
            l.pack(pady=(0, 15))
            self.lbl_stats[key] = l

        cfg_frame = ctk.CTkFrame(parent, fg_color=COLORS["card"])
        cfg_frame.pack(fill="x", pady=10)

        ctk.CTkLabel(cfg_frame, text="Attack Configuration", font=("Roboto", 14, "bold")).pack(anchor="w", padx=20,
                                                                                               pady=15)

        self.entry_url = ctk.CTkEntry(cfg_frame, placeholder_text="https://target.com", height=35)
        self.entry_url.pack(fill="x", padx=20, pady=(0, 15))
        self.entry_url.insert(0, self.settings["target_url"])

        slider_row = ctk.CTkFrame(cfg_frame, fg_color="transparent")
        slider_row.pack(fill="x", padx=10, pady=10)

        t_frame = ctk.CTkFrame(slider_row, fg_color="transparent")
        t_frame.pack(side="left", fill="x", expand=True)

        self.lbl_threads = ctk.CTkLabel(t_frame, text=f"Concurrent Threads: {self.settings.get('threads', 5)}")
        self.lbl_threads.pack(anchor="w")

        self.slider_threads = ctk.CTkSlider(t_frame, from_=1, to=100, number_of_steps=99,
                                            command=self.update_thread_lbl, button_color=COLORS["accent"], button_hover_color=COLORS["accent_hover"])
        self.slider_threads.set(self.settings.get("threads", 5))
        self.slider_threads.pack(fill="x", pady=5)

        v_frame = ctk.CTkFrame(slider_row, fg_color="transparent")
        v_frame.pack(side="left", fill="x", expand=True, padx=20)

        self.lbl_viewtime = ctk.CTkLabel(v_frame,
                                         text=f"Duration: {self.settings.get('viewtime_min', 5)}s - {self.settings.get('viewtime_max', 10)}s")
        self.lbl_viewtime.pack(anchor="w")

        ctk.CTkLabel(v_frame, text="Min:", font=("Roboto", 10)).pack(anchor="w")
        self.slider_view_min = ctk.CTkSlider(v_frame, from_=1, to=60, number_of_steps=59, command=self.update_view_lbl, button_color=COLORS["accent"], button_hover_color=COLORS["accent_hover"])
        self.slider_view_min.set(self.settings.get("viewtime_min", 5))
        self.slider_view_min.pack(fill="x", pady=2)

        ctk.CTkLabel(v_frame, text="Max:", font=("Roboto", 10)).pack(anchor="w")
        self.slider_view_max = ctk.CTkSlider(v_frame, from_=1, to=60, number_of_steps=59, command=self.update_view_lbl, button_color=COLORS["accent"], button_hover_color=COLORS["accent_hover"])
        self.slider_view_max.set(self.settings.get("viewtime_max", 10))
        self.slider_view_max.pack(fill="x", pady=2)

        # Button Row
        btn_row = ctk.CTkFrame(cfg_frame, fg_color="transparent")
        btn_row.pack(fill="x", padx=20, pady=20)

        self.btn_attack = ctk.CTkButton(btn_row, text="START CAMPAIGN", height=45, fg_color=COLORS["success"],
                                        font=("Roboto", 14, "bold"), command=self.toggle_attack)
        self.btn_attack.pack(side="left", fill="x", expand=True, padx=(0, 10))

        # NEW RESET BUTTON
        self.btn_reset = ctk.CTkButton(btn_row, text="RESET STATS", height=45, fg_color=COLORS["warning"],
                                       font=("Roboto", 12, "bold"), width=120, command=self.reset_stats)
        self.btn_reset.pack(side="right")

        ctk.CTkLabel(parent, text="Activity Log", text_color=COLORS["text_dim"]).pack(anchor="w", pady=(10, 5))
        self.log_box = ctk.CTkTextbox(parent, fg_color=COLORS["card"])
        self.log_box.pack(fill="both", expand=True)

    def update_thread_lbl(self, value):
        self.lbl_threads.configure(text=f"Concurrent Threads: {int(value)}")

    def update_view_lbl(self, value):
        mn = int(self.slider_view_min.get())
        mx = int(self.slider_view_max.get())
        self.lbl_viewtime.configure(text=f"Duration: {mn}s - {mx}s")

    def setup_proxy_ui(self, parent):
        tools = ctk.CTkFrame(parent, fg_color=COLORS["card"])
        tools.pack(fill="x", pady=(0, 10))

        # Row 1: Actions & Protocol Checkboxes
        r1 = ctk.CTkFrame(tools, fg_color="transparent")
        r1.pack(fill="x", padx=10, pady=10)

        ctk.CTkButton(r1, text="Scrape New", width=100, command=self.run_scraper, fg_color=COLORS["accent"], hover_color=COLORS["accent_hover"]).pack(side="left", padx=5)
        ctk.CTkButton(r1, text="Load File", width=100, fg_color=COLORS["accent"], hover_color=COLORS["accent_hover"], command=self.load_proxy_file).pack(
            side="left", padx=5)
        ctk.CTkButton(r1, text="Export Active", width=100, fg_color="#F39C12", command=self.export_active).pack(
            side="right", padx=5)

        proto_frm = ctk.CTkFrame(tools, fg_color="transparent")
        proto_frm.pack(fill="x", padx=10, pady=5)

        self.chk_http = ctk.CTkCheckBox(proto_frm, text="HTTP/S", width=70, fg_color=COLORS["accent"], hover_color=COLORS["accent_hover"])
        if self.settings.get("use_http", True): self.chk_http.select()
        self.chk_http.pack(side="left", padx=10)

        self.chk_socks4 = ctk.CTkCheckBox(proto_frm, text="SOCKS4", width=70, fg_color=COLORS["accent"], hover_color=COLORS["accent_hover"])
        if self.settings.get("use_socks4", True): self.chk_socks4.select()
        self.chk_socks4.pack(side="left", padx=10)

        self.chk_socks5 = ctk.CTkCheckBox(proto_frm, text="SOCKS5", width=70, fg_color=COLORS["accent"], hover_color=COLORS["accent_hover"])
        if self.settings.get("use_socks5", True): self.chk_socks5.select()
        self.chk_socks5.pack(side="left", padx=10)

        self.chk_hide_dead = ctk.CTkCheckBox(proto_frm, text="Hide Dead", width=70, fg_color=COLORS["danger"])
        if self.settings.get("hide_dead", True): self.chk_hide_dead.select()
        self.chk_hide_dead.pack(side="right", padx=10)

        r_counts = ctk.CTkFrame(tools, fg_color="transparent")
        r_counts.pack(fill="x", padx=10, pady=5)

        self.lbl_loaded = ctk.CTkLabel(r_counts, text="Total: 0", font=("Roboto", 12, "bold"))
        self.lbl_loaded.pack(side="left", padx=5)

        self.lbl_proto_counts = ctk.CTkLabel(r_counts, text="HTTP: 0 | HTTPS: 0 | SOCKS4: 0 | SOCKS5: 0",
                                             text_color=COLORS["text_dim"], font=("Roboto", 11))
        self.lbl_proto_counts.pack(side="right", padx=15)

        self.lbl_bandwidth = ctk.CTkLabel(r_counts, text="Network Traffic: 0.00 Mbps", text_color=COLORS["accent"], font=("Roboto", 11, "bold"))
        self.lbl_bandwidth.pack(side="right", padx=5)

        r2 = ctk.CTkFrame(tools, fg_color=COLORS["bg"])
        r2.pack(fill="x", padx=10, pady=(0, 10))

        self.entry_test_url = ctk.CTkEntry(r2, width=200, placeholder_text="Test Gateway")
        self.entry_test_url.insert(0, self.settings["proxy_test_url"])
        self.entry_test_url.pack(side="left", padx=5, pady=5)

        ctk.CTkLabel(r2, text="Timeout (ms):").pack(side="left", padx=2)
        self.entry_timeout = ctk.CTkEntry(r2, width=70) # Expanded width
        self.entry_timeout.insert(0, str(self.settings["proxy_timeout"]))
        self.entry_timeout.pack(side="left", padx=2)

        ctk.CTkLabel(r2, text="Check Threads:").pack(side="left", padx=(10, 2))
        self.entry_check_threads = ctk.CTkEntry(r2, width=70) # Expanded width
        self.entry_check_threads.insert(0, str(self.settings["proxy_check_threads"]))
        self.entry_check_threads.pack(side="left", padx=2)

        ctk.CTkLabel(r2, text="Scrape Threads:").pack(side="left", padx=(10, 2))
        self.entry_scrape_threads = ctk.CTkEntry(r2, width=40)
        self.entry_scrape_threads.insert(0, str(self.settings["proxy_scrape_threads"]))
        self.entry_scrape_threads.pack(side="left", padx=2)

        r3 = ctk.CTkFrame(tools, fg_color=COLORS["bg"])
        r3.pack(fill="x", padx=10, pady=(0, 5))
        ctk.CTkLabel(r3, text="Scraper Proxy:").pack(side="left", padx=5)
        
        self.combo_scraper_proto = ctk.CTkComboBox(r3, values=["http", "socks4", "socks5"], width=90)
        self.combo_scraper_proto.set(self.settings.get("scraper_proxy_protocol", "http"))
        self.combo_scraper_proto.pack(side="left", padx=5)

        self.entry_scraper_proxy = ctk.CTkEntry(r3, placeholder_text="user:pass@ip:port", width=250)
        self.entry_scraper_proxy.insert(0, self.settings.get("scraper_proxy", ""))
        self.entry_scraper_proxy.pack(side="left", padx=5)

        self.chk_use_scraper_proxy = ctk.CTkCheckBox(r3, text="Use Proxy", width=60, fg_color=COLORS["accent"], hover_color=COLORS["accent_hover"])
        if self.settings.get("use_scraper_proxy", False): self.chk_use_scraper_proxy.select()
        self.chk_use_scraper_proxy.pack(side="left", padx=5)

        self.btn_test_proxy = ctk.CTkButton(r3, text="TEST", width=60, fg_color=COLORS["accent"], hover_color=COLORS["accent_hover"], command=self.test_scraper_proxy)
        self.btn_test_proxy.pack(side="left", padx=5)

        self.btn_test = ctk.CTkButton(r2, text="TEST ALL", width=100, fg_color=COLORS["success"],
                                      command=self.toggle_test)
        self.btn_test.pack(side="right", padx=5, pady=5)
        
        self.btn_pause = ctk.CTkButton(r2, text="PAUSE", width=80, fg_color=COLORS["warning"],
                                       command=self.toggle_pause_test, state="disabled")
        self.btn_pause.pack(side="right", padx=5, pady=5)

        self.progress_bar = ctk.CTkProgressBar(parent, height=10)
        self.progress_bar.set(0)
        self.progress_bar.pack(fill="x", pady=(0, 5))
        self.progress_bar.pack_forget()

        self.proxy_grid = VirtualGrid(parent, columns=["Address", "Proto", "Country", "Status", "Ping", "Anon"])
        self.proxy_grid.pack(fill="both", expand=True)

    def setup_settings_ui(self, parent):
        card = ctk.CTkFrame(parent, fg_color=COLORS["card"])
        card.pack(fill="x")
        self.chk_headless = ctk.CTkCheckBox(card, text="Headless Browser Mode (Invisible)", fg_color=COLORS["accent"], hover_color=COLORS["accent_hover"])
        if self.settings.get("headless", True): self.chk_headless.select()
        self.chk_headless.pack(anchor="w", padx=20, pady=20)
        ctk.CTkButton(card, text="Save Configuration", fg_color=COLORS["accent"], hover_color=COLORS["accent_hover"], command=self.save_cfg).pack(anchor="w", padx=20, pady=(0, 20))

    def log(self, msg):
        self.log_box.configure(state="normal")
        self.log_box.insert("end", f"[{time.strftime('%H:%M:%S')}] {msg}\n")
        self.log_box.see("end")
        self.log_box.configure(state="disabled")

    def load_proxy_file(self):
        f = filedialog.askopenfilename()
        if f:
            try:
                self.proxies = []
                self.buffer = []
                self.proxy_grid.clear()

                with open(f, 'r') as file:
                    for l in file:
                        l = l.strip()
                        if not l: continue
                        # Normalize: Add http:// if no protocol specified (standardizes for dedup)
                        if "://" not in l:
                            l = "http://" + l
                        self.proxies.append(l)
                
                self.proxies = list(set(self.proxies)) # Deduplicate immediately

                self.update_proxy_stats()
                self.log(f"Cleared previous data. Loaded {len(self.proxies)} unique proxies.")
            except:
                pass

    def export_active(self):
        active_objs = self.proxy_grid.get_active_objects()

        if not active_objs:
            return self.log("No active proxies to export.")

        if not os.path.exists("resources/proxies"):
            os.makedirs("resources/proxies")

        socks_list = []
        http_list = []

        for p in active_objs:
            p_str = f"{p['type'].lower()}://{p['ip']}:{p['port']}"
            if "SOCKS" in p['type']:
                socks_list.append(p_str)
            else:
                http_list.append(p_str)

        try:
            if socks_list:
                with open("resources/proxies/socks.txt", "w") as f: f.write("\n".join(socks_list))
            if http_list:
                with open("resources/proxies/http.txt", "w") as f: f.write("\n".join(http_list))

            self.log(f"Auto-Exported: {len(socks_list)} SOCKS, {len(http_list)} HTTP.")
        except Exception as e:
            self.log(f"Export Error: {e}")

    def run_scraper(self):
        try:
            th = int(self.entry_scrape_threads.get())
        except:
            th = 20
            
        scraper_proxy = self.entry_scraper_proxy.get().strip()
        proto = self.combo_scraper_proto.get()
        use_proxy = self.chk_use_scraper_proxy.get()
        
        if use_proxy and scraper_proxy:
            # If no scheme is provided, prepend the selected protocol
            if "://" not in scraper_proxy:
                scraper_proxy = f"{proto}://{scraper_proxy}"
        else:
            scraper_proxy = None

        protos = []
        if self.chk_http.get(): protos.append("http")
        if self.chk_socks4.get(): protos.append("socks4")
        if self.chk_socks5.get(): protos.append("socks5")
        
        sources_file = self.settings["sources"]
        # Ensure sources file exists with defaults
        if not os.path.exists(sources_file):
            with open(sources_file, "w") as f:
                f.write("https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/socks5.txt\n")
                f.write("https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/http.txt\n")
                f.write(f"https://api.proxyscrape.com/v2/?request=getproxies&protocol=http,socks4,socks5&timeout=10000&country=all\n")

        def _job():
            self.log_safe(f"Scraping started (Async) using proxy: {scraper_proxy if scraper_proxy else 'Direct'}...")
            try:
                with open(sources_file, "r") as f:
                    urls = [line.strip() for line in f if line.strip() and not line.startswith("#")]
                
                manager = ThreadedProxyManager()
                
                # Bandwidth tracking
                total_bytes = 0
                last_time = time.time()
                
                def on_scrape_progress(bytes_count):
                    nonlocal total_bytes, last_time
                    total_bytes += bytes_count
                    
                    now = time.time()
                    delta = now - last_time
                    if delta >= 1.0:
                        # Mbps = (bytes * 8) / 1024 / 1024 / delta
                        # We calculate usage over the LAST delta interval for "current speed"? 
                        # Or cumulative average? "Current speed" is better.
                        # But here total_bytes is cumulative. 
                        # I need diff.
                        pass # Logic inside ThreadedProxyManager returns bytes per call? Yes.
                
                # Improved bandwidth tracking with closure state
                scrape_bytes_buffer = 0
                
                def on_progress_wrapper(b):
                    nonlocal scrape_bytes_buffer, last_time
                    scrape_bytes_buffer += b
                    now = time.time()
                    if now - last_time >= 1.0:
                        mbps = (scrape_bytes_buffer * 8) / 1024 / 1024 / (now - last_time)
                        self.after(0, lambda m=mbps: self.lbl_bandwidth.configure(text=f"Scrape BW: {m:.2f} Mbps"))
                        last_time = now
                        scrape_bytes_buffer = 0

                # Run threaded scraper
                results = manager.scrape(urls, protos, max_threads=th, scraper_proxy=scraper_proxy, on_progress=on_progress_wrapper)
                
                # Convert back to string format for the UI list for now (or update UI to hold objects)
                # The UI currently expects simple strings in self.proxies
                found_strings = [p.to_curl_cffi_format() for p in results]
                
                self.proxies.extend(found_strings)
                self.proxies = list(set(self.proxies))

                self.after(0, self.update_proxy_stats)
                self.log_safe(f"Scrape complete. Found {len(results)} proxies.")
            except Exception as e:
                self.log_safe(f"Scrape Error: {e}")

        threading.Thread(target=_job, daemon=True).start()

    def update_proxy_stats(self):
        total = len(self.proxies)
        self.lbl_loaded.configure(text=f"Total: {total}")
        counts = self.proxy_grid.get_counts()
        self.lbl_proto_counts.configure(
            text=f"HTTP: {counts['HTTP']} | HTTPS: {counts['HTTPS']} | SOCKS4: {counts['SOCKS4']} | SOCKS5: {counts['SOCKS5']}")

    def test_scraper_proxy(self):
        scraper_proxy = self.entry_scraper_proxy.get().strip()
        proto = self.combo_scraper_proto.get()
        if not scraper_proxy:
            return self.log("Enter a proxy first.")
            
        if "://" not in scraper_proxy:
            scraper_proxy = f"{proto}://{scraper_proxy}"
            
        self.btn_test_proxy.configure(text="...", state="disabled", fg_color=COLORS["warning"])
            
        def _test():
            self.log(f"Testing proxy: {scraper_proxy}...")
            try:
                proxies = {"http": scraper_proxy, "https": scraper_proxy}
                r = requests.get("https://api.ipify.org?format=json", proxies=proxies, timeout=10)
                if r.status_code == 200:
                    self.log(f"Proxy Success! IP: {r.json().get('ip')}")
                    self.after(0, lambda: self.btn_test_proxy.configure(text="OK", fg_color=COLORS["success"]))
                else:
                    self.log(f"Proxy Failed: HTTP {r.status_code}")
                    self.after(0, lambda: self.btn_test_proxy.configure(text="FAIL", fg_color=COLORS["danger"]))
            except Exception as e:
                self.log(f"Proxy Error: {e}")
                self.after(0, lambda: self.btn_test_proxy.configure(text="ERR", fg_color=COLORS["danger"]))
            
            # Reset button after 2 seconds
            def reset():
                self.btn_test_proxy.configure(text="TEST", state="normal", fg_color=COLORS["accent"])
            self.after(2000, reset)
                
        threading.Thread(target=_test, daemon=True).start()

    def toggle_pause_test(self):
        if not self.testing: return
        self.testing_paused = not self.testing_paused
        if self.testing_paused:
            self.btn_pause.configure(text="RESUME", fg_color=COLORS["success"])
            self.log("Testing PAUSED.")
        else:
            self.btn_pause.configure(text="PAUSE", fg_color=COLORS["warning"])
            self.log("Testing RESUMED.")

    def toggle_test(self):
        if self.testing:
            self.testing = False
            self.testing_paused = False
            self.btn_test.configure(text="TEST ALL", fg_color=COLORS["success"])
            self.btn_pause.configure(state="disabled", text="PAUSE", fg_color=COLORS["warning"])
        else:
            if not self.proxies: return self.log("Load proxies first.")
            self.testing = True
            self.testing_paused = False
            self.btn_test.configure(text="STOP", fg_color=COLORS["danger"])
            self.btn_pause.configure(state="normal", text="PAUSE", fg_color=COLORS["warning"])
            
            self.proxy_grid.clear()
            threading.Thread(target=self.tester_thread, daemon=True).start()

    def tester_thread(self):
        self.progress_bar.pack(fill="x", pady=(0, 5))
        try:
            url = self.entry_test_url.get()
            to = int(self.entry_timeout.get())
            if to < 100: to = 100
            if to > 10000: to = 10000

            th = int(self.entry_check_threads.get())
            hide_dead = self.chk_hide_dead.get()
            
            # Prepare ProxyConfig objects from self.proxies (strings)
            # self.proxies contains strings like "http://1.2.3.4:80" or just "1.2.3.4:80"
            check_configs = []
            allowed_protos = []
            if self.chk_http.get(): allowed_protos.append("http")
            if self.chk_socks4.get(): allowed_protos.append("socks4")
            if self.chk_socks5.get(): allowed_protos.append("socks5")
            
            for p_str in self.proxies:
                try:
                    if "://" in p_str:
                        parts = p_str.split("://")
                        scheme = parts[0].lower()
                        addr = parts[1]
                        
                        # Treat https as http for validation against allowed_protos
                        check_scheme = "http" if scheme == "https" else scheme
                        
                        if check_scheme not in allowed_protos: continue
                    else:
                        # Ambiguous proxy, try all allowed protocols?
                        # Or default to HTTP. For checking, we usually want to know what it is.
                        # The old logic checked all allowed.
                        addr = p_str
                        scheme = "ambiguous"

                    if ":" in addr:
                        host, port = addr.split(":")[:2]
                        port = int(port)
                        
                        if scheme == "ambiguous":
                            for proto in allowed_protos:
                                check_configs.append(ProxyConfig(host=host, port=port, protocol=proto))
                        else:
                            # Map https -> http for config
                            protocol = "http" if scheme == "https" else scheme
                            check_configs.append(ProxyConfig(host=host, port=port, protocol=protocol))
                except:
                    pass

        except Exception as e:
            self.log_safe(f"Config Error: {e}")
            return

        self.log_safe(f"Testing {len(check_configs)} proxies (Threaded/TLS)...")

        manager = ThreadedProxyManager()
        
        last_time = time.time()
        last_count = 0

        # We need a callback that is thread-safe
        def on_progress(res: ProxyCheckResult, idx, total):
            nonlocal last_time, last_count
            if not self.testing: return # Stop signal

            if hide_dead and res.status != "Active":
                pass
            else:
                item = {
                    "ip": res.proxy.host,
                    "port": str(res.proxy.port),
                    "type": res.type,
                    "country": res.country,
                    "country_code": res.country_code,
                    "status": res.status,
                    "speed": res.speed,
                    "anonymity": res.anonymity
                }
                self.buffer.append(item)

            # Update progress bar and bandwidth occasionally
            if idx % 10 == 0 or idx == total:
                 now = time.time()
                 delta = now - last_time
                 if delta >= 1.0:
                     diff = idx - last_count
                     # Est. 3KB per check (SSL handshake is heavy)
                     # Mbps = (diff * 3KB * 8 bits) / 1024 / 1024 / delta
                     mbps = (diff * 3 * 8) / 1024 / delta 
                     self.after(0, lambda m=mbps: self.lbl_bandwidth.configure(text=f"Checker BW: {m:.2f} Mbps"))
                     last_time = now
                     last_count = idx
                 
                 self.after(0, lambda p=idx/total: self.progress_bar.set(p))

        # Run threaded check
        manager.check_proxies(
            check_configs, url, to, self.real_ip, on_progress, concurrency=th,
            pause_checker=lambda: self.testing_paused
        )

        self.testing = False
        self.after(0, lambda: self.progress_bar.pack_forget())
        self.after(0, lambda: self.btn_test.configure(text="TEST ALL", fg_color=COLORS["success"]))
        self.after(0, lambda: self.btn_pause.configure(state="disabled", text="PAUSE", fg_color=COLORS["warning"]))
        self.log_safe("Testing complete.")

    def toggle_attack(self):
        if self.running:
            self.running = False
            self.btn_attack.configure(text="START CAMPAIGN", fg_color=COLORS["success"])
            if self.engine:
                self.engine.stop()
            self.log("Stopping campaign...")
        else:
            self.running = True
            self.btn_attack.configure(text="STOP CAMPAIGN", fg_color=COLORS["danger"])
            
            # Start Async Engine in a separate thread
            self.engine_thread = threading.Thread(target=self.run_async_engine, daemon=True)
            self.engine_thread.start()

    def run_async_engine(self):
        url = self.entry_url.get()
        try:
            threads = int(self.slider_threads.get())
        except:
            threads = 1
            
        v_min = int(self.slider_view_min.get())
        v_max = int(self.slider_view_max.get())
        if v_min > v_max: v_min, v_max = v_max, v_min

        self.log(f"Starting Async Engine: {threads} threads on {url}")

        # Prepare Proxies
        all_active = self.proxy_grid.get_active_objects()
        allowed = []
        if self.chk_http.get(): allowed.append("HTTP")
        if self.chk_http.get(): allowed.append("HTTPS")
        if self.chk_socks4.get(): allowed.append("SOCKS4")
        if self.chk_socks5.get(): allowed.append("SOCKS5")

        engine_proxies = []
        for p in all_active:
             if any(a in p['type'] for a in allowed):
                 # Convert grid dict to ProxyConfig
                 # Grid item: {'ip': '1.2.3.4', 'port': '80', 'type': 'HTTP', ...}
                 try:
                     proto = p['type'].lower()
                     if "socks4" in proto: protocol = "socks4"
                     elif "socks5" in proto: protocol = "socks5"
                     else: protocol = "http"
                     
                     engine_proxies.append(ProxyConfig(
                         host=p['ip'],
                         port=int(p['port']),
                         protocol=protocol
                     ))
                 except:
                     pass

        if not engine_proxies and all_active:
            self.log_safe(f"Warning: Proxies active but filtered by protocol.")
        elif not engine_proxies:
            self.log_safe("No active proxies found. Running direct.")

        self.active_proxy_count = len(engine_proxies)
        
        # Config
        config = TrafficConfig(
            target_url=url,
            max_threads=threads,
            total_visits=0, # Infinite
            min_duration=v_min,
            max_duration=v_max,
            headless=self.settings.get("headless", True)
        )

        # Initialize Engine
        self.engine = AsyncTrafficEngine(config, engine_proxies, on_update=self.on_engine_update)
        
        # Run Async Loop
        asyncio.run(self.engine.run())
        
        self.running = False
        self.after(0, lambda: self.btn_attack.configure(text="START CAMPAIGN", fg_color=COLORS["success"]))
        self.log_safe("Campaign finished.")

    def reset_stats(self):
        self.stats = {"req": 0, "success": 0, "fail": 0}
        self.active_proxy_count = 0
        self.lbl_stats["req"].configure(text="0")
        self.lbl_stats["success"].configure(text="0")
        self.lbl_stats["fail"].configure(text="0")
        self.log("Campaign statistics reset.")

    def on_engine_update(self, stats: TrafficStats):
        # Callback from async engine, must invoke on main thread
        self.stats["req"] = stats.total_requests
        self.stats["success"] = stats.success
        self.stats["fail"] = stats.failed
        self.active_proxy_count = stats.active_proxies
        # We don't need to force update GUI here, update_gui_loop handles it periodically

    def log_safe(self, msg):
        self.after(0, lambda: self.log(msg))

    def save_cfg(self):
        try:
            self.settings["target_url"] = self.entry_url.get()
            self.settings["threads"] = int(self.slider_threads.get())
            self.settings["viewtime_min"] = int(self.slider_view_min.get())
            self.settings["viewtime_max"] = int(self.slider_view_max.get())
            self.settings["proxy_test_url"] = self.entry_test_url.get()

            # Save timeout with clamp
            t_val = int(self.entry_timeout.get())
            if t_val < 100: t_val = 100
            if t_val > 10000: t_val = 10000
            self.settings["proxy_timeout"] = t_val

            self.settings["proxy_check_threads"] = int(self.entry_check_threads.get())
            self.settings["proxy_scrape_threads"] = int(self.entry_scrape_threads.get())
            self.settings["scraper_proxy"] = self.entry_scraper_proxy.get().strip()
            self.settings["scraper_proxy_protocol"] = self.combo_scraper_proto.get()
            self.settings["use_scraper_proxy"] = self.chk_use_scraper_proxy.get()
            self.settings["use_http"] = self.chk_http.get()
            self.settings["use_socks4"] = self.chk_socks4.get()
            self.settings["use_socks5"] = self.chk_socks5.get()
            self.settings["hide_dead"] = self.chk_hide_dead.get()
            self.settings["headless"] = self.chk_headless.get()
            Utils.save_settings(self.settings)
            self.log("Settings saved.")
        except Exception as e:
            self.log(f"Error saving settings: {e}")

    def update_gui_loop(self):
        if self.buffer:
            chunk = self.buffer[:40]
            del self.buffer[:40]
            for i in chunk: self.proxy_grid.add(i)
            if len(self.buffer) % 5 == 0: self.update_proxy_stats()

        self.lbl_stats["req"].configure(text=str(self.stats["req"]))
        self.lbl_stats["success"].configure(text=str(self.stats["success"]))
        self.lbl_stats["fail"].configure(text=str(self.stats["fail"]))
        self.lbl_stats["proxies"].configure(text=str(self.active_proxy_count))

        self.after(100, self.update_gui_loop)
