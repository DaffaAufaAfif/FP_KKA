import itertools
from model import WorldBuilder, World
from ga import run_genetic_algorithm, evaluate_chromosome
from ui import cetak_peta_2d


def main():
    USER_DE_PATH = 50.0
    JUMLAH_NODE = 6

    builder = WorldBuilder(size=(10, 10), num_nodes=JUMLAH_NODE, random_nodes=True, de_path=USER_DE_PATH)

    my_world = World(
        x=builder.x,
        y=builder.y,
        node_positions=builder.node_positions,
        default_cost=builder.de_path,
        threshold=2,
        growth_rate=2.0,
        discount_factor=0.01,
    )

    print("Posisi Koordinat Kota yang Terbentuk:")
    for city_id, pos in my_world.node_pos.items():
        print(f"  Kota {city_id} -> {pos}")

    daftar_id_kota = list(my_world.node_pos.keys())
    daftar_rute = list(itertools.combinations(daftar_id_kota, 2))

    best_order, best_cost = run_genetic_algorithm(my_world, daftar_rute, pop_size=30, generations=20)

    evaluate_chromosome(best_order, my_world, daftar_rute)

    print("\n================ HASIL OPTIMASI GA ================")
    print(f"Urutan Indeks Pembuatan Rute Terbaik: {best_order}")
    print(f"Total Biaya Seluruh Jaringan Terpilih: {best_cost:.2f}")

    cetak_peta_2d(my_world)


if __name__ == "__main__":
    main()
