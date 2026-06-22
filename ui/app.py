# ui/simulator_app.py
import pygame
import sys
import itertools
from model.world import World, WorldBuilder
from ga.ga import run_genetic_algorithm, evaluate_chromosome

# Palette Warna (Dark Theme)
BG_MAIN = (21, 26, 35)          
BG_PANEL = (30, 38, 50)         
GRID_LINE = (45, 55, 72)        
TEXT_WHITE = (230, 235, 245)    
TEXT_MUTED = (140, 150, 170)    
BLUE_TEXT = (96, 165, 250)

ROAD_SHARING = (52, 211, 153)   # Hijau neon
ROAD_CONGESTED = (248, 113, 113)# Merah pastel

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
        
        # Load Assets
        try:
            self.icon_city = pygame.image.load("ui/assets/1.png")
            self.icon_city = pygame.transform.scale(self.icon_city, (self.cell_size, self.cell_size))
            self.icon_road = pygame.image.load("ui/assets/2.png")
            self.icon_road = pygame.transform.scale(self.icon_road, (self.cell_size, self.cell_size))
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

    def draw_rounded_panel(self, rect, color, radius=8):
        pygame.draw.rect(self.screen, color, rect, border_radius=radius)

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
                
                # Render jalan hanya jika sudah masuk mode SIMULATION
                if self.mode == "SIMULATION" and self.world:
                    layers = self.world.road_layers[x][y]
                    if layers > 0:
                        self.screen.blit(self.icon_road, (cell_rect.x, cell_rect.y))
                        overlay = pygame.Surface((self.cell_size, self.cell_size), pygame.SRCALPHA)
                        if layers <= self.world.max_traf:
                            overlay.fill((52, 211, 153, 100)) 
                        else:
                            overlay.fill((248, 113, 113, 150)) 
                        self.screen.blit(overlay, (cell_rect.x, cell_rect.y))
                
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
        
        # PANEL 1: Simulation Stats
        info_rect = pygame.Rect(sidebar_x, self.padding + 50, self.sidebar_w, 180)
        self.draw_rounded_panel(info_rect, BG_PANEL)
        self.screen.blit(self.header_font.render("Simulation Info", True, TEXT_WHITE), (sidebar_x + 15, self.padding + 65))
        
        total_cluster_str = str(len(self.world.cluster_members)) if (self.world and self.mode == "SIMULATION") else "0"
        stats = [
            ("Application Mode", self.mode),
            ("Total Kota/Node", str(len(self.input_nodes))),
            ("Generasi GA", str(self.current_generation)),
            ("Best Cost Network", f"{self.best_cost:.2f}"),
            ("Total Kluster", total_cluster_str)
        ]
        for i, (label, val) in enumerate(stats):
            y_pos = self.padding + 95 + (i * 22)
            self.screen.blit(self.font.render(label, True, TEXT_MUTED), (sidebar_x + 15, y_pos))
            self.screen.blit(self.font.render(val, True, TEXT_WHITE if label != "Application Mode" else BLUE_TEXT), (sidebar_x + 140, y_pos))

        # PANEL 2: Dynamic Controls based on current mode
        ctrl_rect = pygame.Rect(sidebar_x, self.padding + 245, self.sidebar_w, 240)
        self.draw_rounded_panel(ctrl_rect, BG_PANEL)
        self.screen.blit(self.header_font.render("Controls", True, TEXT_WHITE), (sidebar_x + 15, self.padding + 260))
        
        if self.mode == "PLANNING":
            controls_text = [
                "[Mous Klik]   Taruh / Hapus Kota",
                "[G]           Acak Posisi Kota (25 Node)", # Tambahkan ini
                "[ENTER]       Kunci & Build Map",
                "[R]           Reset Seluruh Node",
                "",
                "Petunjuk:",
                "Taruh kota manual ATAU pencet G",
                "untuk mengacak posisi kota,",
                "kemudian tekan ENTER."
            ]
        else:
            controls_text = [
                "[SPACE]       Pause / Resume GA",
                "[M]           Brush Mode: MACET",
                "[H]           Brush Mode: HANCUR",
                "[R]           Kembali ke Planning",
                "",
                "Kuas Aktif: " + self.brush_mode,
                "Klik-Drag kiri di grid kosong",
                "untuk pasang penalti macet."
            ]
            
        for i, line in enumerate(controls_text):
            y_pos = self.padding + 290 + (i * 20)
            color = BLUE_TEXT if line.startswith("[") else TEXT_MUTED
            if "Petunjuk" in line: color = TEXT_WHITE
            self.screen.blit(self.font.render(line, True, color), (sidebar_x + 15, y_pos))

    def build_simulation_world(self):
        """Membuat instance objek WorldBuilder dan World asli menggunakan koordinat kustom user"""
        if len(self.input_nodes) < 2:
            print("Taruh minimal 2 kota sebelum melakukan simulasi!")
            return
            
        USER_DE_PATH = 50.0
        # Panggil builder dengan input koordinat kustom
        self.builder = WorldBuilder(
            size=(self.grid_x_size, self.grid_y_size),
            num_nodes=len(self.input_nodes),
            random_nodes=False, # Matikan randomizer!
            de_path=USER_DE_PATH,
            inp=self.input_nodes # Overwrite pakai hasil klik user!
        )

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
        
        self.mode = "SIMULATION"
        print("World berhasil di-build! Masuk ke Simulation Mode.")

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
                
            elif event.type == pygame.KEYDOWN:
                if self.mode == "PLANNING":
                    if event.key == pygame.K_RETURN: # Tekan ENTER
                        self.build_simulation_world()
                    elif event.key == pygame.K_r:
                        self.input_nodes.clear()
                    elif event.key == pygame.K_g:
                        self.input_nodes.clear() # Bersihkan dulu input sebelumnya
                        import random
                        # Kumpulkan semua kemungkinan koordinat di grid
                        all_positions = [(i, j) for i in range(self.grid_x_size) for j in range(self.grid_y_size)]
                        # Ambil 25 koordinat acak yang unik (bisa kamu ganti jumlahnya sesuai kebutuhan)
                        jumlah_node_acak = min(25, len(all_positions))
                        self.input_nodes = random.sample(all_positions, jumlah_node_acak)
                
                elif self.mode == "SIMULATION":
                    if event.key == pygame.K_SPACE:
                        self.is_running = not self.is_running
                    elif event.key == pygame.K_m:
                        self.brush_mode = "MACET"
                    elif event.key == pygame.K_h:
                        self.brush_mode = "HANCUR"
                    elif event.key == pygame.K_r:
                        # Reset total balik ke fase gambar kota awal
                        self.mode = "PLANNING"
                        self.world = None
                        self.builder = None
                        self.current_generation = 0
                        self.best_cost = 0.0
                        self.is_running = False

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = pygame.mouse.get_pos()
                grid_start_y = self.padding + 50
                
                # Pastikan klik berada di dalam area grid
                if self.padding <= mx < self.padding + self.grid_w and grid_start_y <= my < grid_start_y + self.grid_h:
                    grid_x = (mx - self.padding) // self.cell_size
                    grid_y = (my - grid_start_y) // self.cell_size
                    coord = (grid_x, grid_y)
                    
                    if self.mode == "PLANNING":
                        if coord in self.input_nodes:
                            self.input_nodes.remove(coord) # Jika di-klik lagi, hapus kotanya
                        else:
                            self.input_nodes.append(coord) # Tambah kota baru
                            
            # Klik kiri ditahan & geser (Hanya berlaku di Simulation Mode untuk gambar macet)
            elif pygame.mouse.get_pressed()[0] and self.mode == "SIMULATION" and self.world:
                mx, my = pygame.mouse.get_pos()
                grid_start_y = self.padding + 50
                if self.padding <= mx < self.padding + self.grid_w and grid_start_y <= my < grid_start_y + self.grid_h:
                    grid_x = (mx - self.padding) // self.cell_size
                    grid_y = (my - grid_start_y) // self.cell_size
                    
                    if self.brush_mode == "MACET":
                        self.world.road_layers[grid_x][grid_y] = float('inf') # Set biaya jadi inf!
                    elif self.brush_mode == "HANCUR":
                        self.world.road_layers[grid_x][grid_y] = 0

    def run(self):
        while True:
            self.handle_events()
            self.screen.fill(BG_MAIN)
            
            # Judul
            title_surface = self.title_font.render("Genetic Algorithm Road Planner", True, TEXT_WHITE)
            self.screen.blit(title_surface, (self.padding, self.padding))
            
            # Logika Eksekusi GA saat Simulation Mode aktif
            if self.mode == "SIMULATION" and self.is_running and self.world:
                daftar_id_kota = list(self.world.node_pos.keys())
                daftar_rute = list(itertools.combinations(daftar_id_kota, 2))
                
                best_order, best_cost = run_genetic_algorithm(self.world, daftar_rute, pop_size=30, generations=20)
                evaluate_chromosome(best_order, self.world, daftar_rute)
                
                self.best_cost = best_cost
                self.current_generation = 20
                self.is_running = False 
            
            # Rendering
            self.draw_grid_area()
            self.draw_cities()
            self.draw_right_panels()
            
            pygame.display.flip()
            self.clock.tick(30)