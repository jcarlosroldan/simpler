from requests import get
from simpler.format import seconds_to_human, bytes_to_human
from sys import stdout
from time import time
from threading import Thread
from urllib.open import urlopen

def download_file(url, path=None, chunk_size=10**5):
	''' Downloads a file keeping track of the progress. '''
	if path == None: path = url.split('/')[-1]
	r = get(url, stream=True)
	total_bytes = int(r.headers.get('content-length'))
	bytes_downloaded = 0
	start = time()
	print('Downloading %s (%s)' % (url, bytes_to_human(total_bytes)))
	with open(path, 'wb') as fp:
		for chunk in r.iter_content(chunk_size=chunk_size):
			if not chunk: continue
			fp.write(chunk)
			bytes_downloaded += len(chunk)
			percent = bytes_downloaded / total_bytes
			bar = ('█' * int(percent * 32)).ljust(32)
			time_delta = time() - start
			eta = seconds_to_human((total_bytes - bytes_downloaded) * time_delta / bytes_downloaded)
			avg_speed = bytes_to_human(bytes_downloaded / time_delta).rjust(9)
			stdout.flush()
			stdout.write('\r  %6.02f%% |%s| %s/s eta %s' % (100 * percent, bar, avg_speed, eta))
	print()

class DownloaderPool:

	def __init__(self, num_workers=100, download_method=urlopen):
		self.pending_urls = []
		self.responses = {}
		self.workers = [Thread(target=self.download_worker) for _ in range(num_workers)]
		self.download_method = download_method
		[w.start() for w in self.workers]

	def download_worker(self):
		while True:
			if len(self.pending_urls):
				url = self.pending_urls.pop()
				try:
					res = self.download_method(url, timeout=5).read()
				except:
					res = None
				self.responses[url] = res

	def get(self, urls):
		self.pending_urls.extend(urls)
		request_pending_urls = urls[:]
		while len(request_pending_urls):
			for url in request_pending_urls:
				if url in self.responses:
					break
			else:
				continue
			yield url, self.responses[url]
			del self.responses[url]