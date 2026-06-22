# Optimasi Jaringan Jalan Global Menggunakan Ant Colony Optimization (ACO) dan A* (Mesh Network Approach)

Dokumen ini berisi deskripsi ide proyek dan rencana implementasi sistem kecerdasan artifisial untuk mengoptimalkan tata ruang jaringan jalan dinamis berbasis graf bebas (*Mesh Network*) dengan menerapkan prinsip-prinsip teknik sipil.

---

### 1. Deskripsi Matang Ide Proyek

* **Lingkungan & Node**: Proyek berjalan di atas grid atau matriks 2D berisi rintangan alam berupa Gunung (impassable/inf) dan Rawa (cost tinggi), serta $N$ node kota acak. Node kota berfungsi sebagai rintangan fisik, artinya jalan tidak boleh dibangun menembus koordinat kota lain kecuali kota tersebut merupakan titik awal atau tujuan dari jalur tersebut.

* **Mekanisme Konektivitas**: Hubungan antar-sel jalan hanya berlaku secara ortogonal melalui 4 arah (Atas, Bawah, Kiri, atau Kanan) dan melarang pergerakan diagonal. Seluruh kota harus terhubung ke dalam jaringan jalan global berbentuk **Mesh Network (Graf Bebas)**. Pendekatan ini mengizinkan adanya jalur alternatif dan rute ganda (*loop/cycle*) demi menghindari ketergantungan pada satu jalur tunggal yang rentan macet atau terputus.

* **Aturan Skor & Kemacetan**: Membangun jalan di atas sel grid yang sudah memiliki jalan dari rute lain akan memberikan keuntungan berupa insentif berbagi jalur (*sharing path*). Apabila jumlah tumpukan jalur pada satu sel melampaui batas traffic, sel tersebut akan dianggap mengalami kemacetan parah dan biayanya naik secara eksponensial.

---

### 2. Implementasi ACO + A* (Civil Engineering Design)

Kolaborasi ini membagi tugas secara adil: **ACO** bertugas sebagai otak makro untuk menentukan prioritas rute dan menyebarkan feromon pada jalur yang optimal, sementara **A*** bertugas sebagai navigator lapangan yang merancang koordinat jalurnya secara dinamis di atas grid fisik.

#### A. Mekanisme Ant Colony Optimization (ACO)
* **Kromosom/Semut**: Setiap semut mewakili urutan pembuatan rute kota (permutasi acak dari seluruh pasangan rute).
* **Peta Feromon (`world.pheromones`)**: Matriks 2D yang mencatat intensitas jejak semut sebelumnya. Sel yang sering dilewati oleh semut dengan skor terbaik akan memiliki feromon yang tinggi.
* **Biaya Terpandu Feromon**: Selama pencarian rute oleh A*, biaya perjalanan pada sel grid dipengaruhi langsung oleh feromon:
  $$\text{Cost A*} = \frac{\text{Physical Cell Cost}}{\text{Pheromone}}$$
  Jalan dengan feromon tinggi akan berbiaya sangat murah, mengarahkan semut generasi berikutnya untuk berbagi jalur (*sharing path*) membentuk jalan arteri utama.
* **Evaporasi & Deposisi Feromon**:
  - Pada akhir iterasi, feromon di seluruh peta menguap sebesar $10\%$ agar sistem tidak terjebak pada jalur suboptimal.
  - Semut terbaik di generasi tersebut menaburkan feromon baru pada sel-sel jalan yang dilaluinya sebanding dengan kualitas solusi:
    $$\Delta\tau = \frac{5000.0}{\text{Total Cost}}$$

#### B. Aturan Pembangunan Teknik Sipil Nyata
Sistem ini mengadopsi standar rancangan geometrik jalan raya teknik sipil nyata:
* **Turn Penalty (Penghindaran Kelokan Tajam)**: A* melacak arah gerakan sebelumnya (`last_dir`). Setiap kali jalan berbelok 90 derajat, dikenakan biaya tambahan (**Turn Penalty = 15.0**). Ini meminimalkan jalan berkelok-kelok (*zig-zag*) tidak teratur dan menghasilkan koridor jalan lurus yang efisien.
* **Hamiltonian / Ring Road Incentive**: Jaringan jalan yang membentuk sirkuit melingkar tertutup (loop) diberikan bonus diskon biaya sebesar **1000.0**. Ini mendorong terbentuknya jalan lingkar luar (*Ring Road*) sebagai jalur alternatif memutar.
* **Jalan Alternatif Cadangan (Redundansi)**: Algoritma dipaksa untuk terus membangun minimal **5 rute tambahan** setelah seluruh kota terhubung. Ini memastikan tersedianya jalan alternatif cadangan. Jika salah satu jalan utama dihancurkan (misal lewat mode HANCUR di simulator), kota-kota tetap terhubung melalui jalur melingkar cadangan tersebut.

---

## Install Dependencies

Untuk memasang pustaka Python yang dibutuhkan oleh proyek ini, jalankan perintah berikut:

```bash
uv pip install -r requirements.txt
```

Atau menggunakan pip standar:

```bash
pip install pygame
```

Aplikasi dapat dijalankan melalui berkas utama simulator:

```bash
uv run python runner.py
```