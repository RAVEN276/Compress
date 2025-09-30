# Video Compressor (Beta)

Aplikasi GUI ringan dan modern untuk mengompresi video berdasarkan target ukuran file. Dibuat dengan Python (CustomTkinter) dan memanfaatkan FFmpeg sebagai mesin encoding.

Versi saat ini: 0.1.0 (Beta)

Executable (EXE) tersedia untuk Windows (dibangun dengan PyInstaller). Anda juga bisa menjalankan langsung via Python.

## ✨ Fitur

- Pilihan codec: H.264, H.265, AV1
- Pilihan encoder: Software (CPU) atau Hardware (GPU)
- Kompresi berdasarkan Target MB (akurasi lebih baik dengan 2-pass)
- Profil "AI (Efisien)": preset lebih lambat untuk kualitas lebih baik di ukuran sama
- Log FFmpeg realtime dan progress bar
- Deteksi otomatis akselerasi hardware yang benar-benar tersedia (Intel QSV, NVIDIA NVENC, AMD AMF) sesuai perangkat pengguna

## 🖥️ Deteksi Hardware

Berbeda dengan sekadar membaca daftar encoder FFmpeg, aplikasi ini benar-benar menguji setiap encoder hardware dengan mencoba menginisialisasinya pada video sintetis 1 detik. Hanya encoder yang berhasil diinisialisasi di mesin Anda yang akan ditampilkan di UI.

Contoh hasil:

- Laptop hanya Intel: yang muncul hanya "Intel" pada codec yang didukung
- Ada GPU NVIDIA: "NVIDIA" akan muncul jika NVENC aktif untuk H.264/H.265/AV1
- Tidak ada hardware encoding: hanya "Software" yang tersedia

## 📦 Prasyarat

- Windows 10/11 (disarankan) atau OS lain dengan penyesuaian
- Python 3.8+
- FFmpeg terpasang dan ada di PATH
  - Unduh: https://ffmpeg.org/download.html
- Paket Python: `customtkinter`

## 🔧 Instalasi (Mode Python)

```powershell
# Dari root proyek
pip install customtkinter
```

Pastikan `ffmpeg` dan `ffprobe` bisa diakses dari terminal:

```powershell
ffmpeg -version
ffprobe -version
```

## ▶️ Menjalankan Aplikasi

```powershell
python video_compressor_app.py
```

Atau jalankan file EXE di folder `dist/` jika Anda punya build.

## 🗜️ Cara Pakai

1. Pilih file video input
2. Pilih codec (H.264/H.265/AV1) dan tipe encoder (Software/Hardware)
3. Masukkan target ukuran (MB)
4. Pilih algoritma:
   - Standard: seimbang kecepatan/kualitas
   - AI (Efisien): lebih lambat, kualitas lebih baik
5. Tekan mulai; pantau progress dan log di aplikasi

Catatan:
- Output default adalah `.mp4` dengan audio AAC 192 kbps
- AV1 software (libaom-av1) untuk mode target-size dinonaktifkan pada Beta karena sangat lambat

## 🏗️ Build EXE (Windows, PyInstaller)

```powershell
pip install pyinstaller
python -m PyInstaller --onefile --windowed video_compressor_app.py
```

File EXE akan berada di folder `dist/`.

## 🧭 Kebijakan Versi

- Status saat ini: Beta (0.1.x). Perubahan minor tidak selalu menaikkan versi.
- Versi rilis stabil pertama akan ditandai sebagai `v1.0`.

## 🗺️ Roadmap

- [ ] Opsi kontainer output (MP4/MKV) dan pilih audio: copy vs re-encode
- [ ] Mode alternatif: CRF/Quality-based dan Target Bitrate (selain Target MB)
- [ ] Preset kustom per encoder (NVENC/QSV/AMF/libx26x)
- [ ] Dukungan batch (multi-file) dan antrian pekerjaan
- [ ] Pengaturan lanjutan (resolusi, fps, tune/psy, profile/level)
- [ ] Estimasi waktu dan sisa (ETA) yang lebih akurat
- [ ] Tema UI tambahan dan lokalization

## ⚠️ Keterbatasan (Beta)

- Target-size untuk AV1 software tidak didukung (sangat lambat)
- Kontainer masih tetap MP4; pilihan kontainer akan ditambah
- Akurasi 2-pass bisa bervariasi tergantung encoder/driver

## 🙌 Kredit

- FFmpeg sebagai backend encoding
- CustomTkinter untuk UI modern berbasis Tkinter
