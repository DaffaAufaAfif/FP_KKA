# Optimasi Jaringan Jalan Global Menggunakan Algoritma Genetika dan A* (Mesh Network Approach)

Dokumen ini berisi deskripsi ide proyek dan rencana implementasi sistem kecerdasan artifisial untuk mengoptimalkan tata ruang jaringan jalan dinamis berbasis graf bebas (*Mesh Network*).

---

### 1. Deskripsi Matang Ide Proyek

* **Lingkungan & Node**: Proyek berjalan di atas grid atau matriks 2D yang awalnya kosong dengan $N$ node acak tanpa ada yang saling bertumpuk. Node lain dalam sistem berfungsi sebagai rintangan, yang berarti sebuah jalur tidak boleh dibangun menembus koordinat node lain kecuali jika node tersebut merupakan titik awal atau titik tujuan dari jalur tersebut.

* **Mekanisme Konektivitas**: Hubungan antar-sel jalan hanya berlaku secara ortogonal melalui 4 arah (Atas, Bawah, Kiri, atau Kanan) dan melarang pergerakan diagonal. Seluruh node harus terhubung ke dalam jaringan jalan global berbentuk **Mesh Network (Graf Bebas)**. Pendekatan ini mengizinkan adanya jalur alternatif, jalan pintas, atau rute ganda (*loop/cycle*) demi menghindari ketergantungan pada satu jalur tunggal yang rentan macet.

* **Aturan Skor & Kemacetan**: Membangun jalan di atas sel grid yang sudah memiliki jalan dari node lain akan memberikan keuntungan berupa insentif nilai positif (berbagi jalur/*sharing*). Apabila jumlah tumpukan jalur pada satu sel melampaui batas $x$, sel tersebut akan dianggap mengalami kemacetan parah dan nilainya berubah menjadi penalti negatif. Namun, jika berdasarkan pencarian rute global ternyata jalur macet tersebut merupakan opsi dengan total biaya terkecil, maka program akan tetap membiarkan kemacetan tersebut terjadi.

* **Goal Akhir**: Menghasilkan rancangan jaringan jalan global dengan total jarak terpendek dan skor nilai positif tertinggi sembari meminimalkan kemacetan parah, serta memastikan tidak ada node yang terisolasi dari jaringan.

---

### 2. Rencana Implementasi GA + A*

Kolaborasi ini membagi tugas secara adil: **GA** bertugas sebagai otak makro untuk menentukan topologi/kombinasi jalan yang aktif, sementara **A*** bertugas sebagai arsitek lapangan yang menggambar jalurnya secara dinamis di atas grid fisik.

#### A. Arsitektur Kromosom (Sisi GA)

* Satu kromosom direpresentasikan sebagai **Array Biner (0 atau 1)** dengan panjang sesuai dengan total seluruh kemungkinan kombinasi pasangan node yang ada, yaitu:
  $$\text{Panjang Kromosom} = \frac{N(N-1)}{2}$$
* Angka `1` berarti jalur/koneksi makro antar pasangan node tersebut aktif (harus dibangun), sedangkan `0` berarti tidak aktif (tidak dibangun).
* GA bertugas menentukan kombinasi pasangan jalan mana saja yang aktif atau tidak aktif untuk membentuk struktur jaringan terbaik tanpa harus mengetahui detail belokan rute di dalam grid.

#### B. Logika Perhitungan Rute (Sisi A*)

* A\* bertugas menggambar rute jalan nyata berdasarkan instruksi pasangan node yang bernilai `1` di dalam kromosom milik GA.
* Biaya langkah (*Cost*) pada fungsi tetangga A* dimodifikasi secara dinamis dengan membaca kondisi matriks 2D pada *real-time*:
  * **Sel Kosong**: Bernilai cost standar (misal: 10) karena merupakan biaya pembangunan jalan baru.
  * **Sel Berjalan ($\le x$)**: Bernilai cost sangat murah (misal: 2) agar A* condong berbagi jalur (*sharing path*).
  * **Sel Macet ($> x$)**: Bernilai cost sangat mahal (misal: 50) agar A* sebisa mungkin memutar, namun tetap bisa diterobos jika rute memutar memakan terlalu banyak sel kosong.
  * **Sel Berisi Node Lain**: Bernilai cost tak terhingga ($\infty$) agar tidak bisa dilewati secara sembarangan.

#### C. Siklus Alur Program (Workflow)

1. **Inisialisasi**: Program membuat populasi awal yang terdiri dari puluhan kandidat solusi kromosom berbentuk array biner secara acak.
2. **Evaluasi (Fitness Function)**: Untuk menguji tiap kromosom, matriks grid 2D dikosongkan terlebih dahulu. A* kemudian dipanggil untuk menggambar rute hanya pada pasangan node yang bergen `1`. Skor *Fitness* akhir dihitung berdasarkan rumus:
   $$\text{Fitness} = (\text{Bonus Sharing}) - (\text{Penalti Macet}) - (\text{Total Panjang Jalur}) - (\text{Penalti Isolasi})$$
   *Catatan:* Program akan memberikan **Penalti Sangat Besar (Penalti Isolasi)** jika ditemukan ada node yang sama sekali tidak memiliki jalur masuk/keluar (terisolasi) akibat kromosom terlalu banyak berisi angka `0`.
3. **Seleksi**: Solusi dengan nilai fitness rendah akan dibuang, sementara kromosom dengan fitness tinggi dipertahankan untuk menjadi orang tua (*parent*).
4. **Crossover & Mutasi**: Pasangan orang tua terbaik digabungkan fiturnya menggunakan *crossover* pada array biner untuk melahirkan variasi anak baru. Mekanisme mutasi dilakukan dengan cara *bit-flip* (mengubah `0` menjadi `1` atau sebaliknya) secara acak pada gen tertentu agar program dapat menemukan alternatif jalan pintas yang tidak terduga.
5. **Iterasi & Visualisasi**: Proses evaluasi hingga mutasi diulang terus-menerus selama puluhan hingga ratusan generasi. Kromosom biner terbaik pada generasi terakhir akan diambil, digambar ulang oleh A* pada kanvas bersih, lalu divisualisasikan sebagai cetak biru jaringan jalan yang paling optimal.

---

## Install Dependencies

To install required Python packages for this project, create and activate a virtual environment, then install from the included requirements file:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

If you don't want a virtualenv, you can install the main dependency directly:

```bash
pip install pygame
```

The project currently depends on `pygame` in addition to standard-library modules.