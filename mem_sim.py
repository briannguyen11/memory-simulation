from support_func import *
import binascii
import sys

FIFO_FLG = 0
LRU_FLG = 1
OPT_FLG = 2

FRAME_SIZE = 256
BYTE_SIZE = 8
TLB_SIZE = 4  # debug
PAGE_TABLE_SIZE = 256

DFLT_N_FRMAES = 256
LOADED = 1
NOT_LOADED = 0
EMPTY = -1


TLB_HIT_DATA = 0
PAGE_FAULT_DATA = 1

FRAME_NUM_POS = 1
PAGE_NUM_POS = 0
LOAD_POS = 0

alg_frame_table = []
alg_accessed_pages = []
alg_future_pages = []

frame_full_flg = False

#############################################
# @brief: Sets a flag if all frames have been
#         filled in a frame table to signify 
#         when to start using algo-generated
#         frame numbers within LRU and OPT
# @params: new_value (boolean)
# @return: void
#############################################
def set_full_flg(new_value):
    global frame_full_flg
    frame_full_flg = new_value


#############################################
# @brief: Checks if a byte is equal to zero
# @params: item (list of bytes)
# @return: boolean
#############################################
def is_all_zeros(item):
    for byte in item:
        if byte != 0:
            return False
    return True


#############################################
# @brief: Separates logical addresses into
#         offsets and page numbers and stores
#         this info in a list of LogicalAddr 
#         objects
# @params: filename
# @return: list of LogicalAddr objects
#############################################
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


#############################################
# @brief: Finds location of a page in TLB
# @params: page_num, tlb
# @return: int i (index in TLB)
#############################################
def find_page_num_in_tlb(page_num, tlb):
    for i in range(TLB_SIZE):
        if page_num == tlb[i][PAGE_NUM_POS]:
            return i
    return -1


#############################################
# @brief: Finds page number of frame to be 
#         unloaded during page replacement
# @params: page_table, frame_num
# @return: int i (page number)
#############################################
def find_page_to_unload(page_table, frame_num):
    for i in range(PAGE_TABLE_SIZE):
        if page_table[i][FRAME_NUM_POS] == frame_num:
            return i
    return -1


#############################################
# @brief: Loads frame content if frame is 
#         empty, unloads page in frame to be
#         replaced, and loads new page into
#         frame. Sets page to loaded in page 
#         table and adds corresponding frame #
# @params: frame_space, frame_num, page_table, page_num, page_content
# @return: void
#############################################
def update_page_table_and_frame(frame_space, frame_num, page_table, page_num, page_content):
    if is_all_zeros(frame_space[frame_num]):
        # put page content in physical frame if empty
        frame_space[frame_num] = page_content
    else:
        # unload page number associated with occupied frame and put in new page content
        page_num_to_unload = find_page_to_unload(page_table, frame_num)
        print(f"UNLOADING {page_num_to_unload}")
        page_table[page_num_to_unload][FRAME_NUM_POS] = EMPTY
        page_table[page_num_to_unload][LOAD_POS] = NOT_LOADED
        frame_space[frame_num] = page_content
    
    # update page_table
    page_table[page_num][FRAME_NUM_POS] = frame_num
    page_table[page_num][LOAD_POS] = LOADED


#############################################
# @brief: Prints logical address, bin memory
#         value, frame number, and byte 
#         content of loaded page
# @params: addr, page_content, frame_num_tmp
# @return: void
#############################################
def print_mem_data(addr, page_content, frame_num_tmp):
    byte_val = page_content[addr.offset]
    page_content_value = byte_val if byte_val < 128 else byte_val - 256
    page_content = binascii.hexlify(page_content).decode("utf-8")
    print(f"{addr.address}, {page_content_value}, {frame_num_tmp}, \n{page_content}")


#############################################
# @brief: Determines frame that should have its
#         page swapped during a page fault when
#         FIFO algo is used
# @params: curr_idx, buf_size
# @return: int res (frame index)
#############################################
def get_fifo_idx(curr_idx, buf_size):
    if curr_idx == (buf_size - 1):
        res = curr_idx % (buf_size - 1)
    else:
        res = (curr_idx % (buf_size - 1)) + 1
    return res


