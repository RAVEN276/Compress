# -*- coding: utf-8 -*-
# Nama File: video_compressor_app.py
# Deskripsi: Aplikasi GUI untuk kompresi video dengan target ukuran file.
# Versi: 0.1.0 (Beta)
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

# --- Konfigurasi Dasar ---
APP_VERSION = "0.1.0"
APP_CHANNEL = "Beta"
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class VideoCompressorApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # --- Konfigurasi Window ---
        self.title(f"Video Compressor {APP_CHANNEL} v{APP_VERSION}")
        self.geometry("800x750")
        self.resizable(False, False)

        # --- Variabel Internal ---
        self.input_path = ""
        self.output_path = ""
        self.available_hw_encoders = {}
        self.is_compressing = False

        # --- Inisialisasi UI ---
        self.create_widgets()
        self.check_ffmpeg()

    def check_ffmpeg(self):
        """Memeriksa apakah ffmpeg dan ffprobe ada di PATH."""
        try:
            # Jalankan perintah 'ffmpeg -version' dan sembunyikan output
            subprocess.run(["ffmpeg", "-version"], check=True, capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
            self.log("ffmpeg ditemukan.")
            # Jika ffmpeg ada, deteksi hardware encoders
            self.detect_hw_encoders()
        except (subprocess.CalledProcessError, FileNotFoundError):
            self.log("ERROR: ffmpeg tidak ditemukan. Pastikan ffmpeg terinstall dan ada di PATH sistem Anda.")
            self.log("Anda bisa mengunduhnya dari: https://ffmpeg.org/download.html")
            self.compress_button.configure(state="disabled")


    def create_widgets(self):
        """Membuat semua elemen UI."""
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(pady=20, padx=20, fill="both", expand=True)

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
        self.codec_menu = ctk.CTkOptionMenu(options_frame, variable=self.codec_var, values=["H.264", "H.265", "AV1"], command=self.update_encoder_options)
        self.codec_menu.grid(row=0, column=1, padx=10, pady=5, sticky="ew")

        ctk.CTkLabel(options_frame, text="Tipe Encoder:").grid(row=1, column=0, padx=10, pady=5, sticky="w")
        self.encoder_type_var = ctk.StringVar(value="Software")
        self.encoder_type_menu = ctk.CTkOptionMenu(options_frame, variable=self.encoder_type_var, values=["Software"])
        self.encoder_type_menu.grid(row=1, column=1, padx=10, pady=5, sticky="ew")

        ctk.CTkLabel(options_frame, text="Target Ukuran (MB):").grid(row=2, column=0, padx=10, pady=5, sticky="w")
        self.target_mb_entry = ctk.CTkEntry(options_frame, placeholder_text="Contoh: 50")
        self.target_mb_entry.grid(row=2, column=1, padx=10, pady=5, sticky="ew")
        
        ctk.CTkLabel(options_frame, text="Algoritma:").grid(row=3, column=0, padx=10, pady=5, sticky="w")
        self.algorithm_var = ctk.StringVar(value="Standard")
        self.algorithm_menu = ctk.CTkOptionMenu(options_frame, variable=self.algorithm_var, values=["Standard", "AI (Efisien)"])
        self.algorithm_menu.grid(row=3, column=1, padx=10, pady=5, sticky="ew")


        # --- 3. Frame Aksi & Status ---
        action_frame = ctk.CTkFrame(main_frame)
        action_frame.pack(pady=10, padx=10, fill="x")

        self.compress_button = ctk.CTkButton(action_frame, text="Mulai Kompresi", command=self.start_compression_thread)
        self.compress_button.pack(pady=10, padx=10, fill="x")

        self.status_label = ctk.CTkLabel(action_frame, text="Status: Menunggu", text_color="yellow")
        self.status_label.pack(pady=5, padx=10)

        self.progress_bar = ctk.CTkProgressBar(action_frame)
        self.progress_bar.set(0)
        self.progress_bar.pack(pady=5, padx=10, fill="x")

        # --- 4. Frame Log ---
        log_frame = ctk.CTkFrame(main_frame)
        log_frame.pack(pady=10, padx=10, fill="both", expand=True)
        
        ctk.CTkLabel(log_frame, text="Log Proses:").pack(anchor="w", padx=10)
        self.log_textbox = ctk.CTkTextbox(log_frame, state="disabled", height=200)
        self.log_textbox.pack(pady=10, padx=10, fill="both", expand=True)

    def log(self, message):
        """Menambahkan pesan ke textbox log."""
        self.log_textbox.configure(state="normal")
        self.log_textbox.insert("end", message + "\n")
        self.log_textbox.configure(state="disabled")
        self.log_textbox.see("end")

    def browse_file(self):
        """Membuka dialog untuk memilih file video."""
        filepath = filedialog.askopenfilename(
            title="Pilih File Video",
            filetypes=(("Video Files", "*.mp4 *.mkv *.avi *.mov"), ("All files", "*.*"))
        )
        if filepath:
            self.input_path = filepath
            self.input_label.configure(text=f"File Video Input: {os.path.basename(filepath)}")
            
            # Generate output path
            path, filename = os.path.split(filepath)
            name, ext = os.path.splitext(filename)
            self.output_path = os.path.join(path, f"{name}_compressed.mp4") # Selalu output .mp4
            self.output_label.configure(text=f"File Video Output: {os.path.basename(self.output_path)}")
            self.log(f"Input: {self.input_path}")
            self.log(f"Output: {self.output_path}")

    def detect_hw_encoders(self):
        """Deteksi encoder hardware aktual di mesin pengguna dengan mencoba inisialisasi encoder.

        Hanya encoder yang benar-benar bisa diinisialisasi (GPU+driver tersedia) yang akan ditampilkan.
        """
        self.log("Mendeteksi perangkat keras (uji inisialisasi encoder)...")

        # Helper: uji apakah encoder bisa dipakai dengan encode video dummy 1 detik ke null device
        null_device = 'NUL' if sys.platform == 'win32' else '/dev/null'

        def test_encoder_available(encoder_name):
            """Kembalikan (True, '') jika encoder bisa dipakai, jika tidak (False, reason)."""
            cmd = [
                "ffmpeg", "-hide_banner", "-v", "error",
                "-f", "lavfi", "-i", "color=c=black:s=128x72:r=30:d=1",
                "-an", "-sn",
                "-c:v", encoder_name,
                "-b:v", "500k",
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
                # Ambil 1 baris error teratas untuk info singkat
                err = (res.stderr or res.stdout or "").strip().splitlines()
                reason = err[-1] if err else "ffmpeg exit code != 0"
                return False, reason
            except FileNotFoundError:
                return False, "ffmpeg tidak ditemukan"
            except subprocess.TimeoutExpired:
                return False, "timeout saat uji encoder"
            except Exception as e:
                return False, str(e)

        # Peta encoder hardware per codec
        encoders_to_find = {
            "H.264": {"NVIDIA": "h264_nvenc", "AMD": "h264_amf", "Intel": "h264_qsv"},
            "H.265": {"NVIDIA": "hevc_nvenc", "AMD": "hevc_amf", "Intel": "hevc_qsv"},
            "AV1": {"NVIDIA": "av1_nvenc", "AMD": "av1_amf", "Intel": "av1_qsv"}
        }

        self.available_hw_encoders = {"H.264": [], "H.265": [], "AV1": []}

        # Coba inisialisasi setiap encoder; hanya masukkan brand yang lolos uji
        for codec, brands in encoders_to_find.items():
            for brand, enc_name in brands.items():
                ok, reason = test_encoder_available(enc_name)
                if ok:
                    self.available_hw_encoders[codec].append(brand)
                    self.log(f"OK: {brand} untuk {codec} tersedia ({enc_name})")
                else:
                    # Ringkas pesan error agar tidak membanjiri log
                    self.log(f"Skip: {brand} {codec} tidak tersedia -> {reason}")

        # Jika tidak ada satu pun hardware yang terdeteksi, beri info
        if not any(self.available_hw_encoders.values()):
            self.log("INFO: Tidak ada akselerasi hardware yang terdeteksi; hanya 'Software' yang akan tersedia.")

        # Refresh opsi encoder sesuai codec yang aktif
        self.update_encoder_options()

    def update_encoder_options(self, *args):
        """Update pilihan encoder berdasarkan codec yang dipilih."""
        selected_codec = self.codec_var.get()
        options = ["Software"]
        if self.available_hw_encoders.get(selected_codec):
            options.extend(self.available_hw_encoders[selected_codec])
        
        self.encoder_type_menu.configure(values=options)
        # Jika pilihan saat ini tidak valid, set ke 'Software'
        if self.encoder_type_var.get() not in options:
            self.encoder_type_var.set("Software")

    def get_video_duration(self, filepath):
        """Mendapatkan durasi video dalam detik menggunakan ffprobe."""
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
        except (subprocess.CalledProcessError, FileNotFoundError, ValueError) as e:
            self.log(f"ERROR: Gagal mendapatkan durasi video: {e}")
            return None

    def start_compression_thread(self):
        """Memulai proses kompresi di thread terpisah agar UI tidak freeze."""
        if self.is_compressing:
            self.log("Kompresi sedang berjalan.")
            return
        
        # Validasi input
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

        self.is_compressing = True
        self.compress_button.configure(state="disabled", text="Sedang Mengompres...")
        self.status_label.configure(text="Status: Memulai...", text_color="cyan")
        self.progress_bar.set(0)
        
        # Hapus file log pass sebelumnya jika ada
        if os.path.exists("ffmpeg2pass-0.log"):
            os.remove("ffmpeg2pass-0.log")
        if os.path.exists("ffmpeg2pass-0.log.mbtree"):
            os.remove("ffmpeg2pass-0.log.mbtree")

        # Mulai thread
        thread = threading.Thread(target=self.run_compression, args=(target_mb,))
        thread.daemon = True
        thread.start()

    def run_compression(self, target_mb):
        """Logika utama untuk menjalankan kompresi ffmpeg."""
        duration = self.get_video_duration(self.input_path)
        if duration is None:
            self.compression_finished(success=False, message="Gagal mendapatkan durasi video.")
            return

        # Hitung bitrate (dalam bits per detik)
        # (Target Ukuran MB * 8 * 1024 * 1024) / Durasi detik
        target_bitrate_bits = (target_mb * 8 * 1024 * 1024) / duration
        target_bitrate_k = int(target_bitrate_bits / 1000)
        self.log(f"Target bitrate dihitung: {target_bitrate_k}k")

        # Tentukan codec dan encoder
        codec = self.codec_var.get()
        encoder_type = self.encoder_type_var.get()
        algorithm = self.algorithm_var.get()

        encoder_map = {
            "H.264": {"Software": "libx264", "NVIDIA": "h264_nvenc", "AMD": "h264_amf", "Intel": "h264_qsv"},
            "H.265": {"Software": "libx265", "NVIDIA": "hevc_nvenc", "AMD": "hevc_amf", "Intel": "hevc_qsv"},
            "AV1": {"Software": "libaom-av1", "NVIDIA": "av1_nvenc", "AMD": "av1_amf", "Intel": "av1_qsv"}
        }
        
        # AV1 software (libaom-av1) sangat lambat dan tidak mendukung two-pass dengan cara biasa
        if codec == "AV1" and encoder_type == "Software":
             self.compression_finished(success=False, message="ERROR: AV1 Software (libaom-av1) tidak didukung untuk mode target ukuran saat ini karena sangat lambat.")
             return

        ffmpeg_encoder = encoder_map[codec][encoder_type]
        self.log(f"Menggunakan encoder: {ffmpeg_encoder}")

        # --- Perintah FFMPEG ---
        # Pass 1
        self.status_label.configure(text="Status: Pass 1 dari 2...", text_color="cyan")
        self.log("\n--- MEMULAI PASS 1 ---")
        
        # Tentukan output null device berdasarkan OS
        null_device = 'NUL' if sys.platform == 'win32' else '/dev/null'

        pass1_cmd = [
            "ffmpeg", "-y", "-i", self.input_path,
            "-c:v", ffmpeg_encoder,
            "-b:v", f"{target_bitrate_k}k",
            "-pass", "1",
            "-preset", "slow" if algorithm == "AI (Efisien)" else "medium",
            "-f", "mp4", null_device
        ]
        
        # Tambahan argumen untuk AV1 software jika nanti didukung
        if ffmpeg_encoder == "libaom-av1":
            pass1_cmd.extend(["-cpu-used", "4"])

        success_pass1 = self.execute_ffmpeg_command(pass1_cmd, duration)
        if not success_pass1:
            self.compression_finished(success=False, message="Gagal pada Pass 1.")
            return

        # Pass 2
        self.status_label.configure(text="Status: Pass 2 dari 2...", text_color="cyan")
        self.log("\n--- MEMULAI PASS 2 ---")
        pass2_cmd = [
            "ffmpeg", "-y", "-i", self.input_path,
            "-c:v", ffmpeg_encoder,
            "-b:v", f"{target_bitrate_k}k",
            "-pass", "2",
            "-preset", "slow" if algorithm == "AI (Efisien)" else "medium",
            "-c:a", "aac", # Selalu copy audio stream
            "-b:a", "192k",
            self.output_path
        ]
        
        if ffmpeg_encoder == "libaom-av1":
            pass2_cmd.extend(["-cpu-used", "1"])

        success_pass2 = self.execute_ffmpeg_command(pass2_cmd, duration)
        if not success_pass2:
            self.compression_finished(success=False, message="Gagal pada Pass 2.")
            return

        self.compression_finished(success=True, message="Kompresi Selesai!")

    def execute_ffmpeg_command(self, command, duration):
        """Menjalankan perintah ffmpeg dan menangkap outputnya."""
        try:
            process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding='utf-8', errors='replace', creationflags=subprocess.CREATE_NO_WINDOW)
            
            stdout = process.stdout
            if stdout is None:
                self.log("ERROR: ffmpeg tidak memberikan output.")
                process.wait()
                return False

            time_pattern = re.compile(r"time=(\d{2}):(\d{2}):(\d{2})\.(\d{2})")

            for line in iter(stdout.readline, ''):
                self.log(line.strip())
                
                match = time_pattern.search(line)
                if match:
                    h, m, s, ms = map(int, match.groups())
                    current_time = h * 3600 + m * 60 + s + ms / 100
                    progress = current_time / duration
                    self.progress_bar.set(progress)
            
            process.wait()
            return process.returncode == 0

        except Exception as e:
            self.log(f"FATAL ERROR saat eksekusi: {e}")
            return False

    def compression_finished(self, success, message):
        """Dipanggil ketika kompresi selesai atau gagal."""
        self.is_compressing = False
        self.compress_button.configure(state="normal", text="Mulai Kompresi")
        if success:
            self.status_label.configure(text=f"Status: {message}", text_color="light green")
            self.progress_bar.set(1)
            self.log(f"\nSUKSES: File disimpan di {self.output_path}")
        else:
            self.status_label.configure(text=f"Status: {message}", text_color="red")
            self.progress_bar.set(0)
            self.log(f"\nGAGAL: {message}")
        
        # Hapus file log pass
        try:
            if os.path.exists("ffmpeg2pass-0.log"):
                os.remove("ffmpeg2pass-0.log")
            if os.path.exists("ffmpeg2pass-0.log.mbtree"):
                os.remove("ffmpeg2pass-0.log.mbtree")
        except OSError as e:
            self.log(f"Info: Gagal menghapus file log pass: {e}")


if __name__ == "__main__":
    # Cek dan install dependensi jika belum ada
    try:
        import customtkinter
    except ImportError:
        print("CustomTkinter belum terinstall. Menginstall sekarang...")
        subprocess.run([sys.executable, "-m", "pip", "install", "customtkinter"], check=True)
        print("Instalasi selesai. Silakan jalankan kembali script ini.")
        sys.exit(0)

    app = VideoCompressorApp()
    app.mainloop()
