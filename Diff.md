# Difference.md: Log Perubahan dan Pembaruan Sistem Optimasi Jaringan Jalan

Dokumen ini mencatat log perubahan, optimasi, dan peningkatan fitur dari arsitektur lama (**Versi 2: Algoritma Genetika + A***) menuju arsitektur baru (**Versi 1: Ant Colony Optimization + A***) untuk mendukung pembentukan *Mesh Network* yang lebih matang.

---

## 🚀 Ringkasan Perubahan Utama (The Big Upgrades)

| Komponen | Versi 2 (Lama) | Versi 1 (Baru) | Status |
| :--- | :--- | :--- | :--- |
| **Algoritma Makro** | Algoritma Genetika (GA) | Ant Colony Optimization (ACO) | **Major Upgrade** |
| **Representasi Gen** | Array Biner (0/1 untuk tiap pasangan) | Urutan Permutasi Pembuatan Rute | **Refactored** |
| **Kompleksitas Peta** | Grid Kosong (Hanya rintangan node) | Multi-Terrain (Gunung & Rawa) | **Lebih Realistis** |
| **Interaksi Arsitektur** | Isolasional (Grid di-reset tiap evaluasi) | Kolektif via Peta Feromon 2D Global | **Lebih Dinamis** |
| **Parameter Desain** | Murni Struktur Graf Ilmu Komputer | Standar Geometrik Teknik Sipil Nyata | **Fitur Baru** |

---

## 🛠️ Detil Pembaruan Sistem

### 1. Perubahan Paradigma Kecerdasan Artifisial (GA -> ACO)
* **Versi 2**: GA mengevaluasi status aktif/nonaktif jalur secara kaku lewat array biner (`0` atau `1`). GA tidak mempertimbangkan urutan kronologis pembuatan rute yang optimal.
* **Versi 1**: ACO mengoptimalkan **urutan prioritas pengerjaan rute** (permutasi urutan). Agen semut meletakkan jejak feromon pada sel grid yang dilewatinya, sehingga semut berikutnya dipandu oleh akumulasi feromon global secara dinamis.

### 2. Peningkatan Realisme Lingkungan (Environment)
* **Versi 2**: Lingkungan berupa grid kosong monoton tanpa variasi biaya rintangan alam selain koordinat node itu sendiri.
* **Versi 1**: Ditambahkan rintangan medan (*terrain*) nyata:
  * **Gunung**: Bersifat *impassable* (biaya melintas tak terhingga/$\infty$).
  * **Rawa**: Memiliki biaya melintas (*cost*) yang sangat tinggi.

### 3. Modifikasi Rumus Biaya Langkah A* (Pheromone-Driven Pathfinding)
* **Versi 2**: Fungsi biaya A* bersifat statis berdasarkan kondisi sel saat dievaluasi (Kosong = 10, Berjalan = 2, Macet = 50).
* **Versi 1**: Fungsi biaya A* dimodulasi secara dinamis oleh intensitas feromon semut pada matriks peta global (`world.pheromones`):
  $$\text{Cost A*} = \frac{\text{Physical Cell Cost}}{\text{Pheromone}}$$
  Mekanisme ini mengarahkan rute-rute baru untuk bergabung ke koridor jalan yang sama secara natural membentuk **Jalan Arteri Utama** (efek *sharing path*).

### 4. Penerapan Standar Geometrik Teknik Sipil
Versi 1 menambahkan tiga parameter fungsional baru untuk mendekati desain dunia nyata:
* **Turn Penalty (Penalti Kelokan)**: A* melacak arah sebelumnya (`last_dir`). Jika rute berbelok 90°, dikenakan biaya tambahan (+15.0) untuk meminimalkan pola jalan zig-zag.
* **Hamiltonian / Ring Road Incentive**: Memberikan potongan biaya besar (-1000.0) jika jaringan jalan berhasil menutup sirkuit membentuk jalan lingkar (*Ring Road*).
* **Fault-Tolerant Redundancy**: Algoritma dipaksa membangun minimal **5 rute tambahan** setelah graf terhubung penuh. Ini menjamin tersedianya jalan alternatif jika salah satu segmen utama terputus.

### 5. Efisiensi Alur Evaluasi (Workflow)
* **Versi 2**: Menggunakan *Penalti Isolasi* yang keras untuk membuang kromosom secara ekstrem, rentan membuat populasi mandek (*stuck*).
* **Versi 1**: Menggunakan mekanisme *Evaporasi Feromon* (10% penyusutan per generasi) dan *Deposisi Feromon* berbasis kualitas total cost ($\Delta\tau = 5000.0 / \text{Total Cost}$) untuk menjamin konvergensi solusi tanpa mematikan variasi rute alternatif secara mendadak.

## 🧾 Catatan Implementasi & Perbedaan Riil (Kode Saat Ini)

Berikut pengecekan mendalam terhadap kode sumber saat ini dan bagaimana pernyataan di atas benar atau perlu diperhalus:

