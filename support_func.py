class LogicalAddr:
    def __init__(self, address: int, page_num: int, offset: int):
        # Instance attributes (unique to each instance)
        self.address = address
        self.page_num = page_num
        self.offset = offset


class LRUCache:
    def __init__(self, capacity):
        self.capacity = capacity
        self.phys_table = set()  # Stores the pages currently in physical memory
        self.usage_order = []  # Maintains the order of page usage

    def access_page(self, page):
        if page in self.phys_table:
            # Page is already in memory, move it to the most recently used position
            self.usage_order.remove(page)
            self.usage_order.append(page)
        else:
            # Page is not in memory, add it to memory
            if len(self.phys_table) >= self.capacity:
                # Memory is full, remove the least recently used page
                lru_page = self.usage_order[0]
                self.cache.remove(lru_page)
                self.usage_order.pop(0)
            self.cache.add(page)
            self.usage_order.append(page)
