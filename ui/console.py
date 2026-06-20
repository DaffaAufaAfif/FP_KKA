def cetak_peta_2d(world):
    """Print a simple ASCII visualization of the world grid with cluster info."""
    grid = [[" . " for _ in range(world.y)] for _ in range(world.x)]

    for x in range(world.x):
        for y in range(world.y):
            layers = world.road_layers[x][y]
            if layers > 0:
                if layers <= world.max_traf:
                    grid[x][y] = f" #{layers}"
                else:
                    grid[x][y] = f" {layers}!"

    # Mark nodes by their cluster id (C#) when available, otherwise by node id (K#)
    for city_id, (nx, ny) in world.node_pos.items():
        cid = world.pos_to_cluster.get((nx, ny))
        if cid is not None:
            grid[nx][ny] = f" C{cid}"
        else:
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
    
    # Print cluster info and connectivity components
    print("\n================== INFORMASI KLUSTER ==================")
    print(f"Total Kluster: {len(world.cluster_members)}")
    for cluster_id, members in sorted(world.cluster_members.items()):
        connected = "✓ CONNECTED" if cluster_id in world.connected_clusters else "✗ NOT CONNECTED"
        print(f"  Kluster {cluster_id} {connected}: Nodes {sorted(members)}")

    # show connected components (flood-fill over cluster graph)
    try:
        components = world.get_cluster_components()
        print("\nCluster Components (connected groups):")
        for i, comp in enumerate(components, start=1):
            status = "CONNECTED" if len(comp) > 1 else "SINGLETON"
            print(f"  Component {i} ({status}): Clusters {sorted(comp)}")
    except Exception:
        print("  (No cluster graph available)")

    print("==========================================================")
