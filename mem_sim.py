from support_func import *
import binascii
import sys

FIFO_FLG = 0
LRU_FLG = 1
OPT_FLG = 2

FRAME_SIZE = 256
BYTE_SIZE = 8
TLB_SIZE = 16
PAGE_TABLE_SIZE = 256

DFLT_N_FRMAES = 256
LOADED = 1
NOT_LOADED = 0
EMPTY = -1
NOT_FOUND = -1

TLB_HIT_DATA = 0
PAGE_FAULT_DATA = 1

FRAME_NUM_POS = 1
PAGE_NUM_POS = 0
LOAD_POS = 0

alg_frame_table = []
alg_accessed_pages = []
alg_future_pages = []

PHYS_FULL_FLG = 0


def get_logical_addresses(filename: str):
    logical_addr_list = []
    with open(filename, "r") as file:
        lower_page_mask = 0xFF
        for line in file:
            address = int(line)
            offset = int(line) & lower_page_mask
            page_num = int(line) >> 8
            curr_addr = LogicalAddr(address, page_num, offset)
            logical_addr_list.append(curr_addr)
    return logical_addr_list


def find_page_num_in_tlb(page_num, tlb):
    for i in range(TLB_SIZE):
        if page_num == tlb[i][PAGE_NUM_POS]:
            return i
    return NOT_FOUND


def confirm_frame_num_in_page_table(page_num, page_table):
    if page_table[page_num][FRAME_NUM_POS] != EMPTY:
        return True
    else:
        return False


def find_addr_to_unload(page_table, frame_num):
    for i in range(PAGE_TABLE_SIZE):
        if page_table[i][FRAME_NUM_POS] == frame_num:
            return i
    return NOT_FOUND


def print_mem_data(addr, page_content, frame_num_tmp):
    byte_val = page_content[addr.offset]
    page_content_value = byte_val if byte_val < 128 else byte_val - 256
    page_content = binascii.hexlify(page_content).decode("utf-8")
    print(f"{addr.address}, {page_content_value}, {frame_num_tmp}, \n{page_content}")


def update_accessed_table(page_num):
    alg_accessed_pages.remove(page_num)
    alg_accessed_pages.append(page_num)


def get_fifo_idx(curr_idx, buf_size):
    if curr_idx == (buf_size - 1):
        res = curr_idx % (buf_size - 1)
    else:
        res = (curr_idx % (buf_size - 1)) + 1
    return res


def get_lru_idx(curr_idx, buf_size, page_num):
    if len(alg_frame_table) < buf_size:
        # Add only if table is not full
        alg_frame_table.append(page_num)
        alg_accessed_pages.append(page_num)
        return curr_idx + 1
    else:
        PHYS_FULL_FLG = 1
        # Find LRU
        alg_accessed_pages.append(page_num)
        rem_page = alg_accessed_pages.pop(0)
        for i in range(len(alg_frame_table)):
            if alg_frame_table[i] == rem_page:
                alg_frame_table[i] = page_num
                return i


#############################################
# @breif
# @params
# @return
#############################################
def get_opt_idx(curr_idx, buf_size, page_num):
    if len(alg_frame_table) < buf_size:
        # Add only if table is not full
        alg_frame_table.append(page_num)
        alg_future_pages.pop(0)
        return curr_idx + 1
    else:
        PHYS_FULL_FLG = 1
        # Find furthest away page to remove
        alg_future_pages.pop(0)
        rem_page = 0
        rem_page_limit = 0
        rem_page_accessed = set()
        found_rem_page = False
        for page in alg_future_pages:
            if rem_page_limit >= buf_size:
                break
            elif page in alg_frame_table:
                found_rem_page == True
                rem_page = page
                if page not in rem_page_accessed:
                    rem_page_accessed.add(page)
                    rem_page_limit += 1

        if found_rem_page == False:
            # set rem_page to first item in frame table if nothing else to replace
            rem_page = alg_frame_table[0]

        # Replace page in alg table
        for i in range(len(alg_frame_table)):
            if alg_frame_table[i] == rem_page:
                alg_frame_table[i] = page_num
                return i


