class Pagination:
	def __init__(self, page: int, per_page: int, total: int):
		self.page = page
		self.per_page = per_page
		self.total = total
		self.pages = (total - 1) // per_page + 1 if total > 0 else 0
		self.has_prev = page > 1
		self.has_next = page < self.pages
		self.prev_num = page - 1 if self.has_prev else None
		self.next_num = page + 1 if self.has_next else None

	def iter_pages(self):
		start = max(1, self.page - 2)
		end = min(self.pages + 1, self.page + 3)
		return range(start, end)


