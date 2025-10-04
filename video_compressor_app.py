# -*- coding: utf-8 -*-
# Nama File: video_compressor_app.py
# Versi: 0.1.2 (Beta)
# Author: Verxina

import tkinter
import tkinter.filedialog as filedialog
import customtkinter as ctk
import subprocess
import threading
import json
import re
import os
import sys
import time

# --- Konfigurasi Dasar ---
APP_VERSION = "0.1.2"
APP_CHANNEL = "Beta"
CONFIG_FILE = "fastcompress_config.json"

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class VideoCompressorApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # --- Konfigurasi Window ---
        self.title(f"FastCompress {APP_CHANNEL} v{APP_VERSION}")
        self.geometry("820x820")
        # Izinkan resize dan tetapkan ukuran minimum
        self.minsize(820, 600)
        self.resizable(True, True)

        # --- Variabel Internal ---
        self.input_path = ""
        self.output_path = ""
        self.available_hw_encoders = {}
        self.is_compressing = False
        self.cancel_requested = False
        self.current_process = None
        self.canceled = False
        self.audio_bitrate_k = 128  # default saat re-encode

        # --- Inisialisasi UI ---
        self.create_widgets()
        self.load_config()
        self.check_ffmpeg()

    def check_ffmpeg(self):
        """Memeriksa apakah ffmpeg dan ffprobe ada di PATH."""
        try:
            subprocess.run(["ffmpeg", "-version"], check=True, capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
            self.log("ffmpeg ditemukan.")
            self.detect_hw_encoders()
        except (subprocess.CalledProcessError, FileNotFoundError):
            self.log("ERROR: ffmpeg tidak ditemukan. Pastikan ffmpeg terinstall dan ada di PATH sistem Anda.")
            self.log("Unduh: https://ffmpeg.org/download.html")
            self.compress_button.configure(state="disabled")

    def create_widgets(self):
        """Membuat semua elemen UI."""
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(pady=15, padx=15, fill="both", expand=True)

        # --- 1. Frame File ---
        file_frame = ctk.CTkFrame(main_frame)
        file_frame.pack(pady=10, padx=10, fill="x")

        self.input_label = ctk.CTkLabel(file_frame, text="File Video Input: (Belum dipilih)", anchor="w")
        self.input_label.pack(pady=5, padx=10, fill="x")
        self.browse_button = ctk.CTkButton(file_frame, text="Pilih Video", command=self.browse_file)
        self.browse_button.pack(pady=5, padx=10, side="left")

        self.output_label = ctk.CTkLabel(file_frame, text="File Video Output: (Otomatis)", anchor="w")
        self.output_label.pack(pady=5, padx=10, fill="x")

        # --- 2. Frame Opsi Kompresi ---
        options_frame = ctk.CTkFrame(main_frame)
        options_frame.pack(pady=10, padx=10, fill="x")
        options_frame.grid_columnconfigure((0, 1), weight=1)

        ctk.CTkLabel(options_frame, text="Codec:").grid(row=0, column=0, padx=10, pady=5, sticky="w")
        self.codec_var = ctk.StringVar(value="H.264")
        self.codec_menu = ctk.CTkOptionMenu(options_frame, variable=self.codec_var, values=["H.264", "H.265", "AV1"], command=self.on_codec_change)
        self.codec_menu.grid(row=0, column=1, padx=10, pady=5, sticky="ew")

        ctk.CTkLabel(options_frame, text="Tipe Encoder:").grid(row=1, column=0, padx=10, pady=5, sticky="w")
        self.encoder_type_var = ctk.StringVar(value="Software")
        self.encoder_type_menu = ctk.CTkOptionMenu(options_frame, variable=self.encoder_type_var, values=["Software"], command=lambda _=None: self.save_config())
        self.encoder_type_menu.grid(row=1, column=1, padx=10, pady=5, sticky="ew")

        ctk.CTkLabel(options_frame, text="Target Ukuran (MB):").grid(row=2, column=0, padx=10, pady=5, sticky="w")
        self.target_mb_entry = ctk.CTkEntry(options_frame, placeholder_text="Contoh: 50")
        self.target_mb_entry.grid(row=2, column=1, padx=10, pady=5, sticky="ew")

        ctk.CTkLabel(options_frame, text="Algoritma:").grid(row=3, column=0, padx=10, pady=5, sticky="w")
        self.algorithm_var = ctk.StringVar(value="Standard")
        self.algorithm_menu = ctk.CTkOptionMenu(options_frame, variable=self.algorithm_var, values=["Standard", "AI (Efisien)"], command=lambda _=None: self.save_config())
        self.algorithm_menu.grid(row=3, column=1, padx=10, pady=5, sticky="ew")

        ctk.CTkLabel(options_frame, text="Audio Mode:").grid(row=4, column=0, padx=10, pady=5, sticky="w")
        self.audio_mode_var = ctk.StringVar(value="Re-encode (AAC 128k)")
        self.audio_mode_menu = ctk.CTkOptionMenu(options_frame, variable=self.audio_mode_var,
                                                 values=["Re-encode (AAC 128k)", "Copy"], command=lambda _=None: self.save_config())
        self.audio_mode_menu.grid(row=4, column=1, padx=10, pady=5, sticky="ew")

        self.hw_detect_label = ctk.CTkLabel(options_frame, text="Hardware: (menunggu deteksi)", text_color="orange", anchor="w")
        self.hw_detect_label.grid(row=5, column=0, columnspan=2, padx=10, pady=(8, 4), sticky="w")

        # --- 3. Frame Aksi & Status ---
        action_frame = ctk.CTkFrame(main_frame)
        action_frame.pack(pady=10, padx=10, fill="x")

        btn_frame = ctk.CTkFrame(action_frame)
        btn_frame.pack(pady=5, padx=5, fill="x")

        self.compress_button = ctk.CTkButton(btn_frame, text="Mulai Kompresi", command=self.start_compression_thread)
        self.compress_button.pack(pady=5, padx=5, side="left", expand=True, fill="x")

        self.cancel_button = ctk.CTkButton(btn_frame, text="Batal", command=self.cancel_compression, fg_color="#aa3333", hover_color="#992222", state="disabled")
        self.cancel_button.pack(pady=5, padx=5, side="left")

        self.clear_log_button = ctk.CTkButton(btn_frame, text="Clear Log", command=self.clear_log, fg_color="#444444", hover_color="#555555")
        self.clear_log_button.pack(pady=5, padx=5, side="left")

        self.status_label = ctk.CTkLabel(action_frame, text="Status: Menunggu", text_color="yellow")
        self.status_label.pack(pady=5, padx=10)

        self.progress_bar = ctk.CTkProgressBar(action_frame)
        self.progress_bar.set(0)
        self.progress_bar.pack(pady=5, padx=10, fill="x")

        # --- 4. Frame Log ---
        log_frame = ctk.CTkFrame(main_frame)
        log_frame.pack(pady=10, padx=10, fill="both", expand=True)
        ctk.CTkLabel(log_frame, text="Log Proses:").pack(anchor="w", padx=10)
        # Hapus height agar mengikuti resize jendela
        self.log_textbox = ctk.CTkTextbox(log_frame, state="disabled")
        self.log_textbox.pack(pady=10, padx=10, fill="both", expand=True)

    def log(self, message):
        self.log_textbox.configure(state="normal")
        self.log_textbox.insert("end", f"{message}\n")
        self.log_textbox.configure(state="disabled")
        self.log_textbox.see("end")

    def clear_log(self):
        self.log_textbox.configure(state="normal")
        self.log_textbox.delete("1.0", "end")
        self.log_textbox.configure(state="disabled")

    def browse_file(self):
        filepath = filedialog.askopenfilename(
            title="Pilih File Video",
            filetypes=(("Video Files", "*.mp4 *.mkv *.avi *.mov *.webm"), ("All files", "*.*"))
        )
        if filepath:
            self.input_path = filepath
            self.input_label.configure(text=f"File Video Input: {os.path.basename(filepath)}")
            path, filename = os.path.split(filepath)
            name, _ = os.path.splitext(filename)
            self.output_path = os.path.join(path, f"{name}_compressed.mp4")
            self.output_label.configure(text=f"File Video Output: {os.path.basename(self.output_path)}")
            self.log(f"Input: {self.input_path}")
            self.log(f"Output: {self.output_path}")
            self.save_config()

    def detect_hw_encoders(self):
        self.log("Mendeteksi perangkat keras (uji inisialisasi encoder)...")
        null_device = 'NUL' if sys.platform == 'win32' else '/dev/null'

        def test_encoder_available(encoder_name):
            cmd = [
                "ffmpeg", "-hide_banner", "-v", "error",
                "-f", "lavfi", "-i", "color=c=black:s=128x72:r=30:d=1",
                "-an", "-sn",
                "-c:v", encoder_name,
                "-b:v", "300k",
                "-t", "1",
                "-f", "mp4", null_device
            ]
            try:
                res = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=8,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
                if res.returncode == 0:
                    return True, ""
                err = (res.stderr or res.stdout or "").strip().splitlines()
                reason = err[-1] if err else "exit code != 0"
                return False, reason
            except Exception as e:
                return False, str(e)

        encoders_to_find = {
            "H.264": {"NVIDIA": "h264_nvenc", "AMD": "h264_amf", "Intel": "h264_qsv"},
            "H.265": {"NVIDIA": "hevc_nvenc", "AMD": "hevc_amf", "Intel": "hevc_qsv"},
            "AV1": {"NVIDIA": "av1_nvenc", "AMD": "av1_amf", "Intel": "av1_qsv"}
        }
        self.available_hw_encoders = {"H.264": [], "H.265": [], "AV1": []}

        for codec, brands in encoders_to_find.items():
            for brand, enc_name in brands.items():
                ok, reason = test_encoder_available(enc_name)
                if ok:
                    self.available_hw_encoders[codec].append(brand)
                    self.log(f"OK: {brand} untuk {codec} tersedia ({enc_name})")
                else:
                    self.log(f"Skip: {brand} {codec} tidak tersedia -> {reason}")

        if not any(self.available_hw_encoders.values()):
            self.log("INFO: Tidak ada akselerasi hardware terdeteksi.")
            self.hw_detect_label.configure(text="Hardware: None", text_color="orange")
        else:
            brands = set()
            for lst in self.available_hw_encoders.values():
                brands.update(lst)
            txt = "Hardware: " + ", ".join(sorted(brands))
            self.hw_detect_label.configure(text=txt, text_color="light green")

        self.update_encoder_options()

    def update_encoder_options(self):
        selected_codec = self.codec_var.get()
        options = ["Software"]
        if self.available_hw_encoders.get(selected_codec):
            options.extend(self.available_hw_encoders[selected_codec])
        self.encoder_type_menu.configure(values=options)
        if self.encoder_type_var.get() not in options:
            self.encoder_type_var.set("Software")
        self.save_config()

    def on_codec_change(self, *_):
        self.update_encoder_options()

    def get_video_duration(self, filepath):
        self.log("Mendapatkan durasi video...")
        command = [
            "ffprobe",
            "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            filepath
        ]
        try:
            result = subprocess.run(command, capture_output=True, text=True, check=True, creationflags=subprocess.CREATE_NO_WINDOW)
            duration = float(result.stdout.strip())
            self.log(f"Durasi video: {duration:.2f} detik")
            return duration
        except Exception as e:
            self.log(f"ERROR: Gagal mendapatkan durasi video: {e}")
            return None

    def get_source_audio_bitrate(self):
        """Ambil bitrate audio (k) jika ada; fallback 128k."""
        if not self.input_path:
            return 128
        cmd = [
            "ffprobe", "-v", "error",
            "-select_streams", "a:0",
            "-show_entries", "stream=bit_rate",
            "-of", "default=noprint_wrappers=1:nokey=1",
            self.input_path
        ]
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=5, creationflags=subprocess.CREATE_NO_WINDOW)
            val = res.stdout.strip()
            if val.isdigit():
                return max(32, int(int(val) / 1000))
        except Exception:
            pass
        return 128

    def start_compression_thread(self):
        if self.is_compressing:
            self.log("Kompresi sedang berjalan.")
            return
        if not self.input_path:
            self.log("ERROR: Silakan pilih file video terlebih dahulu.")
            return
        try:
            target_mb = float(self.target_mb_entry.get())
            if target_mb <= 0:
                raise ValueError
        except ValueError:
            self.log("ERROR: Target ukuran MB harus angka positif.")
            return

        # Validasi target tidak lebih besar dari ukuran sumber
        try:
            src_size_mb = os.path.getsize(self.input_path) / (1024 * 1024)
            if target_mb >= src_size_mb:
                self.log(f"PERINGATAN: Target ({target_mb:.2f} MB) >= ukuran sumber ({src_size_mb:.2f} MB). Kompresi dibatalkan.")
                return
        except OSError:
            pass

        self.is_compressing = True
        self.cancel_requested = False
        self.canceled = False
        self.compress_button.configure(state="disabled", text="Sedang Mengompres...")
        self.cancel_button.configure(state="normal")
        self.status_label.configure(text="Status: Memulai...", text_color="cyan")
        self.progress_bar.set(0)

        for f in ("ffmpeg2pass-0.log", "ffmpeg2pass-0.log.mbtree"):
            if os.path.exists(f):
                try: os.remove(f)
                except OSError: pass

        self.save_config()
        thread = threading.Thread(target=self.run_compression, args=(target_mb,))
        thread.daemon = True
        thread.start()

    def run_compression(self, target_mb):
        duration = self.get_video_duration(self.input_path)
        if duration is None:
            self.cleanup_after_failure("Gagal mendapatkan durasi video.")
            return

        total_bits_target = target_mb * 8 * 1024 * 1024

        audio_mode = self.audio_mode_var.get()
        if "Copy" in audio_mode:
            src_audio_k = self.get_source_audio_bitrate()
            audio_bitrate_k = src_audio_k
            self.log(f"Audio mode: COPY (estimasi {audio_bitrate_k}k)")
        else:
            audio_bitrate_k = self.audio_bitrate_k
            self.log(f"Audio mode: Re-encode AAC {audio_bitrate_k}k")

        audio_bits_total = audio_bitrate_k * 1000 * duration
        video_bits_available = total_bits_target - audio_bits_total
        if video_bits_available <= 200000:
            self.cleanup_after_failure("Target terlalu kecil setelah alokasi audio.")
            return

        target_video_bitrate_k = int(video_bits_available / duration / 1000)
        self.log(f"Target video bitrate (disesuaikan): {target_video_bitrate_k}k")

        codec = self.codec_var.get()
        encoder_type = self.encoder_type_var.get()
        algorithm = self.algorithm_var.get()

        encoder_map = {
            "H.264": {"Software": "libx264", "NVIDIA": "h264_nvenc", "AMD": "h264_amf", "Intel": "h264_qsv"},
            "H.265": {"Software": "libx265", "NVIDIA": "hevc_nvenc", "AMD": "hevc_amf", "Intel": "hevc_qsv"},
            "AV1": {"Software": "libaom-av1", "NVIDIA": "av1_nvenc", "AMD": "av1_amf", "Intel": "av1_qsv"}
        }

        if codec == "AV1" and encoder_type == "Software":
            self.cleanup_after_failure("AV1 Software terlalu lambat untuk mode ini.")
            return

        ffmpeg_encoder = encoder_map[codec][encoder_type]
        self.log(f"Menggunakan encoder: {ffmpeg_encoder}")

        null_device = 'NUL' if sys.platform == 'win32' else '/dev/null'
        preset = "slow" if algorithm == "AI (Efisien)" else "medium"

        pass1_cmd = [
            "ffmpeg", "-y", "-i", self.input_path,
            "-c:v", ffmpeg_encoder,
            "-b:v", f"{target_video_bitrate_k}k",
            "-pass", "1",
            "-preset", preset,
            "-an",
            "-f", "mp4", null_device
        ]
        if ffmpeg_encoder == "libaom-av1":
            pass1_cmd.extend(["-cpu-used", "4"])

        self.status_label.configure(text="Status: Pass 1 dari 2...", text_color="cyan")
        self.log("\n--- MEMULAI PASS 1 ---")
        ok1 = self.execute_ffmpeg_command(pass1_cmd, duration)
        if not ok1:
            if self.canceled:
                self.compression_finished(False, "Dibatalkan.")
            else:
                self.cleanup_pass_logs()
                self.compression_finished(False, "Gagal pada Pass 1.")
            return

        pass2_cmd = [
            "ffmpeg", "-y", "-i", self.input_path,
            "-c:v", ffmpeg_encoder,
            "-b:v", f"{target_video_bitrate_k}k",
            "-pass", "2",
            "-preset", preset
        ]
        if "Copy" in audio_mode:
            pass2_cmd.extend(["-c:a", "copy"])
        else:
            pass2_cmd.extend(["-c:a", "aac", "-b:a", f"{audio_bitrate_k}k"])

        pass2_cmd.append(self.output_path)
        if ffmpeg_encoder == "libaom-av1":
            pass2_cmd.extend(["-cpu-used", "1"])

        self.status_label.configure(text="Status: Pass 2 dari 2...", text_color="cyan")
        self.log("\n--- MEMULAI PASS 2 ---")
        ok2 = self.execute_ffmpeg_command(pass2_cmd, duration)
        if not ok2:
            if self.canceled:
                self.compression_finished(False, "Dibatalkan.")
            else:
                self.compression_finished(False, "Gagal pada Pass 2.")
            return

        self.compression_finished(True, "Kompresi Selesai!")

    def execute_ffmpeg_command(self, command, duration):
        time_pattern = re.compile(r"time=(\d{2}):(\d{2}):(\d{2})\.(\d{2})")
        frame_pattern = re.compile(r"frame=\s*(\d+)")
        speed_pattern = re.compile(r"speed=\s*([\d\.]+)x")

        try:
            self.current_process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding='utf-8',
                errors='replace',
                creationflags=subprocess.CREATE_NO_WINDOW
            )
        except Exception as e:
            self.log(f"ERROR: Tidak bisa menjalankan ffmpeg: {e}")
            return False

        if self.current_process.stdout is None:
            self.log("ERROR: stdout is None, process may not have started correctly.")
            return False
        stdout = self.current_process.stdout
        last_update = 0
        while True:
            if self.cancel_requested:
                try:
                    self.current_process.terminate()
                except Exception:
                    pass
                self.canceled = True
                return False

            line = stdout.readline()
            if not line:
                if self.current_process.poll() is not None:
                    break
                else:
                    time.sleep(0.05)
                    continue

            line_stripped = line.strip()
            if line_stripped:
                self.log(line_stripped)

            match_time = time_pattern.search(line)
            match_frame = frame_pattern.search(line)
            match_speed = speed_pattern.search(line)

            current_time = None
            if match_time:
                h, m, s, ms = map(int, match_time.groups())
                current_time = h * 3600 + m * 60 + s + ms / 100

            if current_time is not None and duration > 0:
                progress = min(1.0, current_time / duration)
                now = time.time()
                if now - last_update > 0.05:
                    self.progress_bar.set(progress)
                    last_update = now
                speed_txt = ""
                if match_speed:
                    speed_val = match_speed.group(1)
                    speed_txt = f" speed={speed_val}x"
                percent = int(progress * 100)
                self.status_label.configure(text=f"Status: Proses... {percent}%{speed_txt}", text_color="cyan")

        ret = self.current_process.wait()
        self.current_process = None
        return ret == 0

    def cancel_compression(self):
        if not self.is_compressing:
            return
        self.cancel_requested = True
        self.status_label.configure(text="Status: Membatalkan...", text_color="orange")
        self.log("Permintaan pembatalan dikirim...")

    def cleanup_after_failure(self, msg):
        self.compression_finished(False, msg)

    def cleanup_pass_logs(self):
        for f in ("ffmpeg2pass-0.log", "ffmpeg2pass-0.log.mbtree"):
            if os.path.exists(f):
                try: os.remove(f)
                except OSError: pass

    def compression_finished(self, success, message):
        self.is_compressing = False
        self.compress_button.configure(state="normal", text="Mulai Kompresi")
        self.cancel_button.configure(state="disabled")
        if success:
            self.status_label.configure(text=f"Status: {message}", text_color="light green")
            self.progress_bar.set(1)
            self.log(f"\nSUKSES: File disimpan di {self.output_path}")
        else:
            if self.canceled:
                self.status_label.configure(text=f"Status: {message}", text_color="orange")
                self.log("\nDIBATALKAN oleh pengguna.")
            else:
                self.status_label.configure(text=f"Status: {message}", text_color="red")
                self.log(f"\nGAGAL: {message}")
            if not success:
                self.progress_bar.set(0)
        self.cleanup_pass_logs()

    # --- Konfigurasi (Simpan / Muat) ---
    def save_config(self):
        data = {
            "codec": self.codec_var.get(),
            "encoder_type": self.encoder_type_var.get(),
            "algorithm": self.algorithm_var.get(),
            "audio_mode": self.audio_mode_var.get(),
            "target_mb": self.target_mb_entry.get()
        }
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception:
            pass

    def load_config(self):
        if not os.path.exists(CONFIG_FILE):
            return
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            if "codec" in data:
                self.codec_var.set(data["codec"])
            if "encoder_type" in data:
                self.encoder_type_var.set(data["encoder_type"])
            if "algorithm" in data:
                self.algorithm_var.set(data["algorithm"])
            if "audio_mode" in data:
                self.audio_mode_var.set(data["audio_mode"])
            if "target_mb" in data:
                self.target_mb_entry.delete(0, "end")
                self.target_mb_entry.insert(0, data["target_mb"])
        except Exception:
            pass

if __name__ == "__main__":
    try:
        import customtkinter  # noqa
    except ImportError:
        print("CustomTkinter belum terinstall. Menginstall sekarang...")
        subprocess.run([sys.executable, "-m", "pip", "install", "customtkinter"], check=True)
        print("Instalasi selesai. Jalankan ulang.")
        sys.exit(0)

    app = VideoCompressorApp()
    app.mainloop()
