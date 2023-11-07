class LogicalAddr:
    def __init__(self, address: int, page_num: int, offset: int):
        # Instance attributes (unique to each instance)
        self.address = address
        self.page_num = page_num
        self.offset = offset


