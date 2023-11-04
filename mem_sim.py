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


def main():
    tlb = {}
    page_table = {}

    addr_list = get_logical_addresses("addresses.txt")

    for addr in addr_list:
        print(f"Page Number {addr.page_num}, Offset {addr.offset} ")
    # once you have page number, look in tlb
    # if it is found in the tlb --> go straight to physical
    # if not found in tlb --> go to page table
    # if found in page talbe --> go straight to physical
    # if not found in page table --> pull from bin file and load into physical


if __name__ == "__main__":
    main()
