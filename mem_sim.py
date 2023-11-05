from logical_addr import *
import binascii
import struct
import sys

FIFO_FLG = 0
LRU_FLG = 1
OPT_FLG = 2
FRAME_SIZE = 256
BYTE_SIZE = 8
LOADED = 1
EMPTY = -1


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


def print_mem_data(addr, page_content, frame_num_tmp):
    byte_val = page_content[addr.offset]
    page_content_value = byte_val if byte_val < 128 else byte_val - 256
    page_content = binascii.hexlify(page_content).decode("utf-8")
    print(f"{addr.address}, {page_content_value}, {frame_num_tmp}, \n{page_content}")


def get_fifo_idx(frame_num, n_frames):
    if frame_num == (n_frames - 1):
        res = frame_num % (n_frames - 1)
    else:
        res = (frame_num % (n_frames - 1)) + 1
    return res


def do_mem_sim(frame_space, n_frames, logical_addr_list):
    # Init main bufferes and indeces
    tlb = {}
    page_table = [[0, 0] for _ in range(n_frames)]
    frame_num = 0

    # Begin Simulation
    for addr in logical_addr_list:
        if addr.page_num in tlb:
            print("found logical page num in tlb")
            frame_num_tmp = tlb.get(addr.page_num)
            page_content = frame_space[frame_num_tmp]

        else:
            if page_table[addr.page_num][1] == LOADED:
                print("found logical page num in page table")
                frame_num_tmp = page_table[addr.page_num][0]
                page_content = frame_space[frame_num_tmp]
            else:
                print("Page Fault Occured")

                # Get page content from bin file
                byte_offset = addr.page_num * FRAME_SIZE
                with open("BACKING_STORE.bin", "rb") as bin_file:
                    bin_file.seek(byte_offset)
                    page_content = bin_file.read(FRAME_SIZE)

                # Put page content into physical memory using updated index
                frame_num_tmp = frame_num
                frame_num = get_fifo_idx(frame_num, n_frames)
                if frame_space[frame_num_tmp] == EMPTY:
                    frame_space[frame_num_tmp] = page_content

                # Put page number and frame number (aka frame_num) into tlb
                tlb[addr.page_num] = frame_num_tmp

                # # Put frame number into page table at index = page number
                # # and set loaded bit because added into physical memory
                page_table[addr.page_num][0] = frame_num_tmp
                page_table[addr.page_num][1] = LOADED

        # Print Data
        print_mem_data(addr, page_content, frame_num_tmp)
    # print(tlb)
    # print(page_table)


def main():
    # Parse command line arguments
    if (len(sys.argv) < 2) or (len(sys.argv) > 4):
        print("Usage: python script.py")
        sys.exit(1)

    # Get arg 1
    filename = sys.argv[1]

    # Get arg 2
    n_frames = int(sys.argv[2]) if len(sys.argv) >= 3 else 256
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
    do_mem_sim(frame_space, n_frames, addr_list)

    # for addr in addr_list:
    #     print(
    #         f"Address {addr.address}, Page Number {addr.page_num}, Offset {addr.offset} "
    #     )


if __name__ == "__main__":
    main()
