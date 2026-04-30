import tkinter as tk
from tkinter import messagebox, scrolledtext
from PIL import Image, ImageTk, ImageDraw
import os, subprocess, random, math, sys, fcntl, socket
import smtplib
from email.message import EmailMessage
from datetime import datetime
import cv2
import numpy as np

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

        # --- EMAIL CREDENTIALS ---
        self.email_sender = "bsbachert@gmail.com"
        self.email_pass = "pucapkfuesrrnasm" 
        self.path_email = "/home/pi/allsky_guard/email_receiver.txt"
        self.email_receiver = "bsbachert@gmail.com"
        
        if os.path.exists(self.path_email):
            try:
                with open(self.path_email, "r") as f:
                    content = f.read().strip()
                    if content: self.email_receiver = content
            except: pass

        # --- PATHS ---
        self.path_allsky = "/var/www/html/allsky/images/latest.jpg"
        self.path_radar = "/home/pi/allsky_guard/radar.png"
        self.path_clock = "/home/pi/allsky_guard/clock.png" 
        self.path_sensors = "/home/pi/allsky_guard/sensors.txt"
        self.path_hours = "/home/pi/allsky_guard/hours.txt"
        self.path_notes = "/home/pi/allsky_guard/dossier.txt"
        self.path_thresh = "/home/pi/allsky_guard/cloud_threshold.txt"
        self.path_star_thresh = "/home/pi/allsky_guard/star_threshold.txt"
        self.path_seestar_ip = "/home/pi/allsky_guard/seestar_ip.txt"
        self.path_fingerbot_mac = "/home/pi/allsky_guard/fingerbot_mac.txt"
        self.path_roof_cmd = "/home/pi/allsky_guard/roof_cmd.txt"
        self.path_radar_id = "/home/pi/allsky_guard/radar_coords.txt"
        self.path_csk_id = "/home/pi/allsky_guard/csk_id.txt"
        self.path_sync_script = "/home/pi/allsky_guard/get_radar.py"

        self.img_all = None
        self.img_rad = None
        self.img_clk = None
        self.seestar_ip = "0.0.0.0"
        self.last_allsky_ts = 0
        
        self.last_roof_safety_state = None
        self.emergency_sent = False
        self.dusk_sent_today = None
        
        # --- AI TUNING ---
        self.ai_brightness_trigger = 60.0
        self.ai_color_trigger = 7.0
        self.star_threshold = 18

        self.cloud_threshold = 30.0
        if os.path.exists(self.path_thresh):
            try:
                with open(self.path_thresh, "r") as f:
                    self.cloud_threshold = float(f.read().strip())
            except: pass

        if os.path.exists(self.path_star_thresh):
            try:
                with open(self.path_star_thresh, "r") as f:
                    self.star_threshold = int(f.read().strip())
            except: pass
            
        if os.path.exists(self.path_seestar_ip):
            try:
                with open(self.path_seestar_ip, "r") as f:
                    self.seestar_ip = f.read().strip()
            except: pass

        self.canvas = tk.Canvas(root, width=self.sw, height=self.sh, bg='black', highlightthickness=0)
        self.canvas.pack()
        
        self.draw_stars()
        self.create_ui_elements()
        self.check_cleaning_reminder()
        self.send_email_notification("System Power Recovery", "The Observatory HUD has restarted successfully.")
        self.update_loop()

    def send_email_notification(self, subject, body):
        try:
            msg = EmailMessage()
            msg.set_content(body)
            msg['Subject'] = subject
            msg['From'] = self.email_sender
            msg['To'] = self.email_receiver
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(self.email_sender, self.email_pass)
            server.send_message(msg)
            server.quit()
        except Exception as e: print(f"Email Error: {e}")

    def run_ai_clear_check(self, manual_click=False):
        """Centered Circular Mask with a Linear Left Cutoff for Trees."""
        if not os.path.exists(self.path_allsky):
            self.btn_ai.config(text="NO IMAGE", bg="#555")
            return

        try:
            img = cv2.imread(self.path_allsky)
            if img is None: return
            
            h, w = img.shape[:2]
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            if np.mean(gray) > self.ai_brightness_trigger:
                self.btn_ai.config(text="DAYTIME / OFF", bg="#222")
                return

            # --- MASK CREATION ---
            mask = np.zeros((h, w), dtype=np.uint8)
            cx, cy = int(w / 2), int(h / 2)
            
            # Base Sky Circle (38% radius)
            radius = int(h * 0.38)
            cv2.circle(mask, (cx, cy), radius, 255, -1)

            # THE CUTOFF: Remove the left ~25% of the circle area
            # Adjusted X boundary to shave off branches
            cutoff_x = int(cx - (radius * 0.50)) 
            cv2.rectangle(mask, (0, 0), (cutoff_x, h), 0, -1)

            masked_gray = cv2.bitwise_and(gray, gray, mask=mask)

            # Detect Blobs (Clouds)
            b_params = cv2.SimpleBlobDetector_Params()
            b_params.filterByArea = True
            b_params.minArea = 400 
            blob_detector = cv2.SimpleBlobDetector_create(b_params)
            blobs = blob_detector.detect(masked_gray)
            blob_count = len(blobs)

            # Detect Stars
            s_params = cv2.SimpleBlobDetector_Params()
            s_params.filterByArea, s_params.minArea, s_params.maxArea = True, 10, 150
            s_params.filterByCircularity, s_params.minCircularity = True, 0.8  
            star_detector = cv2.SimpleBlobDetector_create(s_params)
            stars = star_detector.detect(masked_gray)
            star_count = len(stars)

            # Debug Output
            debug_path = "/tmp/star_debug.jpg"
            debug_img = img.copy()
            # Draw yellow circle and red cutoff line
            cv2.circle(debug_img, (cx, cy), radius, (0, 255, 255), 2)
            cv2.line(debug_img, (cutoff_x, cy - radius), (cutoff_x, cy + radius), (0, 0, 255), 3)
            
            for s in stars:
                cv2.circle(debug_img, (int(s.pt[0]), int(s.pt[1])), 15, (0, 0, 255), 2)
            cv2.imwrite(debug_path, debug_img)

            if star_count >= self.star_threshold and blob_count < 2:
                status, color = "AI CLEAR", "#1E8449"
            elif blob_count <= 4:
                status, color = "SOME CLOUDS", "#D4AC0D"
            else:
                status, color = "AI CLOUDY", "#922B21"

            self.btn_ai.config(text=f"{status}\n(S:{star_count} B:{blob_count})", bg=color)
            if manual_click: self.popout(debug_path)
            
        except Exception as e:
            self.btn_ai.config(text="AI ERROR", bg="#555")
            print(f"AI Check Error: {e}")

    def update_ai_bright(self, val): self.ai_brightness_trigger = float(val)
    def update_ai_color(self, val): self.ai_color_trigger = float(val)

    def open_browser(self):
        url = "http://localhost:5432"
        try: subprocess.Popen(["/usr/bin/chromium", f"--app={url}", f"--window-size={int(self.sw*0.75)},{int(self.sh*0.85)}", "--window-position=20,80"])
        except: subprocess.Popen(["x-www-browser", url])

    def manual_open(self):
        with open(self.path_roof_cmd, "w") as f: f.write("OPEN")
        messagebox.showinfo("ROOF", "Manual OPEN command sent.")

    def manual_close(self):
        with open(self.path_roof_cmd, "w") as f: f.write("CLOSE")
        messagebox.showinfo("ROOF", "Manual CLOSE command sent.")

    def trigger_fingerbot(self):
        try:
            subprocess.Popen(["python3", "/home/pi/allsky_guard/seestar_push.py"])
            self.power_btn.config(bg="red", text="⚡ SENDING...")
            self.root.after(2000, lambda: self.power_btn.config(bg="#900", text="⚡ SEESTAR"))
        except: messagebox.showerror("ERROR", "Could not run seestar_push.py")

    def run_health_check(self):
        report = []
        if os.path.exists(self.path_sensors):
            mtime = os.path.getmtime(self.path_sensors)
            report.append("✅ SENSORS: Active" if (datetime.now().timestamp() - mtime) < 30 else "❌ SENSORS: Stale")
        try:
            bt_check = subprocess.check_output(["bluetoothctl", "devices"], text=True)
            report.append("✅ BLUETOOTH: Bot paired" if "E1:6A:83:06:38:48" in bt_check else "⚠️ BLUETOOTH: Bot missing")
        except: report.append("❌ BLUETOOTH: Error")
        messagebox.showinfo("SYSTEM HEALTH REPORT", "\n".join(report))

    def get_connection_type(self):
        try:
            ips = subprocess.check_output("hostname -I", shell=True).decode().split()
            for ip in ips:
                if ip.startswith("100."): return "REMOTE (VPN)", "orange"
            return "LOCAL (WiFi)", "lightgreen"
        except: return "UNKNOWN", "gray"

    def update_threshold(self, val):
        self.cloud_threshold = float(val)
        try:
            with open(self.path_thresh, "w") as f: f.write(str(self.cloud_threshold))
        except: pass

    def create_placeholder(self, text, w, h):
        img = Image.new('RGB', (w, h), color=(15, 15, 15))
        draw = ImageDraw.Draw(img)
        draw.rectangle([0, 0, w-1, h-1], outline="red", width=3)
        draw.text((w//2, h//2), text, fill="white", anchor="mm", align="center")
        return ImageTk.PhotoImage(img)

    def load_scale(self, path, w, h, label):
        if not os.path.exists(path) or os.path.getsize(path) < 100:
            return self.create_placeholder(f"SET {label} ID\nIN DOSSIER", w, h)
        try:
            with Image.open(path) as raw:
                img = raw.convert("RGB")
                img.thumbnail((w, h), Image.Resampling.LANCZOS)
                return ImageTk.PhotoImage(img)
        except: return self.create_placeholder(f"ERROR LOADING\n{label}", w, h)

    def create_ui_elements(self):
        radar_center_x = self.sw * 0.53
        self.canvas.create_text(radar_center_x, 25, text="--- OBSERVATORY CONTROLS ---", fill="#FFCC00", font=("Arial", 12, "bold"))
        
        self.btn_open = tk.Button(self.root, text="OPEN ROOF", bg="#1E8449", fg="white", font=("Arial", 9, "bold"), command=self.manual_open)
        self.btn_open.place(x=radar_center_x - 180, y=50, width=100, height=40)

        self.btn_ai = tk.Button(self.root, text="AI CHECKING", bg="#6C3483", fg="white", font=("Arial", 8, "bold"), command=lambda: self.run_ai_clear_check(manual_click=True))
        self.btn_ai.place(x=radar_center_x - 65, y=50, width=130, height=40)

        self.btn_close = tk.Button(self.root, text="CLOSE ROOF", bg="#922B21", fg="white", font=("Arial", 9, "bold"), command=self.manual_close)
        self.btn_close.place(x=radar_center_x + 80, y=50, width=100, height=40)

        self.canvas.create_text(radar_center_x - 110, 110, text="BRIGHT:", fill="white", font=("Arial", 8, "bold"))
        self.ai_bright_slider = tk.Scale(self.root, from_=10, to=200, orient='horizontal', bg='black', fg='white', troughcolor='#333', length=80, highlightthickness=0, font=("Arial", 7), command=self.update_ai_bright)
        self.ai_bright_slider.set(self.ai_brightness_trigger)
        self.ai_bright_slider.place(x=radar_center_x - 85, y=95)

        self.canvas.create_text(radar_center_x + 35, 110, text="COLOR:", fill="white", font=("Arial", 8, "bold"))
        self.ai_color_slider = tk.Scale(self.root, from_=2, to=50, orient='horizontal', bg='black', fg='white', troughcolor='#333', length=80, highlightthickness=0, font=("Arial", 7), command=self.update_ai_color)
        self.ai_color_slider.set(self.ai_color_trigger)
        self.ai_color_slider.place(x=radar_center_x + 60, y=95)

        self.net_status_text = self.canvas.create_text(self.sw - 20, 20, text="NET: CHECKING...", font=("Arial", 10, "bold"), fill="cyan", anchor="ne")

        tk.Button(self.root, text="EXIT HUD", command=self.root.destroy, bg="#500", fg="white", font=("Arial", 9, "bold")).place(x=20, y=20, width=100)
        tk.Button(self.root, text="MAINT / DOSSIER", command=self.open_dossier, bg="#222", fg="white", font=("Arial", 9, "bold")).place(x=140, y=20, width=120)
        self.power_btn = tk.Button(self.root, text="⚡ SEESTAR", command=self.trigger_fingerbot, bg="#900", fg="white", font=("Arial", 9, "bold"))
        self.power_btn.place(x=280, y=20, width=100)
        self.btn_control = tk.Button(self.root, text="🔭 CONTROL", bg="#2874A6", fg="white", font=("Arial", 9, "bold"), command=self.open_browser)
        self.btn_control.place(x=400, y=20, width=100)
        self.btn_health = tk.Button(self.root, text="🩺 SYSTEM CHECK", bg="#5D6D7E", fg="white", font=("Arial", 9, "bold"), command=self.run_health_check)
        self.btn_health.place(x=520, y=20, width=130)

        box_w, box_h = int(self.sw * 0.25), int(self.sh * 0.85)
        rx, ry = self.sw - box_w - 20, 40
        self.canvas.create_rectangle(rx, ry, rx + box_w, ry + box_h, fill='#050505', outline='#00FFCC', width=3)
        
        y_off, spacing = ry + 45, box_h // 13.5
        self.val_sky   = self.add_sensor_line("🌡️", "SKY TEMP:", rx + 15, y_off, "#AAB7B8", box_w)
        self.val_cloud = self.add_sensor_line("☁️", "SKY COND:", rx + 15, y_off + spacing, "#5DADE2", box_w)
        
        self.slider = tk.Scale(self.root, from_=5, to=100, orient='horizontal', bg='#050505', fg='white', troughcolor='#500', activebackground='red', highlightthickness=0, font=("Arial", 8), command=self.update_threshold)
        self.slider.set(self.cloud_threshold)
        self.slider.place(x=rx + 55, y=y_off + spacing + 18, width=box_w - 80)

        y_mid = y_off + (spacing * 2.8)
        self.val_amb   = self.add_sensor_line("🌡️", "AMB TEMP:", rx + 15, y_mid, "#EC7063", box_w)
        self.val_hum   = self.add_sensor_line("💧", "HUMIDITY:", rx + 15, y_mid + spacing, "#5499C7", box_w)
        self.val_dew   = self.add_sensor_line("✨", "DEW POINT:", rx + 15, y_mid + spacing*2, "#A569BD", box_w)
        self.val_heat  = self.add_sensor_line("🔥", "DEW HEAT:", rx + 15, y_mid + spacing*3, "#FF5733", box_w)
        self.val_pres  = self.add_sensor_line("⏲️", "PRESSURE:", rx + 15, y_mid + spacing*4, "#58D68D", box_w)
        self.val_wind  = self.add_sensor_line("💨", "WIND SPD:", rx + 15, y_mid + spacing*5, "#F4D03F", box_w)
        self.val_rain  = self.add_sensor_line("☔", "RAIN DET:", rx + 15, y_mid + spacing*6, "#AF7AC5", box_w)
        self.val_dome  = self.add_sensor_line("🏠", "ROOF STAT:", rx + 15, y_mid + spacing*7, "#EB984E", box_w)
        
        y_bot = y_mid + spacing*9
        self.val_alpaca = self.add_sensor_line("🔭", "ALPACA LINK:", rx + 15, y_bot - spacing, "#00FF00", box_w)
        self.val_hrs   = self.add_sensor_line("⌛", "OP HOURS:", rx + 15, y_bot, "#FFCC00", box_w)
        self.sync_light = self.canvas.create_oval(rx + 15, y_bot - 8, rx + 31, y_bot + 8, fill="gray", outline="white")

        self.all_img_id = self.canvas.create_image(self.sw*0.22, self.sh*0.4, anchor='center', tags="zoom")
        self.rad_img_id = self.canvas.create_image(radar_center_x, self.sh*0.4, anchor='center', tags="zoom")
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
        if "latest.jpg" in path.lower():
            img.thumbnail((int(self.sw * 0.95), int(self.sh * 0.95)), Image.Resampling.LANCZOS)
        elif "radar" in path.lower() or "star_debug" in path.lower():
            new_h = int(self.sh * 0.88); ratio = new_h / float(img.size[1]);
            new_w = int(float(img.size[0]) * ratio)
            img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
        else:
            img.thumbnail((int(self.sw * 0.8), int(self.sh * 0.8)), Image.Resampling.LANCZOS)
        self.p_img = ImageTk.PhotoImage(img)
        tk.Button(pop, image=self.p_img, bg='black', bd=0, activebackground='black', command=pop.destroy).pack(expand=True)

    def open_dossier(self):
        d_win = tk.Toplevel(self.root)
        d_win.geometry(f"{int(self.sw * 0.45)}x{int(self.sh * 0.85)}")
        d_win.config(bg="#050505"); d_win.attributes("-topmost", True)
        d_win.grid_rowconfigure(2, weight=1); d_win.grid_columnconfigure(0, weight=1)
        tk.Label(d_win, text="SYSTEM DOSSIER", bg="#050505", fg="#FFCC00", font=("Arial", 18, "bold")).grid(row=0, column=0, pady=10)
        
        entry_frame = tk.Frame(d_win, bg="#050505")
        entry_frame.grid(row=1, column=0, sticky="ew", padx=20)
        
        def create_entry(label_text, path, color="cyan"):
            f = tk.Frame(entry_frame, bg="#111")
            f.pack(fill="x", pady=2)
            tk.Label(f, text=label_text, bg="#111", fg="white", width=15, anchor="w").pack(side="left")
            e = tk.Entry(f, bg="black", fg=color, insertbackground="white")
            e.pack(side="left", padx=10, fill="x", expand=True)
            if os.path.exists(path):
                with open(path, "r") as file: e.insert(0, file.read().strip())
            return e

        rad_entry = create_entry("Radar Station:", self.path_radar_id, "orange")
        csk_entry = create_entry("ClearSky ID:", self.path_csk_id, "#00FFCC")
        ip_entry  = create_entry("Seestar IP:", self.path_seestar_ip, "#FF33FF")
        bt_entry  = create_entry("Fingerbot MAC:", self.path_fingerbot_mac, "#FFCC00")
        mail_entry = create_entry("Alert Email:", self.path_email, "lightgreen")
        
        txt = scrolledtext.ScrolledText(d_win, bg="black", fg="#00FFCC", font=("Courier", 14), insertbackground="white")
        txt.grid(row=2, column=0, sticky="nsew", padx=20, pady=5)
        if os.path.exists(self.path_notes):
            with open(self.path_notes, "r") as f: txt.insert('1.0', f.read())

        def save_all():
            with open(self.path_radar_id, "w") as f: f.write(rad_entry.get().upper().strip())
            with open(self.path_csk_id, "w") as f: f.write(csk_entry.get().strip())
            with open(self.path_seestar_ip, "w") as f: f.write(ip_entry.get().strip())
            with open(self.path_fingerbot_mac, "w") as f: f.write(bt_entry.get().strip())
            with open(self.path_email, "w") as f: f.write(mail_entry.get().strip())
            with open(self.path_notes, 'w') as f: f.write(txt.get('1.0', 'end'))
            with open(self.path_star_thresh, 'w') as f: f.write(str(star_slider.get()))
            self.seestar_ip = ip_entry.get().strip()
            self.email_receiver = mail_entry.get().strip()
            self.star_threshold = star_slider.get()
            d_win.destroy()

        def reset_hrs():
            if messagebox.askyesno("RESET", "Reset Timer to 0?"):
                with open(self.path_hours, "w") as f: f.write("0.0")

        btn_f = tk.Frame(d_win, bg="#050505")
        btn_f.grid(row=3, column=0, sticky="ew", pady=(10, 20))
        tk.Button(btn_f, text="♻ RESET", bg="#D4AC0D", command=reset_hrs).pack(side="left", padx=10)
        tk.Button(btn_f, text="🔄 SYNC", bg="#4B0082", fg="white", command=lambda: subprocess.Popen(["python3", self.path_sync_script])).pack(side="left", padx=5)
        tk.Button(btn_f, text="🤖 TEST BOT", bg="orange", command=self.trigger_fingerbot).pack(side="left", padx=5)
        
        tk.Label(btn_f, text="STARS:", bg="#050505", fg="white", font=("Arial", 8)).pack(side="left", padx=(10, 2))
        star_slider = tk.Scale(btn_f, from_=5, to=100, orient='horizontal', bg='#050505', fg='white', troughcolor='#333', length=80, highlightthickness=0, font=("Arial", 7))
        star_slider.set(self.star_threshold)
        star_slider.pack(side="left", padx=5)
        
        tk.Button(btn_f, text="💾 SAVE", bg="#1E8449", fg="white", command=save_all).pack(side="right", padx=20)

    def check_cleaning_reminder(self):
        if os.path.exists(self.path_hours):
            try:
                with open(self.path_hours, "r") as f:
                    hrs = float(f.read().strip())
                    if hrs >= 1000.0: messagebox.showwarning("MAINTENANCE", f"Alert: {hrs:.1f} Hours. Clean dome.")
            except: pass

    def draw_stars(self):
        for _ in range(60):
            x, y = random.randint(0, self.sw), random.randint(0, self.sh)
            self.canvas.create_oval(x, y, x+1, y+1, fill='white', outline='white')

    def check_alpaca_status(self):
        if not self.seestar_ip or self.seestar_ip == "0.0.0.0": return False
        try:
            with socket.create_connection((self.seestar_ip, 32323), timeout=0.5): return True
        except: return False

    def update_loop(self):
        img_w, img_h = int(self.sw * 0.28), int(self.sh * 0.45)
        clk_w, clk_h = int(self.sw * 0.60), int(self.sh * 0.35)
        self.img_all = self.load_scale(self.path_allsky, img_w, img_h, "AllSky")
        self.canvas.itemconfig(self.all_img_id, image=self.img_all)
        self.img_rad = self.load_scale(self.path_radar, img_w, img_h, "Radar")
        self.canvas.itemconfig(self.rad_img_id, image=self.img_rad)
        self.img_clk = self.load_scale(self.path_clock, clk_w, clk_h, "ClearSky")
        self.canvas.itemconfig(self.clk_img_id, image=self.img_clk)
        
        if os.path.exists(self.path_allsky):
            ts = os.path.getmtime(self.path_allsky)
            if ts != self.last_allsky_ts:
                self.last_allsky_ts = ts
                self.run_ai_clear_check()

        net_stat, net_col = self.get_connection_type()
        self.canvas.itemconfig(self.net_status_text, text=f"NET: {net_stat}", fill=net_col)
        alpaca_on = self.check_alpaca_status()
        self.canvas.itemconfig(self.val_alpaca, text="ONLINE" if alpaca_on else "OFFLINE", fill="#00FF00" if alpaca_on else "#FF3333")

        if os.path.exists(self.path_hours):
            try:
                mtime = os.path.getmtime(self.path_hours)
                diff = (datetime.now().timestamp() - mtime) / 60
                self.canvas.itemconfig(self.sync_light, fill="#00FF00" if diff < 20 else "#FF0000")
                with open(self.path_hours, "r") as f:
                    num_hrs = float(f.read().strip())
                    hrs_col = "red" if num_hrs >= 1000.0 else "#FFCC00"
                    self.canvas.itemconfig(self.val_hrs, text=f"{num_hrs:.1f} HRS", fill=hrs_col)
            except: pass

        if os.path.exists(self.path_sensors):
            try:
                sky_t, amb_t, hum_val, wind_val, is_wet = None, None, None, None, False
                sensor_report = ""
                with open(self.path_sensors, "r") as f:
                    for line in f:
                        u_line = line.upper().strip(); val = line.split(":", 1)[1].strip() if ":" in u_line else ""
                        sensor_report += f"{line.strip()}\n"
                        if "SKY TEMP" in u_line:
                            self.canvas.itemconfig(self.val_sky, text=val)
                            try: sky_t = float(''.join(c for c in val if c in '0123456789.-'))
                            except: pass
                        elif "AMB TEMP" in u_line:
                            self.canvas.itemconfig(self.val_amb, text=val)
                            try: amb_t = float(''.join(c for c in val if c in '0123456789.-'))
                            except: pass
                        elif "HUMIDITY" in u_line:
                            try:
                                clean_val = val.split('%')[0].strip()
                                hum_val = float(''.join(c for c in clean_val if c in '0123456789.-'))
                                self.canvas.itemconfig(self.val_hum, text=f"{hum_val}%")
                            except: pass
                        elif "WIND" in u_line:
                            try:
                                wind_val = float(''.join(c for c in val if c in '0123456789.-'))
                                self.canvas.itemconfig(self.val_wind, text=f"{wind_val} mph")
                            except: pass
                        elif "RAIN" in u_line or "PRECIP" in u_line:
                            is_wet = "WET" in val.upper()
                            self.canvas.itemconfig(self.val_rain, text="WET" if is_wet else "DRY", fill="red" if is_wet else "cyan")
                        elif "PRESSURE" in u_line:
                            try:
                                raw_p = float(''.join(c for c in val if c in '0123456789.-'))
                                self.canvas.itemconfig(self.val_pres, text=f"{raw_p * 0.02953:.2f} in")
                            except: pass
                        elif "HEATER" in u_line:
                            h_on = "ON" in val.upper()
                            self.canvas.itemconfig(self.val_heat, text=val, fill="#FF5733" if h_on else "cyan")

                delta = (amb_t - sky_t) if (amb_t and sky_t) else 0
                is_clear = delta > self.cloud_threshold
                self.canvas.itemconfig(self.val_cloud, text="CLEAR" if is_clear else "CLOUDY", fill="lightgreen" if is_clear else "orange")
                
                dew_f = 0
                if amb_t and hum_val:
                    T = (amb_t - 32) * 5/9;
                    gamma = (math.log(hum_val/100) + ((17.27 * T) / (237.3 + T)))
                    dew_f = ((237.3 * gamma) / (17.27 - gamma) * 9/5) + 32
                    self.canvas.itemconfig(self.val_dew, text=f"{dew_f:.1f} F")
                
                extreme_dew = (amb_t - dew_f) < 3 if (amb_t and dew_f) else False
                wind_safe = (wind_val < 15) if (wind_val is not None) else False
                
                if is_clear and not is_wet and wind_safe and not extreme_dew:
                    roof_text, roof_color = "SAFE TO OPEN", "lightgreen"
                else:
                    reasons = []
                    if is_wet: reasons.append("RAIN")
                    if not is_clear: reasons.append("CLOUDY")
                    if wind_val and wind_val >= 15: reasons.append("WIND")
                    if extreme_dew: reasons.append("DEW")
                    roof_text, roof_color = (f"UNSAFE: {', '.join(reasons)}" if reasons else "UNSAFE"), "red"

                self.canvas.itemconfig(self.val_dome, text=roof_text, fill=roof_color)

                now = datetime.now()
                if now.hour == 18 and now.minute == 0:
                    if self.dusk_sent_today != now.day:
                        self.send_email_notification("Dusk Sensor Snapshot", f"Observatory status at 18:00:\n\n{sensor_report}")
                        self.dusk_sent_today = now.day

                if is_wet or (wind_val and wind_val > 20):
                    with open(self.path_roof_cmd, "w") as f: f.write("CLOSE")
                    if self.last_roof_safety_state == "SAFE TO OPEN" and not self.emergency_sent:
                        reason = "RAIN" if is_wet else f"HIGH WIND ({wind_val} mph)"
                        self.send_email_notification("EMERGENCY ROOF CLOSE", f"The roof was forced CLOSED due to detected {reason}.\n\n{sensor_report}")
                        self.emergency_sent = True
                else:
                    self.emergency_sent = False

                self.last_roof_safety_state = roof_text
            except: pass

        self.root.after(1000, self.update_loop)

if __name__ == "__main__":
    root = tk.Tk(); app = SumnerHUD(root); root.mainloop()