- **ACO vs GA**: Kode utama kini memang menjalankan perilaku koloni semut (ACO) — `ga/ga.py` menginisialisasi grid `world.pheromones`, melakukan evaporasi (10%) dan deposisi berbasis `Q / cost`. Namun beberapa nama, label UI, dan struktur data masih memakai istilah/konvensi GA untuk kompatibilitas (mis. judul UI "Genetic Algorithm Road Planner", `interfaces.GAConfig`).

- **Representasi**: Chromosome adalah urutan permutasi indeks pasangan rute (list permutation). Ini sesuai dengan klaim "Urutan Permutasi Pembuatan Rute".

- **Pheromone**: Pheromone disimpan dan di-update di `world.pheromones` (evaporasi + deposit) — tetapi **poin penting**: A* yang ada (`model/world.py::a_star_search`) saat ini **tidak** menggunakan nilai feromon untuk menghitung biaya langkah. Dengan kata lain, feromon disimpan dan diperbarui, tetapi belum diintegrasikan ke fungsi biaya A*.

- **Rumus Biaya A***: Dokumen menyatakan biaya A* dimodulasi oleh feromon: Cost = PhysicalCellCost / Pheromone. Pada kode yang berjalan sekarang, `a_star_search` hanya memanggil `world.get_cell_cost(...)`; dan `World.get_cell_cost` menghitung biaya berdasarkan `road_layers`, `traffic_layers`, `default_cost`, `max_traf`, `growth_rate`, dan `discount_factor`. Jadi klaim formula feromon belum direalisasikan — perlu integrasi tambahan jika ingin sesuai dokumen.

- **Terrain (Gunung & Rawa)**: UI (`ui/app.py`) menyediakan `planning_terrain` dan memperbolehkan menandai sel sebagai `float('inf')` (gunung) atau cost besar (rawa). `WorldBuilder` juga menerima `tile_weights` saat pembuatan peta dasar. Namun objek `World` saat ini **tidak** menginisialisasi/menyimpan atribut `terrain_map` yang kemudian diharapkan UI; dan `World.get_cell_cost` tidak membaca peta terrain tersebut. Praktisnya: UI menampilkan gunung/rawa secara visual, tetapi pathfinding saat ini tidak mempertimbangkan `terrain_map`.

- **Turn Penalty**: Dokumen menyebut penalti kelokan (+15.0) dan pelacakan `last_dir` dalam A*. Implementasi A* dalam `model/world.py` **tidak** melacak arah sebelumnya dan tidak menerapkan penalti belokan saat ini.

- **Hamiltonian / Ring Road Incentive**: Implementasi ada — `ga.evaluate_chromosome` menghitung siklus (num_cycles) dari sel jalan dan mengurangi `total_cost` sebesar `1000.0` jika siklus ditemukan. Klaim ini sesuai kode.

- **Fault-Tolerant Redundancy**: Implementasi ada dalam `ga.evaluate_chromosome`/`run_genetic_algorithm` — terdapat mekanisme menambahkan hingga 5 rute tambahan setelah jaringan terhubung penuh (`extra_count >= 5` berhenti). Klaim ini sesuai kode.

- **Evaporasi & Deposisi**: Diimplementasikan di `ga/ga.py` dengan `evaporation_rate = 0.1` dan deposit `world.pheromones[x][y] += Q / best_gen_cost` pada sel jalan. Ini setara dengan pernyataan dokumen.

Jika Anda ingin dokumentasi sepenuhnya mencerminkan perilaku kode, saya sudah memperbaiki Diff.md dengan catatan di atas. Jika Anda ingin saya juga memperbaiki kode (mis. integrasikan pheromone ke `get_cell_cost`, tambahkan `terrain_map` ke `World`, dan implementasikan turn-penalty), beri tahu fitur mana yang ingin diaktifkan dan saya akan terapkan perubahan kode juga.


## Kendala Implementasi

Dalam pengembangan, beberapa pendekatan diuji dan menghasilkan karakteristik berbeda. Ringkasan eksperimen singkat:

| Algoritma | Tahap / Catatan | Hasil Pengamatan |
|---|---:|---|
| Genetic Algorithm (GA) | Eksperimen awal | Cenderung membentuk struktur seperti MST — satu jalur utama tanpa banyak redundansi, sehingga rawan kemacetan dan kegagalan tunggal.
| Civil planner (heuristik) | Eksperimen lanjutan | Menghasilkan banyak jalur dan redundansi; namun sering berlebihan (inefisien) dan memboroskan sumber daya pembuatan jalan.
| Ant Colony Optimization (ACO) | Saat ini (eksperimental) | Memperbaiki beberapa kelemahan GA dan Civil planner: menghasilkan kombinasi koridor utama dan jalur alternatif. Masih belum optimal — beberapa konfigurasi tetap suboptimal tergantung parameter dan peta.

Catatan: penamaan "Civil planner" muncul dari percobaan **Zakiye**, sepenuhnya tanya beliau.