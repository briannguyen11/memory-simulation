from logical_addr import *


def get_logical_addresses(filename: str):
    logical_addr_list = []
    with open(filename, "r") as file:
        lower_page_mask = 0xFF
        for line in file:
            offset = int(line) & lower_page_mask
            page_num = int(line) >> 8
            curr_addr = logical_addr(page_num, offset)
            logical_addr_list.append(curr_addr)
    return logical_addr_list


def find_frame_num(tlb, page_table, logical_addr_list):
    # once you have page number, look in tlb
    # if it is found in the tlb --> go straight to physical
    # if not found in tlb --> go to page table
    # if found in page talbe --> go straight to physical
    # if not found in page table --> pull from bin file and load into physical

    for addr in logical_addr_list:
        if addr in tlb:
            print("found logical in tlb")
        else:
            print("going into page table")
            if addr in page_table:
                print("found logical in page table")
            else:
                print("pull from bin file")


def main():
    tlb = {}
    page_table = {}

    addr_list = get_logical_addresses("addresses.txt")
    find_frame_num(tlb, page_table, addr_list)

    for addr in addr_list:
        print(f"Page Number {addr.page_num}, Offset {addr.offset} ")


if __name__ == "__main__":
    main()
