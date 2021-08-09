from requests import get
from simpler.format import human_seconds, human_bytes
from sys import stdout
from time import time, sleep
from threading import Thread
from traceback import print_exc
from urllib.request import urlopen

def download_file(url, path=None, chunk_size=10**5):
	''' Downloads a file keeping track of the progress. Returns the output path. '''
	if path is None: path = url.split('/')[-1]
	r = get(url, stream=True)
	total_bytes = int(r.headers.get('content-length'))
	bytes_downloaded = 0
	start = time()
	print('Downloading %s (%s)' % (url, human_bytes(total_bytes)))
	with open(path, 'wb') as fp:
		for chunk in r.iter_content(chunk_size=chunk_size):
			if not chunk: continue
			fp.write(chunk)
			bytes_downloaded += len(chunk)
			percent = bytes_downloaded / total_bytes
			bar = ('█' * int(percent * 32)).ljust(32)
			time_delta = time() - start
			eta = human_seconds((total_bytes - bytes_downloaded) * time_delta / bytes_downloaded)
			avg_speed = human_bytes(bytes_downloaded / time_delta).rjust(9)
			stdout.flush()
			stdout.write('\r  %6.02f%% |%s| %s/s eta %s' % (100 * percent, bar, avg_speed, eta))
	print()
	return path

class DownloaderPool:

	def __init__(self, num_workers=100, download_method=lambda url: urlopen(url, timeout=5).read()):
		self.num_workers = num_workers
		self.pending_urls = []
		self.responses = {}
		self.workers = None
		self.download_method = download_method

	def spawn_workers(self):
		self.workers = [Thread(target=self.download_worker) for _ in range(self.num_workers)]
		[w.start() for w in self.workers]

	def download_worker(self):
		while len(self.pending_urls):
			url = self.pending_urls.pop()
			try:
				res = self.download_method(url)
			except:
				print_exc()
				res = None
			self.responses[url] = res

	def get(self, urls):
		self.pending_urls.extend(urls)
		request_pending_urls = urls[:]
		self.spawn_workers()
		while len(request_pending_urls):
			for url in request_pending_urls:
				if url in self.responses:
					break
			else:
				continue
			yield url, self.responses[url]
			del self.responses[url]
			request_pending_urls.remove(url)

_throttle_last = 0
def throttle(seconds: float = 1) -> None:
	''' Sleeps the thread so that the function is called every X seconds. '''
	global _throttle_last
	now = time()
	remaining = _throttle_last + seconds - now
	if remaining > 0:
		sleep(remaining)
		_throttle_last += seconds
	else:
		_throttle_last = now