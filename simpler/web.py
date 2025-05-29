from typing import Dict, Optional, Tuple, Union, List
import threading

def download_file(url, path=None, chunk_size=10**5, show_progress=True) -> str:
	''' Downloads a file keeping track of the progress. Returns the output path. '''
	from requests import get
	from simpler.format import human_seconds, human_bytes
	from sys import stdout
	from time import time
	if path is None: path = url.split('/')[-1]
	r = get(url, stream=True)
	total_bytes = int(r.headers.get('content-length', 0))
	bytes_downloaded = 0
	start = time()
	if show_progress: print('Downloading %s (%s)' % (url, human_bytes(total_bytes)))
	with open(path, 'wb') as fp:
		for chunk in r.iter_content(chunk_size=chunk_size):
			if not chunk: continue
			fp.write(chunk)
			if show_progress and total_bytes > 0:
				bytes_downloaded += len(chunk)
				percent = bytes_downloaded / total_bytes
				bar = ('█' * int(percent * 32)).ljust(32)
				time_delta = time() - start
				eta = human_seconds((total_bytes - bytes_downloaded) * time_delta / bytes_downloaded)
				avg_speed = human_bytes(bytes_downloaded / time_delta).rjust(9)
				stdout.flush()
				stdout.write('\r  %6.02f%% |%s| %s/s eta %s' % (100 * percent, bar, avg_speed, eta))
	if show_progress: print()
	return path

class DownloaderPool:

	def __init__(self, num_workers=100, download_method=None):
		self.num_workers = num_workers
		self.pending_urls = []
		self.responses = {}
		self.workers = None
		self.lock = threading.Lock()
		if download_method is None:
			from urllib.request import urlopen
			self.download_method = lambda url: urlopen(url, timeout=5).read()
		else:
			self.download_method = download_method

	def spawn_workers(self):
		from threading import Thread
		self.workers = [Thread(target=self.download_worker) for _ in range(self.num_workers)]
		[w.start() for w in self.workers]

	def download_worker(self):
		from traceback import print_exc
		while True:
			with self.lock:
				if not self.pending_urls:
					break
				url = self.pending_urls.pop()
			try:
				res = self.download_method(url)
			except:
				print_exc()
				res = None
			with self.lock:
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
	from time import sleep, time
	now = time()
	remaining = _throttle_last + seconds - now
	if remaining > 0:
		sleep(remaining)
		_throttle_last += seconds
	else:
		_throttle_last = now