#############################################
# @brief: Determines frame that should have its
#         page swapped during a page fault when
#         LRU algo is used
# @params: curr_idx, buf_size, page_num
# @return: int i (frame index)
#############################################
def get_lru_idx(curr_idx, buf_size, page_num):
    if len(alg_frame_table) < buf_size:
        # Add only if table is not full
        alg_frame_table.append(page_num)
        alg_accessed_pages.append(page_num)
        return curr_idx + 1
    else:
        set_full_flg(True)
        # Find LRU
        alg_accessed_pages.append(page_num)
        rem_page = alg_accessed_pages.pop(0)
        for i in range(len(alg_frame_table)):
            if alg_frame_table[i] == rem_page:
                alg_frame_table[i] = page_num
                return i


#############################################
# @brief: Determines frame that should have its
#         page swapped during a page fault when
#         OPT algo is used
# @params: curr_idx, buf_size, page_num
# @return: int i (frame index)
#############################################
def get_opt_idx(curr_idx, buf_size, page_num):
    if len(alg_frame_table) < buf_size:
        # Add only if table is not full
        alg_frame_table.append(page_num)
        alg_future_pages.pop(0)
        return curr_idx + 1
    else:
        set_full_flg(True)
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
                found_rem_page = True
                rem_page = page
                if page not in rem_page_accessed:
                    rem_page_accessed.add(page)
                    rem_page_limit += 1
        print(f"flag {found_rem_page}, rem page: {rem_page}")
        if found_rem_page == False:
            # set rem_page to first item in frame table if nothing else to replace
            rem_page = alg_frame_table[0]

        # Replace page in alg table
        for i in range(len(alg_frame_table)):
            if alg_frame_table[i] == rem_page:
                alg_frame_table[i] = page_num
                return i

