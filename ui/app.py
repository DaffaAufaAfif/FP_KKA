# ui/simulator_app.py
import pygame
import sys
from ga.ga import run_genetic_algorithm, evaluate_chromosome
import itertools

# Palette Warna Semacam Referensi (Dark Theme)
BG_MAIN = (21, 26, 35)          # Latar belakang utama aplikasi
BG_PANEL = (30, 38, 50)         # Latar belakang grid dan panel kanan
GRID_LINE = (45, 55, 72)        # Garis grid tipis
TEXT_WHITE = (230, 235, 245)    # Teks utama
TEXT_MUTED = (140, 150, 170)    # Teks sekunder / petunjuk

# Warna Elemen Jalan/Kota
ROAD_EMPTY = (30, 38, 50)       # Sama dengan BG_PANEL jika ingin menyatu, atau buat sedikit beda
ROAD_SHARING = (52, 211, 153)   # Hijau neon estetik untuk jalan normal
ROAD_CONGESTED = (248, 113, 113)# Merah pastel untuk jalan macet

class SimulationUI:
    def __init__(self, world_instance, builder_instance, cell_size=32):
        pygame.init()
        self.world = world_instance
        self.builder = builder_instance
        self.cell_size = cell_size
        
        # Hitung dimensi layout
        self.grid_w = self.builder.x * self.cell_size
        self.grid_h = self.builder.y * self.cell_size
        
        self.padding = 20
        self.sidebar_w = 260
        
        # Ukuran Window Utama
        self.window_w = self.grid_w + (self.padding * 3) + self.sidebar_w
        self.window_h = max(self.grid_h + (self.padding * 2), 520)
        
        self.screen = pygame.display.set_mode((self.window_w, self.window_h))
        pygame.display.set_caption("OpenStreetMap A* & GA Road Planner Simulation")
        self.clock = pygame.time.Clock()
        
        # Fonts
        self.title_font = pygame.font.SysFont("Segoe UI", 24, bold=True)
        self.header_font = pygame.font.SysFont("Segoe UI", 18, bold=True)
        self.font = pygame.font.SysFont("Segoe UI", 14)
        
        # Simulation States
        self.brush_mode = "MACET"
        self.is_running = False
        self.current_generation = 0
        self.best_cost = 0.0

    def draw_rounded_panel(self, rect, color, radius=8):
        """Menggambar panel dengan sudut melengkung mirip CSS/Modern UI"""
        pygame.draw.rect(self.screen, color, rect, border_radius=radius)

    def draw_grid_area(self):
        # Definisikan rect area grid
        grid_rect = pygame.Rect(self.padding, self.padding + 50, self.grid_w, self.grid_h)
        self.draw_rounded_panel(grid_rect, BG_PANEL)
        
        # Gambar sel-sel di dalam grid
        for x in range(self.builder.x):
            for y in range(self.builder.y):
                cell_rect = pygame.Rect(
                    self.padding + (x * self.cell_size),
                    self.padding + 50 + (y * self.cell_size),
                    self.cell_size,
                    self.cell_size
                )
                
                # Cek isi lapisan jalan
                layers = self.world.road_layers[x][y]
                if layers > 0:
                    if layers <= self.world.max_traf:
                        pygame.draw.rect(self.screen, ROAD_SHARING, cell_rect)
                    else:
                        pygame.draw.rect(self.screen, ROAD_CONGESTED, cell_rect)
                
                # Gambar outline grid tipis
                pygame.draw.rect(self.screen, GRID_LINE, cell_rect, 1)

    def draw_cities(self):
        # Gambar titik kota di atas grid
        for city_id, (cx, cy) in self.world.node_pos.items():
            center_x = self.padding + (cx * self.cell_size) + (self.cell_size // 2)
            center_y = self.padding + 50 + (cy * self.cell_size) + (self.cell_size // 2)
            
            # Pewarnaan berbasis kluster dari console.py
            cid = self.world.pos_to_cluster.get((cx, cy))
            if cid is not None:
                city_color = ((cid * 75) % 200 + 50, (cid * 130) % 200 + 50, 230)
            else:
                city_color = (251, 191, 36)  # Kuning amber seperti pin di gambar referensi
                
            pygame.draw.circle(self.screen, city_color, (center_x, center_y), self.cell_size // 3)

    def draw_right_panels(self):
        sidebar_x = self.grid_w + (self.padding * 2)
        
        # 1. PANEL ATAS: Simulation Info
        info_rect = pygame.Rect(sidebar_x, self.padding + 50, self.sidebar_w, 180)
        self.draw_rounded_panel(info_rect, BG_PANEL)
        
        self.screen.blit(self.header_font.render("Simulation", True, TEXT_WHITE), (sidebar_x + 15, self.padding + 65))
        
        stats = [
            ("Status", "RUNNING" if self.is_running else "PAUSED"),
            ("Generasi GA", str(self.current_generation)),
            ("Best Cost Network", f"{self.best_cost:.2f}"),
            ("Total Kluster", str(len(self.world.cluster_members))),
            ("Brush Mode Active", self.brush_mode)
        ]
        
        for i, (label, val) in enumerate(stats):
            y_pos = self.padding + 95 + (i * 22)
            self.screen.blit(self.font.render(label, True, TEXT_MUTED), (sidebar_x + 15, y_pos))
            self.screen.blit(self.font.render(val, True, TEXT_WHITE), (sidebar_x + 160, y_pos))

        # 2. PANEL BAWAH: Controls
        ctrl_rect = pygame.Rect(sidebar_x, self.padding + 50 + 195, self.sidebar_w, 200)
        self.draw_rounded_panel(ctrl_rect, BG_PANEL)
        
        self.screen.blit(self.header_font.render("Controls", True, TEXT_WHITE), (sidebar_x + 15, self.padding + 260))
        
        controls_text = [
            "[SPACE]   Pause / Resume",
            "[M]            Mode Brush Macet",
            "[H]             Mode Brush Hancur",
            "[R]             Reset Simulation",
            "Left Click Drag pada Grid",
            "untuk memakai kuas brush."
        ]
        
        for i, line in enumerate(controls_text):
            y_pos = self.padding + 290 + (i * 20)
            color = TEXT_WHITE if line.startswith("[") else TEXT_MUTED
            self.screen.blit(self.font.render(line, True, color), (sidebar_x + 15, y_pos))

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
                
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    self.is_running = not self.is_running
                elif event.key == pygame.K_m:
                    self.brush_mode = "MACET"
                elif event.key == pygame.K_h:
                    self.brush_mode = "HANCUR"
                elif event.key == pygame.K_r:
                    self.world.reset_world()
                    self.current_generation = 0
                    self.best_cost = 0.0
                    self.is_running = False
                    
            elif pygame.mouse.get_pressed()[0]:
                mx, my = pygame.mouse.get_pos()
                # Cek apakah koordinat mouse berada di dalam batas area grid
                grid_start_y = self.padding + 50
                if self.padding <= mx < self.padding + self.grid_w and grid_start_y <= my < grid_start_y + self.grid_h:
                    grid_x = (mx - self.padding) // self.cell_size
                    grid_y = (my - grid_start_y) // self.cell_size
                    
                    if self.brush_mode == "MACET":
                        self.world.road_layers[grid_x][grid_y] = 5
                    elif self.brush_mode == "HANCUR":
                        self.world.road_layers[grid_x][grid_y] = 0

    def run(self):
        while True:
            self.handle_events()
            self.screen.fill(BG_MAIN)
            
            # Teks Judul Utama di Atas
            title_surface = self.title_font.render("Genetic Algorithm Road Planner", True, TEXT_WHITE)
            self.screen.blit(title_surface, (self.padding, self.padding))
            
            if self.is_running:
                # 1. Siapkan daftar kombinasi rute antar kota seperti di runner.py
                daftar_id_kota = list(self.world.node_pos.keys())
                daftar_rute = list(itertools.combinations(daftar_id_kota, 2))
                
                # 2. Jalankan algoritma GA temanmu
                best_order, best_cost = run_genetic_algorithm(self.world, daftar_rute, pop_size=30, generations=20)
                
                # 3. Plot rute terbaik tersebut ke dalam matriks jalan (road_layers) agar tergambar
                evaluate_chromosome(best_order, self.world, daftar_rute)
                
                # 4. Update data ke panel informasi panel kanan
                self.best_cost = best_cost
                self.current_generation = 20 # Sesuai parameter generasi yang dijalankan
                
                # Selesai pengerjaan, otomatis pause agar tidak looping terus menerus
                self.is_running = False
            
            # Draw All Components
            self.draw_grid_area()
            self.draw_cities()
            self.draw_right_panels()
            
            pygame.display.flip()
            self.clock.tick(30)