# A simplified benchmark suite for testing purposes.

from xenon.tests.datatypes import *

aes_aes = Benchmark("aes-aes")
aes_aes.add_array("ctx", 96, 1)
aes_aes.add_array("k", 32, 1)
aes_aes.add_array("buf", 16, 1)
aes_aes.add_array("rcon", 1, 1)
aes_aes.add_array("sbox", 256, 1)
aes_aes.add_loop("aes_addRoundKey_cpy", "cpkey")
aes_aes.add_loop("aes_subBytes", "sub")
aes_aes.add_loop("aes_addRoundKey", "addkey")
aes_aes.add_loop("aes256_encrypt_ecb", "ecb1")
aes_aes.add_loop("aes256_encrypt_ecb", "ecb2")
aes_aes.add_loop("aes256_encrypt_ecb", "ecb3")

bfs_bulk = Benchmark("bfs-bulk")
bfs_bulk.add_array("nodes", 512, 8)
bfs_bulk.add_array("edges", 4096, 8)
bfs_bulk.add_array("level", 256, 1)
bfs_bulk.add_array("level_counts", 10, 8)
bfs_bulk.add_loop("bfs", "loop_horizons")
bfs_bulk.add_loop("bfs", "loop_nodes")
bfs_bulk.add_loop("bfs", "loop_neighbors")
