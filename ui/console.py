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


def main(argv=None):
    """Run the full program in console mode with defaults.

    Example:
      python -m ui.console
      python ui/console.py --nodes 20 --gens 10
    """
    import argparse
    import itertools
    import os
    import sys

    # Ensure project root (parent directory) is on sys.path so sibling packages
    # `model` and `ga` can be imported when running this file as a script
    pkg_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    if pkg_root not in sys.path:
        sys.path.insert(0, pkg_root)

    from model.world import WorldBuilder, World
    from ga.ga import run_genetic_algorithm, evaluate_chromosome

    parser = argparse.ArgumentParser(description="Run GA+A* in console mode and print results")
    parser.add_argument('--size', type=int, nargs=2, default=(15, 15), help='grid size (W H)')
    parser.add_argument('--nodes', type=int, default=25, help='number of nodes')
    parser.add_argument('--depath', type=float, default=50.0, help='default path cost')
    parser.add_argument('--pop', type=int, default=30, help='GA population size')
    parser.add_argument('--gens', type=int, default=20, help='GA generations')
    parser.add_argument('--threshold', type=int, default=2, help='traffic threshold for sharing')
    parser.add_argument('--seed', type=int, default=None, help='random seed')

    args = parser.parse_args(argv)

    if args.seed is not None:
        import random
        random.seed(args.seed)

    print("Membangun peta dan node...")
    builder = WorldBuilder(size=tuple(args.size), num_nodes=args.nodes, random_nodes=True, de_path=args.depath, inp=[])

    my_world = World(
        x=builder.x,
        y=builder.y,
        node_positions=builder.node_positions,
        pos_to_cluster=builder.pos_to_cluster,
        cluster_members=builder.cluster_members,
        default_cost=builder.de_path,
        threshold=args.threshold,
        growth_rate=2.0,
        discount_factor=0.01,
    )

    print("Posisi node:")
    for nid, pos in sorted(my_world.node_pos.items()):
        print(f"  Node {nid}: {pos}")

    daftar_id_kota = list(my_world.node_pos.keys())
    daftar_rute = list(itertools.combinations(daftar_id_kota, 2))

    print(f"Menjalankan GA (pop={args.pop}, gens={args.gens})...")
    best_order, best_cost = run_genetic_algorithm(my_world, daftar_rute, pop_size=args.pop, generations=args.gens)

    if best_order is None:
        print("GA tidak menghasilkan solusi.")
        return

    # Apply best solution to world state for visualization
    evaluate_chromosome(best_order, my_world, daftar_rute)

    print("\n================ HASIL OPTIMASI GA ================")
    print(f"Urutan Indeks Pembuatan Rute Terbaik: {best_order}")
    if best_cost == float('inf'):
        print("Solusi terbaik tidak terhubung sepenuhnya (infinite cost).")
    else:
        print(f"Total Biaya Seluruh Jaringan Terpilih: {best_cost:.2f}")

    cetak_peta_2d(my_world)


if __name__ == '__main__':
    main()
