import customtkinter as ctk
from tkinter import Canvas
from .styles import COLORS
from .utils import Utils

class VirtualGrid(ctk.CTkFrame):
    def __init__(self, master, columns, **kwargs):
        super().__init__(master, **kwargs)
        self.data = []
        self.row_h = 30
        self.sort_reverse = False

        self.headers = ctk.CTkFrame(self, height=35, fg_color=COLORS["nav"], corner_radius=0)
        self.headers.pack(fill="x")

        self.col_map = columns
        for i, col in enumerate(columns):
            self.headers.columnconfigure(i, weight=1)
            btn = ctk.CTkButton(
                self.headers, text=col, font=("Roboto", 11, "bold"),
                fg_color="transparent", hover_color=COLORS["card"],
                text_color=COLORS["accent"], command=lambda c=col: self.sort_by(c)
            )
            btn.grid(row=0, column=i, sticky="ew")

        self.canvas = Canvas(self, bg=COLORS["bg"], highlightthickness=0)
        self.scr = ctk.CTkScrollbar(self, command=self.canvas.yview, width=14, fg_color=COLORS["bg"])
        self.canvas.configure(yscrollcommand=self.scr.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scr.pack(side="right", fill="y")
        self.canvas.bind("<Configure>", self.draw)
        self.canvas.bind("<MouseWheel>",
                         lambda e: (self.canvas.yview_scroll(int(-1 * (e.delta / 120)), "units"), self.draw()))

    def sort_by(self, col_name):
        key_map = {
            "Address": "ip", "Proto": "type", "Country": "country_code",
            "Status": "status", "Ping": "speed", "Anon": "anonymity"
        }
        key = key_map.get(col_name, "speed")
        self.sort_reverse = not self.sort_reverse
        try:
            self.data.sort(key=lambda x: x[key], reverse=self.sort_reverse)
        except:
            self.data.sort(key=lambda x: str(x[key]), reverse=self.sort_reverse)
        self.draw()

    def add(self, item):
        self.data.append(item)
        self.draw()

    def clear(self):
        self.data = []
        self.canvas.delete("all")
        self.draw()

    def get_active_objects(self):
        return [d for d in self.data if d['status'] == "Active"]

    def get_active(self):
        return [f"{d['type'].lower()}://{d['ip']}:{d['port']}" for d in self.data if d['status'] == "Active"]

    def get_counts(self):
        counts = {"HTTP": 0, "HTTPS": 0, "SOCKS4": 0, "SOCKS5": 0}
        for d in self.data:
            t = d.get('type', 'HTTP').upper()
            if t == "HTTPS":
                counts["HTTPS"] += 1
            elif "HTTP" in t:
                counts["HTTP"] += 1
            elif "SOCKS4" in t:
                counts["SOCKS4"] += 1
            elif "SOCKS5" in t:
                counts["SOCKS5"] += 1
        return counts

    def draw(self, _=None):
        self.canvas.delete("all")
        w, h = self.canvas.winfo_width(), self.canvas.winfo_height()
        total_h = len(self.data) * self.row_h
        self.canvas.configure(scrollregion=(0, 0, w, total_h))

        y_off = self.canvas.yview()[0] * total_h
        start = int(y_off // self.row_h)
        end = start + int(h // self.row_h) + 2
        col_w = w / 6

        for i in range(start, min(end, len(self.data))):
            item = self.data[i]
            y = i * self.row_h
            bg_col = COLORS["card"] if i % 2 == 0 else COLORS["bg"]
            self.canvas.create_rectangle(0, y, w, y + self.row_h, fill=bg_col, width=0)

            vals = [
                f"{item['ip']}:{item['port']}", item['type'],
                f"{Utils.get_flag(item['country_code'])} {item['country_code']}",
                item['status'], f"{item['speed']} ms", item['anonymity']
            ]
            for c, val in enumerate(vals):
                # Color-code: Status (col 3) and Ping (col 4)
                if c == 3:  # Status column
                    color = COLORS["success"] if val == "Active" else COLORS["danger"]
                elif c == 4:  # Ping column - color by speed
                    speed = item.get('speed', 9999)
                    if speed <= 2500:
                        color = COLORS["success"]  # Green
                    elif speed <= 5000:
                        color = "#F1C40F"          # Yellow
                    elif speed <= 7500:
                        color = COLORS["warning"]  # Orange
                    else:
                        color = COLORS["danger"]   # Red
                else:
                    color = COLORS["text"]
                self.canvas.create_text((c * col_w) + 10, y + 15, text=str(val), fill=color, anchor="w",
                                        font=("Roboto", 10))
