import tkinter as tk
from tkinter import messagebox, scrolledtext
from PIL import Image, ImageTk
import os, subprocess, random, math, sys, fcntl
from datetime import datetime

# --- SINGLE INSTANCE SHIELD ---
try:
    lock_file = open('/tmp/sumner_hud.lock', 'w')
    fcntl.lockf(lock_file, fcntl.LOCK_EX | fcntl.LOCK_NB)
except:
    sys.exit(0)

class SumnerHUD:
    def __init__(self, root):
        self.root = root
        self.sw = self.root.winfo_screenwidth()
        self.sh = self.root.winfo_screenheight()
        self.root.attributes('-fullscreen', True, "-topmost", True)
        self.root.config(bg='black')

        # --- PATHS ---
        self.path_allsky = "/var/www/html/allsky/images/latest.jpg"
        self.path_radar = "/home/pi/allsky_guard/radar.png"
        self.path_clock = "/home/pi/allsky_guard/clock_sumner.png"
        self.path_sensors = "/home/pi/allsky_guard/sensors.txt"
        self.path_hours = "/home/pi/allsky_guard/hours.txt"
        self.path_notes = "/home/pi/allsky_guard/dossier.txt"
        self.path_mirror_cfg = "/home/pi/allsky_guard/mirror_config.txt"
        self.path_thresh = "/home/pi/allsky_guard/cloud_threshold.txt"
        self.path_radar_id = "/home/pi/allsky_guard/radar_coords.txt"
        self.path_sync_script = "/home/pi/allsky_guard/get_radar.py"
        
        self.app_manager = "/usr/share/applications/indigo-server-manager.desktop"
        self.app_imager = "/usr/share/applications/ain-imager.desktop"

        # --- LOAD SAVED SENSITIVITY ---
        self.cloud_threshold = 30.0
        if os.path.exists(self.path_thresh):
            try:
                with open(self.path_thresh, "r") as f:
                    self.cloud_threshold = float(f.read().strip())
            except: pass

        self.canvas = tk.Canvas(root, width=self.sw, height=self.sh, bg='black', highlightthickness=0)
        self.canvas.pack()
        
        self.draw_stars()
        self.create_ui_elements()
        self.check_cleaning_reminder()
        self.update_loop()

    def update_threshold(self, val):
        self.cloud_threshold = float(val)
        try:
            with open(self.path_thresh, "w") as f:
                f.write(str(self.cloud_threshold))
        except: pass

    def toggle_roof(self):
        messagebox.showinfo("ROOF CONTROL", "Roof Command Sent")

    def launch_seestar(self):
        w, h, x, y = "450", "900", "100", "100"
        if os.path.exists(self.path_mirror_cfg):
            try:
                with open(self.path_mirror_cfg, "r") as f:
                    coords = f.read().strip().split(',')
                    if len(coords) == 4: w, h, x, y = coords
            except: pass
        subprocess.Popen(["/snap/bin/scrcpy", "--always-on-top", "--window-title", "Seestar Live",
               "--max-size", "1920", "--video-bit-rate", "4M", "--max-fps", "30",
               "--window-x", x, "--window-y", y, "--window-width", w, "--window-height", h])

    def create_ui_elements(self):
        self.canvas.create_text(self.sw//2, 25, text="--- OBSERVATORY CONTROLS ---", fill="#FFCC00", font=("Arial", 12, "bold"))
        
        tk.Button(self.root, text="🚀 INDIGO", bg="#003300", fg="white", font=("Arial", 9, "bold"), command=lambda: subprocess.Popen(["gio", "launch", self.app_manager])).place(x=self.sw//2 - 210, y=45)
        tk.Button(self.root, text="🔭 IMAGER", bg="#001133", fg="white", font=("Arial", 9, "bold"), command=lambda: subprocess.Popen(["gio", "launch", self.app_imager])).place(x=self.sw//2 - 80, y=45)
        tk.Button(self.root, text="📱 SEESTAR (V40)", bg="#4B0082", fg="white", font=("Arial", 9, "bold"), command=self.launch_seestar).place(x=self.sw//2 + 50, y=45)
        tk.Button(self.root, text="MAINT / DOSSIER", command=self.open_dossier, bg="#222", fg="white", font=("Arial", 9, "bold")).place(x=20, y=20)
        tk.Button(self.root, text="EXIT HUD", command=self.root.destroy, bg="#500", fg="white", font=("Arial", 9, "bold")).place(x=150, y=20)

        box_w, box_h = int(self.sw * 0.25), int(self.sh * 0.85)
        rx, ry = self.sw - box_w - 20, 40
        self.canvas.create_rectangle(rx, ry, rx + box_w, ry + box_h, fill='#050505', outline='#00FFCC', width=3)
        
        y_off, spacing = ry + 45, box_h // 12.5
        self.val_sky   = self.add_sensor_line("🌡️", "SKY TEMP:", rx + 15, y_off, "#AAB7B8", box_w)
        self.val_cloud = self.add_sensor_line("☁️", "SKY COND:", rx + 15, y_off + spacing, "#5DADE2", box_w)
        
        self.slider = tk.Scale(self.root, from_=5, to=60, orient='horizontal', bg='#050505', fg='white', troughcolor='#500', activebackground='red', highlightthickness=0, font=("Arial", 8), command=self.update_threshold)
        self.slider.set(self.cloud_threshold)
        self.slider.place(x=rx + 55, y=y_off + spacing + 18, width=box_w - 80)

        y_mid = y_off + (spacing * 2.8)
        self.val_amb   = self.add_sensor_line("🌡️", "AMB TEMP:", rx + 15, y_mid, "#EC7063", box_w)
        self.val_hum   = self.add_sensor_line("💧", "HUMIDITY:", rx + 15, y_mid + spacing, "#5499C7", box_w)
        self.val_dew   = self.add_sensor_line("✨", "DEW POINT:", rx + 15, y_mid + spacing*2, "#A569BD", box_w)
        self.val_pres  = self.add_sensor_line("⏲️", "PRESSURE:", rx + 15, y_mid + spacing*3, "#58D68D", box_w)
        self.val_wind  = self.add_sensor_line("💨", "WIND SPD:", rx + 15, y_mid + spacing*4, "#F4D03F", box_w)
        self.val_rain  = self.add_sensor_line("☔", "RAIN DET:", rx + 15, y_mid + spacing*5, "#AF7AC5", box_w)
        self.val_dome  = self.add_sensor_line("🏠", "ROOF STAT:", rx + 15, y_mid + spacing*6, "#EB984E", box_w)
        
        self.roof_btn = tk.Button(self.root, text="OPEN / CLOSE ROOF", bg="#500", fg="white", activebackground="red", font=("Arial", 8, "bold"), command=self.toggle_roof)
        self.roof_btn.place(x=rx + 55, y=y_mid + spacing*6 + 22, width=box_w - 80)

        y_bot = y_mid + spacing*8
        self.val_hrs   = self.add_sensor_line("⌛", "OP HOURS:", rx + 15, y_bot, "#FFCC00", box_w)
        self.sync_light = self.canvas.create_oval(rx + 15, y_bot - 8, rx + 31, y_bot + 8, fill="gray", outline="white")

        self.all_img_id = self.canvas.create_image(self.sw*0.22, self.sh*0.4, anchor='center', tags="zoom")
        self.rad_img_id = self.canvas.create_image(self.sw*0.53, self.sh*0.4, anchor='center', tags="zoom")
        self.clk_img_id = self.canvas.create_image(self.sw*0.38, self.sh*0.82, anchor='center', tags="zoom")

        self.canvas.tag_bind(self.all_img_id, "<Button-1>", lambda e: self.popout(self.path_allsky))
        self.canvas.tag_bind(self.rad_img_id, "<Button-1>", lambda e: self.popout(self.path_radar))
        self.canvas.tag_bind(self.clk_img_id, "<Button-1>", lambda e: self.popout(self.path_clock))

    def add_sensor_line(self, icon, label, x, y, color, box_w):
        f_size = 11 if self.sw > 1000 else 8
        self.canvas.create_text(x, y, text=icon, anchor='w', fill=color, font=("Arial", 16))
        self.canvas.create_text(x + 40, y, text=label, anchor='w', fill="white", font=("Arial", f_size, "bold"))
        return self.canvas.create_text(x + box_w - 30, y, text="--", anchor='e', fill="cyan", font=("Courier", 16, "bold"))

    def popout(self, path):
        if not os.path.exists(path): return
        pop = tk.Toplevel(self.root)
        pop.attributes("-fullscreen", True, "-topmost", True)
        pop.config(bg='black')
        img = Image.open(path)
        if "radar" in path.lower():
            new_h = int(self.sh * 0.88)
            ratio = new_h / float(img.size[1])
            new_w = int(float(img.size[0]) * ratio)
            img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
        else:
            img.thumbnail((int(self.sw * 0.8), int(self.sh * 0.8)), Image.Resampling.LANCZOS)
        self.p_img = ImageTk.PhotoImage(img)
        tk.Button(pop, image=self.p_img, bg='black', bd=0, activebackground='black', command=pop.destroy).pack(expand=True)

    def open_dossier(self):
        d_win = tk.Toplevel(self.root)
        d_win.geometry(f"{int(self.sw*0.45)}x{int(self.sh*0.8)}")
        d_win.config(bg="#050505")
        d_win.attributes("-topmost", True)
        tk.Label(d_win, text="SYSTEM DOSSIER", bg="#050505", fg="#FFCC00", font=("Arial", 18, "bold")).pack(pady=10)
        
        m_frame = tk.Frame(d_win, bg="#111")
        m_frame.pack(fill="x", padx=20)
        tk.Label(m_frame, text="Mirror Config:", bg="#111", fg="white").pack(side="left")
        cfg_entry = tk.Entry(m_frame, bg="black", fg="cyan", insertbackground="white")
        cfg_entry.pack(side="left", padx=10, fill="x", expand=True)
        if os.path.exists(self.path_mirror_cfg):
            with open(self.path_mirror_cfg, "r") as f: cfg_entry.insert(0, f.read().strip())

        # RADAR STATION ID INPUT
        r_frame = tk.Frame(d_win, bg="#111")
        r_frame.pack(fill="x", padx=20, pady=5)
        tk.Label(r_frame, text="Radar Station:", bg="#111", fg="white").pack(side="left")
        radar_entry = tk.Entry(r_frame, bg="black", fg="orange", insertbackground="white")
        radar_entry.pack(side="left", padx=10, fill="x", expand=True)
        if os.path.exists(self.path_radar_id):
            with open(self.path_radar_id, "r") as f: radar_entry.insert(0, f.read().strip())

        txt = scrolledtext.ScrolledText(d_win, bg="black", fg="#00FFCC", font=("Courier", 14), insertbackground="white")
        txt.pack(padx=20, pady=5, expand=True, fill='both')
        if os.path.exists(self.path_notes):
            with open(self.path_notes, "r") as f: txt.insert('1.0', f.read())
        
        def save_all():
            with open(self.path_mirror_cfg, "w") as f: f.write(cfg_entry.get())
            # Ensure the Radar ID is stripped of spaces and saved correctly
            with open(self.path_radar_id, "w") as f: f.write(radar_entry.get().upper().strip())
            with open(self.path_notes, 'w') as f: f.write(txt.get('1.0', 'end'))
            d_win.destroy()

        def reset_hrs():
            if messagebox.askyesno("RESET", "Reset Maintenance Timer to 0?"):
                with open(self.path_hours, "w") as f: f.write("0.0")
                messagebox.showinfo("SUCCESS", "Timer Reset.")

        def force_sync():
            subprocess.Popen(["python3", self.path_sync_script])
            messagebox.showinfo("SYNC", "Radar Sync Started...")

        btn_f = tk.Frame(d_win, bg="#050505")
        btn_f.pack(fill="x", side="bottom", pady=20)
        tk.Button(btn_f, text="♻ RESET", bg="#D4AC0D", fg="black", font=("Arial", 11, "bold"), command=reset_hrs).pack(side="left", padx=20)
        tk.Button(btn_f, text="🔄 FORCE SYNC", bg="#4B0082", fg="white", font=("Arial", 11, "bold"), command=force_sync).pack(side="left", padx=10)
        tk.Button(btn_f, text="💾 SAVE", bg="#1E8449", fg="white", font=("Arial", 11, "bold"), command=save_all).pack(side="right", padx=20)

    def check_cleaning_reminder(self):
        if os.path.exists(self.path_hours):
            try:
                with open(self.path_hours, "r") as f:
                    hrs = float(f.read().strip())
                    if hrs >= 1000.0:
                        messagebox.showwarning("MAINTENANCE", f"Alert: {hrs:.1f} Hours.\nClean dome/sensors.")
            except: pass

    def draw_stars(self):
        for _ in range(60):
            x, y = random.randint(0, self.sw), random.randint(0, self.sh)
            self.canvas.create_oval(x, y, x+1, y+1, fill='white', outline='white')

    def load_scale(self, path, w, h):
        if not os.path.exists(path): return None
        try:
            # FIX: Explicitly open and close the file to avoid lock issues
            with Image.open(path) as raw_img:
                img = raw_img.convert("RGB")
                img.thumbnail((w, h), Image.Resampling.LANCZOS)
                return ImageTk.PhotoImage(img)
        except Exception as e: 
            print(f"HUD Load Error ({path}): {e}")
            return None

    def update_loop(self):
        img_w, img_h = int(self.sw * 0.28), int(self.sh * 0.45)
        
        # 1. Update Allsky Image
        new_all = self.load_scale(self.path_allsky, img_w, img_h)
        if new_all: 
            self.img_all = new_all # Keep reference to prevent GC
            self.canvas.itemconfig(self.all_img_id, image=self.img_all)
        
        # 2. Update Radar Image (This now swaps correctly)
        new_rad = self.load_scale(self.path_radar, img_w, img_h)
        if new_rad: 
            self.img_rad = new_rad 
            self.canvas.itemconfig(self.rad_img_id, image=self.img_rad)
        
        # 3. Update Clock Image
        new_clk = self.load_scale(self.path_clock, int(self.sw*0.5), int(self.sh*0.35))
        if new_clk: 
            self.img_clk = new_clk
            self.canvas.itemconfig(self.clk_img_id, image=self.img_clk)

        if os.path.exists(self.path_hours):
            try:
                mtime = os.path.getmtime(self.path_hours)
                diff = (datetime.now().timestamp() - mtime) / 60
                self.canvas.itemconfig(self.sync_light, fill="#00FF00" if diff < 20 else "#FF0000")
                with open(self.path_hours, "r") as f:
                    self.canvas.itemconfig(self.val_hrs, text=f"{f.read().strip()} HRS")
            except: pass

        if os.path.exists(self.path_sensors):
            try:
                sky_t, amb_t, hum_val = None, None, None
                with open(self.path_sensors, "r") as f:
                    for line in f:
                        u_line = line.upper().strip()
                        if ":" not in u_line: continue
                        val = line.split(":", 1)[-1].strip()

                        if "SKY TEMP" in u_line: 
                            self.canvas.itemconfig(self.val_sky, text=val)
                            try: sky_t = float(''.join(c for c in val if c in '0123456789.-'))
                            except: pass
                        elif "AMB TEMP" in u_line: 
                            self.canvas.itemconfig(self.val_amb, text=val)
                            try: amb_t = float(''.join(c for c in val if c in '0123456789.-'))
                            except: pass
                        elif "HUMIDITY" in u_line: 
                            self.canvas.itemconfig(self.val_hum, text=val)
                            try: hum_val = float(''.join(c for c in val if c in '0123456789.-'))
                            except: pass
                        elif "PRES" in u_line:
                            try:
                                raw_p = float(''.join(c for c in val if c in '0123456789.-'))
                                if raw_p > 0:
                                    inches_p = raw_p * 0.02953
                                    self.canvas.itemconfig(self.val_pres, text=f"{inches_p:.2f} in")
                                else:
                                    self.canvas.itemconfig(self.val_pres, text="LOW")
                            except Exception as e: 
                                self.canvas.itemconfig(self.val_pres, text=val)
                        elif "WIND SPD" in u_line: self.canvas.itemconfig(self.val_wind, text=val)
                        elif "PRECIP" in u_line or "RAIN" in u_line: 
                            self.canvas.itemconfig(self.val_rain, text=val, fill="red" if "WET" in val.upper() else "cyan")
                        elif "DOME" in u_line or "ROOF" in u_line: 
                            self.canvas.itemconfig(self.val_dome, text=val)

                if sky_t is not None and amb_t is not None:
                    delta = amb_t - sky_t
                    status = "CLEAR" if delta > self.cloud_threshold else "CLOUDY"
                    self.canvas.itemconfig(self.val_cloud, text=status, fill="lightgreen" if status == "CLEAR" else "orange")
                
                if amb_t is not None and hum_val is not None:
                    T = (amb_t - 32) * 5/9
                    gamma = (math.log(hum_val/100) + ((17.27 * T) / (237.3 + T)))
                    dew_f = ((237.3 * gamma) / (17.27 - gamma) * 9/5) + 32
                    self.canvas.itemconfig(self.val_dew, text=f"{dew_f:.1f} F")
            except Exception as e: print(f"Parser Error: {e}")

        self.root.after(5000, self.update_loop)

if __name__ == "__main__":
    root = tk.Tk()
    app = SumnerHUD(root)
    root.mainloop()
