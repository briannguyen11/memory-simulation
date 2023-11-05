from logical_addr import *
import binascii
import struct
import sys

FIFO_FLG = 0
LRU_FLG = 1
OPT_FLG = 2

FRAME_SIZE = 256
BYTE_SIZE = 8
TLB_SIZE = 16

DFLT_N_FRMAES = 256
LOADED = 1
EMPTY = -1

TLB_HIT_DATA = 0
PAGE_FAULT_DATA = 1

FRAME_NUM_POS = 1
PAGE_NUM_POS = 0
LOADED_POS = 0


def get_logical_addresses(filename: str):
    logical_addr_list = []
    with open(filename, "r") as file:
        lower_page_mask = 0xFF
        for line in file:
            address = int(line)
            offset = int(line) & lower_page_mask
            page_num = int(line) >> 8
            curr_addr = logical_addr(address, page_num, offset)
            logical_addr_list.append(curr_addr)
    return logical_addr_list


def find_page_num_in_tlb(page_num, tlb):
    for i in range(TLB_SIZE):
        if page_num == tlb[i][PAGE_NUM_POS]:
            return i
    return -1


def print_mem_data(addr, page_content, frame_num_tmp):
    byte_val = page_content[addr.offset]
    page_content_value = byte_val if byte_val < 128 else byte_val - 256
    page_content = binascii.hexlify(page_content).decode("utf-8")
    print(f"{addr.address}, {page_content_value}, {frame_num_tmp}, \n{page_content}")


def get_fifo_idx(curr_idx, table_size):
    if curr_idx == (table_size - 1):
        res = curr_idx % (table_size - 1)
    else:
        res = (curr_idx % (table_size - 1)) + 1
    return res


def get_lru_idx(curr_idx, table_size):
    print("in lru")


def get_opt_idx(curr_idx, table_size):
    print("in opt")


def do_mem_sim(frame_space, n_frames, algo, logical_addr_list):
    # Init main bufferes, indeces, counters
    tlb = [[0, 0] for _ in range(TLB_SIZE)]
    page_table = [[0, 0] for _ in range(n_frames)]
    frame_num = 0
    tlb_idx = 0
    page_fault_cnt = 0
    tlb_hit_cnt = 0

    # Begin Simulation
    for addr in logical_addr_list:
        if find_page_num_in_tlb(addr.page_num, tlb) != -1:
            print("found logical page num in tlb")
            found_tlb_idx = find_page_num_in_tlb(addr.page_num, tlb)
            frame_num_tmp = tlb[found_tlb_idx][FRAME_NUM_POS]
            page_content = frame_space[frame_num_tmp]
            tlb_hit_cnt += 1

        else:
            if page_table[addr.page_num][LOADED_POS] == LOADED:
                print("found logical page num in page table")
                frame_num_tmp = page_table[addr.page_num][FRAME_NUM_POS]
                page_content = frame_space[frame_num_tmp]
            else:
                print("Page Fault Occured")
                page_fault_cnt += 1

                # Get page content from bin file
                byte_offset = addr.page_num * FRAME_SIZE
                with open("BACKING_STORE.bin", "rb") as bin_file:
                    bin_file.seek(byte_offset)
                    page_content = bin_file.read(FRAME_SIZE)

                # Put page content into physical memory using updated index from algorithm
                frame_num_tmp = frame_num
                if algo == "lru":
                    frame_num = get_lru_idx(frame_num, n_frames)
                elif algo == "opt":
                    frame_num = get_opt_idx(frame_num, n_frames)
                else:
                    frame_num = get_fifo_idx(frame_num, n_frames)

                if frame_space[frame_num_tmp] == EMPTY:
                    frame_space[frame_num_tmp] = page_content

                # Put page number and frame number into tlb using FIFO
                tlb_idx_tmp = tlb_idx
                tlb_idx = get_fifo_idx(tlb_idx, TLB_SIZE)
                tlb[tlb_idx_tmp][PAGE_NUM_POS] = addr.page_num
                tlb[tlb_idx_tmp][FRAME_NUM_POS] = frame_num_tmp

                # # Put frame number into page table at index = page number
                # # and set loaded bit because added into physical memory
                page_table[addr.page_num][FRAME_NUM_POS] = frame_num_tmp
                page_table[addr.page_num][LOADED_POS] = LOADED

        # Print Data
        # print_mem_data(addr, page_content, frame_num_tmp)
    print(tlb)
    # print(page_table)
    return [tlb_hit_cnt, page_fault_cnt]


def main():
    # Parse command line arguments
    if (len(sys.argv) < 2) or (len(sys.argv) > 4):
        print("Usage: python script.py")
        sys.exit(1)

    # Get arg 1
    filename = sys.argv[1]

    # Get arg 2
    n_frames = int(sys.argv[2]) if len(sys.argv) >= 3 else DFLT_N_FRMAES
    frame_space = n_frames * FRAME_SIZE * [EMPTY]

    # Get arg 3:
    algo = sys.argv[3] if len(sys.argv) == 4 else "fifo"
    if algo.lower == "lru":
        algo = LRU_FLG
    elif algo.lower == "opt":
        algo = OPT_FLG
    else:
        algo = FIFO_FLG

    # Get page number and offset from local addresses
    addr_list = get_logical_addresses(filename)

    # Main function
    result = do_mem_sim(frame_space, n_frames, algo, addr_list)

    # Print results of simulation
    # num_translated_addr = len(addr_list)
    # num_page_faults = result[PAGE_FAULT_DATA]
    # rate_page_faults = num_page_faults / num_translated_addr
    # num_tlb_hits = result[TLB_HIT_DATA]
    # num_tlb_misses = num_translated_addr - num_tlb_hits
    # rate_tlb_hits = num_tlb_hits / num_translated_addr

    # print(
    #     f"Number of Translated Addresses = {num_translated_addr}\n"
    #     f"Page Faults = {num_page_faults}\n"
    #     f"Page Fault Rate = {rate_page_faults}\n"
    #     f"TLB Hits = {num_tlb_hits}\n"
    #     f"TLB Misses = {num_tlb_misses}\n"
    #     f"TLB Hit Rate = {rate_tlb_hits}"
    # )

    # for addr in addr_list:
    #     print(
    #         f"Address {addr.address}, Page Number {addr.page_num}, Offset {addr.offset} "
    #     )


if __name__ == "__main__":
    main()