class Driver:

	_CONSOLE_LEVELS = 'debug', 'info', 'log', 'warn', 'error'
	_YEAR_SECONDS = 365.4 * 24 * 3600
	_WAIT_POLL_EACH = .1

	def __init__(
		self, timeout: int = 3, keystroke_delay: int = .005, headless: bool = True, disable_flash: bool = True,
		disable_images: bool = True, language: str = 'en-US, en', options: Dict[str, str] = None
	):
		from autoselenium import Firefox
		from selenium.webdriver.firefox.options import Options
		opts = Options()
		opts.set_preference('intl.accept_languages', language)
		if options is not None:
			[opts.set_preference(k, v) for k, v in options.items()]
		self.driver = Firefox(headless=headless, disable_flash=disable_flash, disable_images=disable_images, options=opts)
		self.timeout = timeout
		self.keystroke_delay = keystroke_delay

	def browse(self, path: str):
		from selenium.webdriver.support.ui import WebDriverWait
		self.driver.get(path)
		WebDriverWait(self.driver, self.timeout).until(lambda d: d.execute_script('return document.readyState') == 'complete')
		self.driver.execute_script('window.CONSOLE_MESSAGES = [];%s' % ';'.join(
			'console.%s = (m) => CONSOLE_MESSAGES.push([\'%s\', m])' % (level, level)
			for level in self._CONSOLE_LEVELS
		))

	def wait(self, element: str, message: str = None, raise_errors: bool = True, invert: bool = False) -> bool:
		from selenium.common.exceptions import TimeoutException
		from selenium.webdriver.common.by import By
		from selenium.webdriver.support import expected_conditions as EC
		from selenium.webdriver.support.ui import WebDriverWait
		try:
			if invert:
				WebDriverWait(self.driver, self.timeout).until_not(EC.presence_of_element_located((By.CSS_SELECTOR, element)))
			else:
				WebDriverWait(self.driver, self.timeout).until(EC.presence_of_element_located((By.CSS_SELECTOR, element)))
			return True
		except TimeoutException as e:
			if raise_errors:
				if message is None:
					message = 'Timeout waiting for element to disappear: ' if invert else 'Timeout waiting for element to appear: '
				raise AssertionError(message + element) from e
		return False

	def wait_for_url(self, url: str, message: str = None, raise_errors: bool = True, invert: bool = False) -> bool:
		from selenium.common.exceptions import TimeoutException
		from selenium.webdriver.support import expected_conditions as EC
		from selenium.webdriver.support.ui import WebDriverWait
		try:
			if invert:
				WebDriverWait(self.driver, self.timeout).until_not(EC.url_to_be(url))
			else:
				WebDriverWait(self.driver, self.timeout).until(EC.url_to_be(url))
			return True
		except TimeoutException as e:
			if raise_errors:
				if message is None:
					message = 'Timeout waiting for URL to not be: ' if invert else 'Timeout waiting for URL to be: '
				raise AssertionError(message + url) from e
		return False

	def wait_for_file(self, path: str, message: str = 'Timeout waiting for file: ', raise_errors=True) -> bool:
		from os.path import exists
		from time import sleep, time
		start = time()
		while True:
			if exists(path): return True
			elapsed = time() - start
			if elapsed > self.timeout:
				if raise_errors:
					raise AssertionError(message + path)
				return False
			sleep(self._WAIT_POLL_EACH)

	def select(self, element, wait: bool = True, all: bool = False, raise_errors: bool = None):
		from selenium.webdriver.common.by import By
		from selenium.webdriver.remote.webelement import WebElement
		if isinstance(element, WebElement): return element
		found = self.wait(element, raise_errors=not all if raise_errors is None else raise_errors) if wait else False
		if all:
			return self.driver.find_elements(By.CSS_SELECTOR, element)
		elif found:
			return self.driver.find_element(By.CSS_SELECTOR, element)

	def write(self, element, text: str, clear: bool = False) -> None:
		from selenium.webdriver.common.action_chains import ActionChains
		from selenium.webdriver.common.keys import Keys
		from time import sleep
		element = self.select(element)
		if clear:
			self.click(element)
			ActionChains(self.driver).key_down(Keys.CONTROL).send_keys('a').key_up(Keys.CONTROL).send_keys(Keys.BACKSPACE).perform()
		for char in text:
			element.send_keys(self.translate(char))
			sleep(self.keystroke_delay)

	def press(self, text: str):
		from selenium.webdriver.common.action_chains import ActionChains
		from time import sleep
		for char in text:
			ActionChains(self.driver).send_keys(self.translate(char)).perform()
			sleep(self.keystroke_delay)

	def click(self, element) -> None:
		self.select(element).click()

	def hover(self, element) -> None:
		from selenium.webdriver.common.action_chains import ActionChains
		ActionChains(self.driver).move_to_element(self.select(element)).perform()

	def focus(self, element) -> None:
		from selenium.webdriver.common.action_chains import ActionChains
		ActionChains(self.driver).move_to_element(self.select(element)).click().perform()

	def drag(self, element, x_offset: int = 0, y_offset: int = 0) -> None:
		from selenium.webdriver.common.action_chains import ActionChains
		ActionChains(self.driver).drag_and_drop_by_offset(self.select(element), x_offset, y_offset).perform()

	def scroll(self, element, x_delta: float = 0, y_delta: float = 0, mouse_x: float = 0, mouse_y: float = 0) -> None:
		self.driver.execute_script('''arguments[0].dispatchEvent(new WheelEvent("wheel", { bubbles: true,
			deltaX: arguments[1], deltaY: arguments[2], clientX: arguments[3], clientY: arguments[4]
		}))''', self.select(element), x_delta, y_delta, mouse_x, mouse_y)

	def scroll_into_view(self, element):
		self.driver.execute_script('arguments[0].scrollIntoView({"block":"center"});', self.select(element))

	def attribute(self, element, attribute: str, value: Optional[str] = None) -> Optional[str]:
		args = [self.select(element), attribute]
		if value is None:
			script = 'return !arguments[0].hasAttribute(arguments[1]) ? null : arguments[0].getAttribute(arguments[1])'
		else:
			script = 'arguments[0].setAttribute(arguments[1], arguments[2])'
			args.append(value)
		return self.driver.execute_script(script, *args)

	def style(self, element, property: str, value: Optional[str] = None) -> Optional[str]:
		args = [self.select(element), property]
		if value is None:
			script = 'return getComputedStyle(arguments[0])[arguments[1]]'
		else:
			script = 'arguments[0].style[arguments[1]] = arguments[2]'
			args.append(value)
		return self.driver.execute_script(script, *args)

	def has_class(self, element, class_name: str) -> bool:
		return self.driver.execute_script(
			'return arguments[0].classList.contains(arguments[1])',
			self.select(element),
			class_name
		)

	def cookie(
		self, name: str, value: Optional[str] = None, expiry: int = None, delete: bool = False,
		path: str = None, domain: str = None, http_only: str = None, secure: str = None
	) -> Optional[str]:
		from time import time
		if delete:
			self.driver.delete_cookie(name)
		elif value is None:
			return self.driver.get_cookie(name)['value']
		else:
			cookie = {'name': name, 'value': value, 'path': '/'}
			cookie['expiry'] = expiry if expiry is not None else int(time() + self._YEAR_SECONDS)
			if path is not None: cookie['path'] = path
			if domain is not None: cookie['domain'] = domain
			if http_only is not None: cookie['httpOnly'] = http_only
			if secure is not None: cookie['secure'] = secure
			self.driver.add_cookie(cookie)

	def local_storage(self, key: str, value: Optional[str] = None, delete: bool = False) -> Optional[str]:
		if delete:
			self.driver.execute_script('localStorage.removeItem(arguments[0])', key)
		elif value is None:
			return self.driver.execute_script('return localStorage.getItem(arguments[0])', key)
		else:
			self.driver.execute_script('localStorage.setItem(arguments[0], arguments[1])', key, value)

	def session_storage(self, key: str, value: Optional[str] = None, delete: bool = False) -> Optional[str]:
		if delete:
			self.driver.execute_script('sessionStorage.removeItem(arguments[0])', key)
		elif value is None:
			return self.driver.execute_script('return sessionStorage.getItem(arguments[0])', key)
		else:
			self.driver.execute_script('sessionStorage.setItem(arguments[0], arguments[1])', key, value)

	def all_cookies(self, clear: bool = True, path: str = None, domain: str = None, http_only: str = None, secure: str = None) -> dict:
		res = {
			c['name']: c['value']
			for c in self.driver.get_cookies()
			if (path is None or c['path'] == path)
			and (domain is None or c['domain'] == domain)
			and (http_only is None or c['httpOnly'] == http_only)
			and (secure is None or c['secure'] == secure)
		}
		if clear:
			self.driver.delete_all_cookies()
		return res

	def all_local_storage(self, clear: bool = True) -> dict:
		res = {k: v for k, v in self.driver.execute_script('return Object.entries(localStorage)')}
		if clear:
			self.driver.execute_script('localStorage.clear()')
		return res

	def all_session_storage(self, clear: bool = True) -> dict:
		res = {k: v for k, v in self.driver.execute_script('return Object.entries(sessionStorage)')}
		if clear:
			self.driver.execute_script('sessionStorage.clear()')
		return res

	def box(self, element) -> Tuple[float, float]:
		res = self.driver.execute_script('return arguments[0].getBoundingClientRect()', self.select(element))
		res['center_left'] = res['left'] + res['width'] / 2
		res['center_top'] = res['top'] + res['height'] / 2
		return res

	def translate(self, char: str) -> str:
		from selenium.webdriver.common.keys import Keys
		if char == '\t':
			return Keys.TAB
		elif char == '\n':
			return Keys.ENTER
		else:
			return char

	def console_clear(self):
		self.driver.execute_script('window.CONSOLE_MESSAGES = []')

	def console_messages(self, group_by_level: bool = False) -> Union[Dict[str, List[str]], List[str]]:
		messages = self.driver.execute_script('return CONSOLE_MESSAGES')
		if group_by_level:
			res = {}
			for level, message in messages:
				res.setdefault(level, []).append(message)
			return res
		else:
			return [m[1] for m in messages]