def do_mem_sim(frame_space, n_frames, algo, logical_addr_list):
    # Init buffers, indices, counters
    tlb = [[EMPTY, EMPTY] for _ in range(TLB_SIZE)]
    page_table = [[NOT_LOADED, EMPTY] for _ in range(PAGE_TABLE_SIZE)]
    frame_num = 0
    tlb_idx = 0
    page_fault_cnt = 0
    tlb_hit_cnt = 0

    # Pupoluate future page number list if OPT
    if algo == OPT_FLG:
        for addr in logical_addr_list:
            alg_future_pages.append(addr.page_num)

    # Begin Simulation
    for addr in logical_addr_list:
        if find_page_num_in_tlb(addr.page_num, tlb) != NOT_FOUND:
            print("Found logical page num in tlb")
            found_tlb_idx = find_page_num_in_tlb(addr.page_num, tlb)
            frame_num_tmp = tlb[found_tlb_idx][FRAME_NUM_POS]
            page_content = frame_space[frame_num_tmp]
            tlb_hit_cnt += 1
            if algo == LRU_FLG:
                update_accessed_table(addr.page_num)
            elif algo == OPT_FLG:
                alg_future_pages.pop(0)
        else:
            if confirm_frame_num_in_page_table(addr.page_num, page_table) != False:
                if page_table[addr.page_num][LOAD_POS] == LOADED:
                    print("Found LOADED logical page num in page table")
                    frame_num_tmp = page_table[addr.page_num][FRAME_NUM_POS]
                    page_content = frame_space[frame_num_tmp]
                else:
                    print("Found UNLOADED logical page num in page table")
                    # Get already known frame_num
                    frame_num_tmp = page_table[addr.page_num][FRAME_NUM_POS]

                    # Get page content from bin file
                    byte_offset = addr.page_num * FRAME_SIZE
                    with open("BACKING_STORE.bin", "rb") as bin_file:
                        bin_file.seek(byte_offset)
                        page_content = bin_file.read(FRAME_SIZE)

                    # Insert new page content and unload old one
                    page_num_to_unload = find_addr_to_unload(page_table, frame_num_tmp)
                    page_table[page_num_to_unload][LOAD_POS] = NOT_LOADED
                    frame_space[frame_num_tmp] = page_content

                    # Update TLB using FIFO
                    tlb_idx_tmp = tlb_idx
                    tlb_idx = get_fifo_idx(tlb_idx, TLB_SIZE)
                    tlb[tlb_idx_tmp][PAGE_NUM_POS] = addr.page_num
                    tlb[tlb_idx_tmp][FRAME_NUM_POS] = frame_num_tmp

                    # Update page table to entry loaded
                    page_table[addr.page_num][LOAD_POS] = LOADED
            else:
                print("Page Fault Occured")
                # Increment page fault count
                page_fault_cnt += 1

                # Get page content from bin file
                byte_offset = addr.page_num * FRAME_SIZE
                with open("BACKING_STORE.bin", "rb") as bin_file:
                    bin_file.seek(byte_offset)
                    page_content = bin_file.read(FRAME_SIZE)

                # Get new frame_num based on algorithm
                frame_num_tmp = frame_num
                if algo == LRU_FLG:
                    frame_num = get_lru_idx(frame_num, n_frames, addr.page_num)
                    if PHYS_FULL_FLG == 1:
                        frame_num_tmp = frame_num

                elif algo == OPT_FLG:
                    frame_num = get_opt_idx(frame_num, n_frames, addr.page_num)
                    if PHYS_FULL_FLG == 1:
                        frame_num_tmp = frame_num
                else:
                    frame_num = get_fifo_idx(frame_num, n_frames)

                # Put page content into physical memory using updated index from algorithm
                if frame_space[frame_num_tmp] == EMPTY:
                    frame_space[frame_num_tmp] = page_content
                else:
                    # Reset entry in page table if physical memory is full
                    page_num_to_unload = find_addr_to_unload(page_table, frame_num_tmp)
                    page_table[page_num_to_unload][LOAD_POS] = NOT_LOADED
                    frame_space[frame_num_tmp] = page_content

                # Update TLB using FIFO
                tlb_idx_tmp = tlb_idx
                tlb_idx = get_fifo_idx(tlb_idx, TLB_SIZE)
                tlb[tlb_idx_tmp][PAGE_NUM_POS] = addr.page_num
                tlb[tlb_idx_tmp][FRAME_NUM_POS] = frame_num_tmp

                # Update page table by inserting frame number at index = page number
                # and set loaded bit because added into physical memory
                page_table[addr.page_num][FRAME_NUM_POS] = frame_num_tmp
                page_table[addr.page_num][LOAD_POS] = LOADED

        # Print Data
        print_mem_data(addr, page_content, frame_num_tmp)

        # print(f"ftable: {alg_frame_table} and access: {alg_future_pages}")  # debug
        # print("------------> ") # debug

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
    if algo.lower() == "lru":
        algo = LRU_FLG
    elif algo.lower() == "opt":
        algo = OPT_FLG
    elif algo.lower() == "fifo":
        algo = FIFO_FLG

    # Get page number and offset from local addresses
    addr_list = get_logical_addresses(filename)

    # Main function
    result = do_mem_sim(frame_space, n_frames, algo, addr_list)

    # Print results of simulation
    num_translated_addr = len(addr_list)
    num_page_faults = result[PAGE_FAULT_DATA]
    rate_page_faults = num_page_faults / num_translated_addr
    num_tlb_hits = result[TLB_HIT_DATA]
    num_tlb_misses = num_translated_addr - num_tlb_hits
    rate_tlb_hits = num_tlb_hits / num_translated_addr

    print(
        f"Number of Translated Addresses = {num_translated_addr}\n"
        f"Page Faults = {num_page_faults}\n"
        f"Page Fault Rate = {rate_page_faults}\n"
        f"TLB Hits = {num_tlb_hits}\n"
        f"TLB Misses = {num_tlb_misses}\n"
        f"TLB Hit Rate = {rate_tlb_hits}"
    )

    # for addr in addr_list:
    #     print(
    #         f"Address {addr.address}, Page Number {addr.page_num}, Offset {addr.offset} "
    #     )


if __name__ == "__main__":
    main()