#############################################
# @brief: Runs through all logical addresses,
#         adding to the tlb and page table if
#         not already there, and running the
#         inputted PRA when there are less 
#         frames than logical addresses
# @params: frame_space, n_frames, algo, 
#          logical_addr_list
# @return: tlb_hit_cnt, page_fault_cnt
#############################################
def do_mem_sim(frame_space, n_frames, algo, logical_addr_list):
    # Init buffers, indices, counters
    tlb = [[EMPTY, EMPTY] for _ in range(TLB_SIZE)]
    page_table = [[NOT_LOADED, EMPTY] for _ in range(PAGE_TABLE_SIZE)]
    frame_num = 0
    tlb_idx = 0
    page_fault_cnt = 0
    tlb_hit_cnt = 0
        
    # Begin Simulation
    for addr in logical_addr_list:
        if find_page_num_in_tlb(addr.page_num, tlb) != -1:
            # Get already known frame_num
            found_tlb_idx = find_page_num_in_tlb(addr.page_num, tlb)
            # Check is it actully loaded
            if page_table[addr.page_num][LOAD_POS] == LOADED:
                print("Found LOADED logical page num in tlb")
                tlb_hit_cnt += 1
                frame_num_tmp = tlb[found_tlb_idx][FRAME_NUM_POS]
                page_content = frame_space[frame_num_tmp]

                if algo == LRU_FLG:
                    alg_accessed_pages.remove(addr.page_num)
                    alg_accessed_pages.append(addr.page_num)
                elif algo == OPT_FLG:
                    alg_future_pages.pop(0)
            else:
                print("Found UNLOADED logical page num in tlb")
                page_fault_cnt += 1

                # Get page content from bin file
                byte_offset = addr.page_num * FRAME_SIZE
                with open("BACKING_STORE.bin", "rb") as bin_file:
                    bin_file.seek(byte_offset)
                    page_content = bin_file.read(FRAME_SIZE)

                # Get new frame_num to unload/insert into physical
                if algo == LRU_FLG:
                    frame_num_tmp = get_lru_idx(frame_num_tmp, n_frames, addr.page_num)
                elif algo == OPT_FLG:
                    frame_num_tmp = get_opt_idx(frame_num_tmp, n_frames, addr.page_num)
                elif algo == FIFO_FLG:
                    frame_num_tmp = frame_num
                    frame_num = get_fifo_idx(frame_num, n_frames)

                # Update page table and physical frames
                update_page_table_and_frame(frame_space, frame_num_tmp, page_table, addr.page_num, page_content)

                # Update TLB frame_num associated with found page_num
                tlb[found_tlb_idx][FRAME_NUM_POS] = frame_num_tmp

        else:
            if page_table[addr.page_num][LOAD_POS] == LOADED:
                print("Found LOADED logical page num in page table")
                frame_num_tmp = page_table[addr.page_num][FRAME_NUM_POS]
                page_content = frame_space[frame_num_tmp]

                # Insert into TLB using FIFO
                tlb_idx_tmp = tlb_idx
                tlb_idx = get_fifo_idx(tlb_idx, TLB_SIZE)
                tlb[tlb_idx_tmp][PAGE_NUM_POS] = addr.page_num
                tlb[tlb_idx_tmp][FRAME_NUM_POS] = frame_num_tmp
            else:
                print("Page Fault Occured")
                # Increment page fault count
                page_fault_cnt += 1

                # Get page content from bin file
                byte_offset = addr.page_num * FRAME_SIZE
                with open("BACKING_STORE.bin", "rb") as bin_file:
                    bin_file.seek(byte_offset)
                    page_content = bin_file.read(FRAME_SIZE)

                # Get new frame_num to unload/insert into physical
                frame_num_tmp = frame_num
                if algo == LRU_FLG:
                    frame_num = get_lru_idx(frame_num, n_frames, addr.page_num)
                    if frame_full_flg == True:
                        frame_num_tmp = frame_num
                elif algo == OPT_FLG:
                    frame_num = get_opt_idx(frame_num, n_frames, addr.page_num)
                    if frame_full_flg == True:
                        frame_num_tmp = frame_num
                elif algo == FIFO_FLG:
                    frame_num = get_fifo_idx(frame_num, n_frames)

                # Update page table and physical frames
                update_page_table_and_frame(frame_space, frame_num_tmp, page_table, addr.page_num, page_content)

                # Update TLB using FIFO
                tlb_idx_tmp = tlb_idx
                tlb_idx = get_fifo_idx(tlb_idx, TLB_SIZE)
                tlb[tlb_idx_tmp][PAGE_NUM_POS] = addr.page_num
                tlb[tlb_idx_tmp][FRAME_NUM_POS] = frame_num_tmp
                

        # Print Data
        # print_mem_data(addr, page_content, frame_num_tmp)
        print(f"lru ftable: {alg_frame_table} and access: {alg_accessed_pages}")  # debug
        print(f"opt ftable: {alg_frame_table} and future: {alg_future_pages}")  # debug
        print(f"page addr: {addr.page_num} and pg fault cnt: {page_fault_cnt}")
        print(tlb)
        print("------------> ")  # debug
    return [tlb_hit_cnt, page_fault_cnt]

#############################################
# @brief: Reads in addresses to translate, runs
#         through every address and stores 
#         appropriately in physical memory,
#         then prints simulation statistics
# @params: void (uses command line args)
# @return: void
#############################################
def main():
    # Parse command line arguments
    if (len(sys.argv) < 2) or (len(sys.argv) > 4):
        print("Usage: python script.py")
        sys.exit(1)

    # Get arg 1
    filename = sys.argv[1]
    addr_list = get_logical_addresses(filename)

    # Get arg 2
    n_frames = int(sys.argv[2]) if len(sys.argv) >= 3 else DFLT_N_FRMAES
    frame_space = [bytearray(FRAME_SIZE) for _ in range(n_frames)]

    # Get arg 3:
    algo = sys.argv[3] if len(sys.argv) == 4 else "fifo"
    if algo.lower() == "lru":
        algo = LRU_FLG
    elif algo.lower() == "opt":
        algo = OPT_FLG
        for addr in addr_list:
            alg_future_pages.append(addr.page_num)
    elif algo.lower() == "fifo":
        algo = FIFO_FLG

    
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

if __name__ == "__main__":
    main()
