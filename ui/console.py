def cetak_peta_2d(world):
    """Print a simple ASCII visualization of the world grid."""
    grid = [[" . " for _ in range(world.y)] for _ in range(world.x)]

    for x in range(world.x):
        for y in range(world.y):
            layers = world.road_layers[x][y]
            if layers > 0:
                if layers <= world.max_traf:
                    grid[x][y] = f" #{layers}"
                else:
                    grid[x][y] = f" {layers}!"

    for city_id, (nx, ny) in world.node_pos.items():
        grid[nx][ny] = f" K{city_id}"

    print("\n================== VISUALISASI PETA 2D ==================")
    print("Keterangan Simbol:")
    print("  K1, K2... = Posisi Kota/Node")
    print("  #1, #2    = Rute Jalan Bersama (Aman / Dapat Diskon Sharing Path)")
    print("  2!, 3!    = Jalan Macet Parah (Kena Penalti Eksponensial)")
    print("  .         = Area Kosong / Lahan Kosong\n")

    print("    " + "".join(f" {y:02d}" for y in range(world.y)))
    print("    " + "---" * world.y)

    for x in range(world.x):
        baris_teks = f"{x:02d} |"
        for y in range(world.y):
            baris_teks += grid[x][y]
        print(baris_teks)
    print("=========================================================")
