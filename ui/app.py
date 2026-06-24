# ui/simulator_app.py
import pygame
import sys
import itertools
from model.world import World, WorldBuilder
from ga.ga import run_genetic_algorithm, evaluate_chromosome, get_gen

# Palette Warna (Dark Theme)
BG_MAIN = (21, 26, 35)          
BG_PANEL = (30, 38, 50)         
GRID_LINE = (45, 55, 72)        
TEXT_WHITE = (230, 235, 245)    
TEXT_MUTED = (140, 150, 170)    
BLUE_TEXT = (96, 165, 250)

ROAD_SHARING = (52, 211, 153)   # Hijau neon
ROAD_CONGESTED = (248, 113, 113)# Merah pastel

TERRAIN_SWAMP = (120, 110, 85)   # Cokelat lumpur / rawa
TERRAIN_MOUNTAIN = (75, 85, 100) # Abu-abu batu / gunung


class SimulationUI:
    def __init__(self, size=(15, 15), cell_size=32):
        pygame.init()
        self.grid_x_size, self.grid_y_size = size
        self.cell_size = cell_size
        
        # Hitung dimensi layout
        self.grid_w = self.grid_x_size * self.cell_size
        self.grid_h = self.grid_y_size * self.cell_size
        self.padding = 20
        self.sidebar_w = 260
        
        self.window_w = self.grid_w + (self.padding * 3) + self.sidebar_w
        self.window_h = max(self.grid_h + (self.padding * 2) + 50, 550)
        
        self.screen = pygame.display.set_mode((self.window_w, self.window_h))
        pygame.display.set_caption("AI Road Infrastructure Simulator")
        self.clock = pygame.time.Clock()
        
        # Fonts
        self.title_font = pygame.font.SysFont("Segoe UI", 24, bold=True)
        self.header_font = pygame.font.SysFont("Segoe UI", 18, bold=True)
        self.font = pygame.font.SysFont("Segoe UI", 14)
        
        # Konfigurasi Icon Jalan
        self.road_sprite_width, self.road_sprite_height = 32, 32
        self.icon_road = list()

        # Load Assets
        try:
            self.icon_city = pygame.image.load("ui/assets/city.png")
            self.icon_city = pygame.transform.scale(self.icon_city, (self.cell_size, self.cell_size))

            # Load Roads
            road_sheet =  pygame.image.load("ui/assets/roads.png").convert_alpha()

            for y in range(4):
                for x in range(4):
                    rect = pygame.Rect(x * self.road_sprite_width, y * self.road_sprite_height, self.road_sprite_width, self.road_sprite_height)
                    road_sprite = road_sheet.subsurface(rect).copy()
                    road_sprite = pygame.transform.scale(road_sprite, (self.cell_size, self.cell_size))
                    self.icon_road.append(road_sprite)

        except pygame.error as e:
            print(f"Gagal memuat aset gambar! Error: {e}")
            sys.exit()
            
        # APP STATES
        # Mode: "PLANNING" (Naruh kota manual) atau "SIMULATION" (GA & Brush jalan ready)
        self.mode = "PLANNING" 
        self.input_nodes = [] # Menyimpan list of tuple (x, y) input user
        
        # Objek backend yang akan di-build dinamis nanti
        self.builder = None
        self.world = None
        
        # Simulation control states
        self.brush_mode = "MACET"
        self.is_running = False
        self.current_generation = 0
        self.best_cost = 0.0
        
        # Matriks sementara untuk menyimpan koordinat rawa (-10) dan gunung (inf) di fase planning
        # Ubah bagian paling bawah di __init__ kamu:
        # Default cost tanah kosong adalah 50.0
        self.planning_terrain = [[50.0 for _ in range(self.grid_y_size)] for _ in range(self.grid_x_size)]
        self.brush_mode = "KOTA"
        
        # State untuk notifikasi error
        self.error_message = ""      
        self.error_timer = 0
        
        # --- STATE ANIMASI GENERASI ---
        self.current_anim_gen = 0       
        self.anim_delay_counter = 0     
        self.is_animating = False       

    def draw_rounded_panel(self, rect, color, radius=8):
        pygame.draw.rect(self.screen, color, rect, border_radius=radius)

    def draw_roads(self):

        # Timpa Gambar Ikon Jalan Tol jika koordinat tersebut dilewati rute GA
        for x in range(self.grid_x_size):
            for y in range(self.grid_y_size):
                cell_rect = pygame.Rect(
                    self.padding + (x * self.cell_size),
                    self.padding + 50 + (y * self.cell_size),
                    self.cell_size,
                    self.cell_size
                )

                layers = self.world.road_layers[x][y] if (self.mode == "SIMULATION" and self.world) else 0

                if layers > 0 and self.mode == "SIMULATION":
                    road_icon_idx = 0

                    # check atas
                    if y - 1 >= 0 and self.world.road_layers[x][y-1] > 0:
                        road_icon_idx += 1

                    # check kanan
                    if  x + 1 <= self.grid_x_size-1 and self.world.road_layers[x+1][y] > 0:
                        road_icon_idx += 2

                    # check bawah
                    if y + 1 <= self.grid_y_size-1 and self.world.road_layers[x][y+1] > 0:
                        road_icon_idx += 4

                    # check kiri
                    if x - 1 >= 0 and self.world.road_layers[x-1][y] > 0:
                        road_icon_idx += 8


                    self.screen.blit(self.icon_road[road_icon_idx], (cell_rect.x, cell_rect.y))

                    overlay = pygame.Surface((self.cell_size, self.cell_size), pygame.SRCALPHA)
                    if layers <= self.world.max_traf:
                        overlay.fill((52, 211, 153, 100))
                    else:
                        overlay.fill((248, 113, 113, 150))

                    self.screen.blit(overlay, (cell_rect.x, cell_rect.y))

    def draw_grid_area(self):
        grid_rect = pygame.Rect(self.padding, self.padding + 50, self.grid_w + 2, self.grid_h + 2)
        self.draw_rounded_panel(grid_rect, BG_PANEL)
        
        for x in range(self.grid_x_size):
            for y in range(self.grid_y_size):
                cell_rect = pygame.Rect(
                    self.padding + (x * self.cell_size),
                    self.padding + 50 + (y * self.cell_size),
                    self.cell_size,
                    self.cell_size
                )
                
                # Ambil nilai rintangan alam
                # Cek nilai terrain (ambil dari world jika simulation, ambil dari planning_terrain jika planning)
                val = self.world.terrain_map[x][y] if (self.mode == "SIMULATION" and self.world) else self.planning_terrain[x][y]
                layers = self.world.road_layers[x][y] if (self.mode == "SIMULATION" and self.world) else 0
                
                # Cek bobot biaya riil untuk menentukan warna visual
                if val == float('inf'):
                    pygame.draw.rect(self.screen, TERRAIN_MOUNTAIN, cell_rect)
                elif val > 50.0 and val != float('inf'): 
                    pygame.draw.rect(self.screen, TERRAIN_SWAMP, cell_rect) # Jika di atas cost normal (50), berarti rawa
                else:
                    pygame.draw.rect(self.screen, BG_PANEL, cell_rect)
                
                pygame.draw.rect(self.screen, GRID_LINE, cell_rect, 1)

    def draw_cities(self):
        # 1. Jika masih PLANNING mode, gambar kota bayangan dari input_nodes
        if self.mode == "PLANNING":
            for (cx, cy) in self.input_nodes:
                pos_x = self.padding + (cx * self.cell_size)
                pos_y = self.padding + 50 + (cy * self.cell_size)
                self.screen.blit(self.icon_city, (pos_x, pos_y))
                
        # 2. Jika sudah SIMULATION mode, gambar kota asli dari backend
        elif self.mode == "SIMULATION" and self.world:
            for city_id, (cx, cy) in self.world.node_pos.items():
                pos_x = self.padding + (cx * self.cell_size)
                pos_y = self.padding + 50 + (cy * self.cell_size)
                self.screen.blit(self.icon_city, (pos_x, pos_y))
                
                # Beri border warna kluster
                cid = self.world.pos_to_cluster.get((cx, cy))
                if cid is not None:
                    cluster_color = ((cid * 75) % 200 + 50, (cid * 130) % 200 + 50, 230)
                    center_x = pos_x + self.cell_size // 2
                    center_y = pos_y + self.cell_size // 2
                    pygame.draw.circle(self.screen, cluster_color, (center_x, center_y), self.cell_size // 2, 2)

    def draw_right_panels(self):
        sidebar_x = self.grid_w + (self.padding * 2)
        
        # PANEL 1: Simulation Stats (Tetap sama seperti sebelumnya)
        info_rect = pygame.Rect(sidebar_x, self.padding + 50, self.sidebar_w, 180)
        self.draw_rounded_panel(info_rect, BG_PANEL)
        self.screen.blit(self.header_font.render("Simulation Info", True, TEXT_WHITE), (sidebar_x + 15, self.padding + 65))
        
        total_cluster_str = str(len(self.world.cluster_members)) if (self.world and self.mode == "SIMULATION") else "0"
        stats = [
            ("Application Mode", self.mode),
            ("Total Kota/Node", str(len(self.input_nodes))),
            ("Generasi", str(self.current_generation)),
            ("Best Cost Network", f"{self.best_cost:.2f}"),
            ("Total Kluster", total_cluster_str)
        ]
        for i, (label, val) in enumerate(stats):
            y_pos = self.padding + 95 + (i * 22)
            self.screen.blit(self.font.render(label, True, TEXT_MUTED), (sidebar_x + 15, y_pos))
            self.screen.blit(self.font.render(val, True, TEXT_WHITE), (sidebar_x + 140, y_pos))

        # PANEL 2: Controls (Disesuaikan ulang posisinya)
        ctrl_rect = pygame.Rect(sidebar_x, self.padding + 245, self.sidebar_w, 260) # Dipertinggi sedikit
        self.draw_rounded_panel(ctrl_rect, BG_PANEL)
        self.screen.blit(self.header_font.render("Controls", True, TEXT_WHITE), (sidebar_x + 15, self.padding + 260))
        
        if self.mode == "PLANNING":
            controls_text = [
                "[Klik Kiri]    Taruh/Hapus Bangunan",
                "[G]            Acak 25 Posisi Bangunan",
                "[1]            Brush Mode: BANGUNAN",
                "[2]            Brush Mode: RAWA",
                "[3]            Brush Mode: GUNUNG",
                "[H]            Brush Mode: HANCUR MEDAN",
                "[ENTER]        Kunci & Build Map",
                "",
                "Kuas Aktif: " + self.brush_mode
            ]
        else:
            controls_text = [
                "[SPACE]       Pause / Resume",
                "[M]           Brush Mode: MACET",
                "[H]           Brush Mode: HANCUR JALAN",
                "[R]           Kembali ke Planning",
                "",
                "Kuas Aktif: " + self.brush_mode,
                "Klik-Drag kiri di grid untuk pasang",
                "penalti kemacetan real-time."
            ]
            
        for i, line in enumerate(controls_text):
            y_pos = self.padding + 290 + (i * 19)
            color = BLUE_TEXT if line.startswith("[") else TEXT_MUTED
            self.screen.blit(self.font.render(line, True, color), (sidebar_x + 15, y_pos))
            
    def draw_error_notification(self):
        """Menggambar banner notifikasi merah jika error_timer aktif"""
        if self.error_timer > 0:
            # Kurangi durasi timer setiap frame berjalan
            self.error_timer -= 1
            
            # Tentukan posisi banner di tengah area grid
            banner_w = self.grid_w - 40
            banner_h = 45
            banner_x = self.padding + 20
            banner_y = self.padding + 50 + (self.grid_h // 2) - (banner_h // 2)
            
            # Gambar background box melengkung berwarna merah solid/pastel
            rect = pygame.Rect(banner_x, banner_y, banner_w, banner_h)
            self.draw_rounded_panel(rect, (239, 68, 68)) # Warna Merah Solid (Tailwind Red 500)
            
            # Tambahkan outline putih tipis di sekeliling box agar kontras
            pygame.draw.rect(self.screen, (255, 255, 255), rect, 1, border_radius=8)
            
            # Render teks pesan error berwarna putih bold
            error_font = pygame.font.SysFont("Segoe UI", 14, bold=True)
            text_surface = error_font.render(self.error_message, True, (255, 255, 255))
            text_rect = text_surface.get_rect(center=(banner_x + banner_w // 2, banner_y + banner_h // 2))
            
            self.screen.blit(text_surface, text_rect)

    def build_simulation_world(self):
        if len(self.input_nodes) < 2:
            # Set notifikasi error di UI jika kota kurang dari 2
            self.error_message = "Taruh minimal 2 kota!"
            self.error_timer = 90  # 90 frame / 30 fps = Tampil selama 3 detik
            return
            
        USER_DE_PATH = 50.0
        
        # 1. Inisialisasi builder terlebih dahulu
        self.builder = WorldBuilder(
            size=(self.grid_x_size, self.grid_y_size),
            num_nodes=len(self.input_nodes),
            random_nodes=False,
            de_path=USER_DE_PATH,
            inp=self.input_nodes,
            tile_weights=self.planning_terrain
        )

        # 2. PANGGIL DENGAN SATU ARGUMEN SAJA (self.input_nodes)
        if not self.builder.check_node_accessibility(self.input_nodes):
            self.error_message = "KOTA TERISOLASI OLEH GUNUNG!"
            self.error_timer = 90  # Tampilkan selama 3 detik
            self.builder = None
            return # Batalkan build, tetap di PLANNING mode

        # 3. Jika lolos, baru buat objek World asli seperti biasa
        self.world = World(
            x=self.builder.x,
            y=self.builder.y,
            node_positions=self.builder.node_positions,
            pos_to_cluster=self.builder.pos_to_cluster,
            cluster_members=self.builder.cluster_members,
            default_cost=self.builder.de_path,
            threshold=2,
            growth_rate=2.0,
            discount_factor=0.01,
        )
        
        # Sinkronisasi terrain map
        for x in range(self.grid_x_size):
            for y in range(self.grid_y_size):
                self.world.terrain_map[x][y] = self.planning_terrain[x][y]
        
        self.mode = "SIMULATION"
        self.brush_mode = "MACET"
        print("World berhasil dibuat! Masuk ke Simulation Mode.")

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
                
            elif event.type == pygame.KEYDOWN:
                if self.mode == "PLANNING":
                    if event.key == pygame.K_RETURN:
                        self.build_simulation_world()
                    elif event.key == pygame.K_r:
                        self.input_nodes.clear()
                        self.planning_terrain = [[0 for _ in range(self.grid_y_size)] for _ in range(self.grid_x_size)]
                    elif event.key == pygame.K_g:
                        self.input_nodes.clear()
                        import random
                        all_positions = [(i, j) for i in range(self.grid_x_size) for j in range(self.grid_y_size)]
                        jumlah_node_acak = min(25, len(all_positions))
                        self.input_nodes = random.sample(all_positions, jumlah_node_acak)
                    # Tombol ganti brush di mode planning
                    elif event.key == pygame.K_1:   self.brush_mode = "KOTA"
                    elif event.key == pygame.K_2:   self.brush_mode = "RAWA"
                    elif event.key == pygame.K_3:   self.brush_mode = "GUNUNG"
                    elif event.key == pygame.K_h:   self.brush_mode = "HANCUR MEDAN"
                
                elif self.mode == "SIMULATION":
                    if event.key == pygame.K_SPACE:
                        self.is_running = not self.is_running
                    elif event.key == pygame.K_m:   self.brush_mode = "MACET"
                    elif event.key == pygame.K_h:   self.brush_mode = "HANCUR JALAN"
                    elif event.key == pygame.K_r:
                        self.mode = "PLANNING"
                        self.world = None
                        self.builder = None
                        self.current_generation = 0
                        self.best_cost = 0.0
                        self.is_running = False
                        self.brush_mode = "KOTA"

            # Logika Klik Tunggal / Drag Mouse
            elif pygame.mouse.get_pressed()[0]:
                mx, my = pygame.mouse.get_pos()
                grid_start_y = self.padding + 50
                if self.padding <= mx < self.padding + self.grid_w and grid_start_y <= my < grid_start_y + self.grid_h:
                    grid_x = (mx - self.padding) // self.cell_size
                    grid_y = (my - grid_start_y) // self.cell_size
                    coord = (grid_x, grid_y)
                    
                    if self.mode == "PLANNING":
                        if self.brush_mode == "KOTA":
                            # Klik biasa (bukan drag ditahan) agar tidak duplikat instant-remove
                            if event.type == pygame.MOUSEBUTTONDOWN:
                                if coord in self.input_nodes: self.input_nodes.remove(coord)
                                else: self.input_nodes.append(coord)
                        elif self.brush_mode == "RAWA":
                            self.planning_terrain[grid_x][grid_y] = 250.0  # Rawa langsung diberi cost mahal (5x lipat)
                        elif self.brush_mode == "GUNUNG":
                            self.planning_terrain[grid_x][grid_y] = float('inf') # Gunung langsung diberi cost tak hingga
                        elif self.brush_mode == "HANCUR MEDAN":
                            self.planning_terrain[grid_x][grid_y] = 50.0   # Kembalikan ke cost normal tanah kosong
                            
                    elif self.mode == "SIMULATION" and self.world:
                        if self.brush_mode == "MACET":
                            self.world.road_layers[grid_x][grid_y] = 5
                        elif self.brush_mode == "HANCUR JALAN":
                            # Kembalikan ke kondisi medan asli sebelum kena jalan tol
                            self.world.road_layers[grid_x][grid_y] = 0
                            
    def update_generation_animation(self):
        """Fungsi ini dipanggil setiap frame untuk memperbarui ubin jalan berdasarkan generasi"""
        if not self.is_animating:
            return

        # Atur kecepatan transisi (misal: ganti generasi setiap 5 frame sekali ~ 0.16 detik)
        self.anim_delay_counter += 1
        if self.anim_delay_counter >= 20:
            self.anim_delay_counter = 0
            
            chrom, cost, paths = get_gen(self.current_anim_gen)
            
            # 2. Jika data generasi tersedia, update peta runtime dan infobar di UI
            if paths is not None:
                # Reset road_layers ke 0 dulu sebelum menimpa dengan data generasi baru
                self.world.road_layers = [[0 for _ in range(self.grid_y_size)] for _ in range(self.grid_x_size)]
                
                # Rekonstruksi tumpukan jalan tol berdasarkan paths generasi saat ini
                for path in paths:
                    for x, y in path:
                        self.world.road_layers[x][y] += 1
                
                # Perbarui teks informasi di panel kanan UI
                self.best_cost = cost
                self.current_generation = self.current_anim_gen + 1 # Tampilkan berurutan dari 1-20
                
                # Geser ke generasi berikutnya untuk frame selanjutnya
                self.current_anim_gen += 1
            else:
                # Jika get_gen mengembalikan None (artinya sudah lewat dari gen 20), animasi selesai!
                self.is_animating = False
                print("Animasi optimasi jaringan selesai!")

    def run(self):
        while True:
            self.handle_events()
            self.screen.fill(BG_MAIN)
            
            # Judul
            title_surface = self.title_font.render("ACO Road Planner", True, TEXT_WHITE)
            self.screen.blit(title_surface, (self.padding, self.padding))
            
            # Logika Eksekusi GA saat Simulation Mode aktif
            # Di dalam main loop run():
            if self.mode == "SIMULATION" and self.is_running and self.world:
                daftar_id_kota = list(self.world.node_pos.keys())
                daftar_rute = list(itertools.combinations(daftar_id_kota, 2))
                
                best_order, best_cost = run_genetic_algorithm(self.world, daftar_rute, pop_size=30, generations=20)
                
                self.current_anim_gen = 0
                self.anim_delay_counter = 0
                self.is_animating = True
                self.is_running = False  
                
            # --- JALANKAN PROSES UPDATE ANIMASI REAL-TIME ---
            self.update_generation_animation()
            
            # --- AREA RENDERING UTAMA ---
            self.draw_grid_area()
            self.draw_roads()
            self.draw_cities()
            self.draw_right_panels()
            
            # PANGGILA HANDLER NOTIFIKASI DI SINI (Digambar paling atas agar tidak tertutup grid)
            self.draw_error_notification()
            # ----------------------------
            
            pygame.display.flip()
            self.clock.tick(30)