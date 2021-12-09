from autoselenium import Firefox
from requests import get
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.ui import WebDriverWait
from simpler.format import human_seconds, human_bytes
from sys import stdout
from threading import Thread
from time import sleep, time
from traceback import print_exc
from typing import Dict, Optional, Tuple, Union
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

class Driver:

	_CONSOLE_LEVELS = 'debug', 'info', 'log', 'warn', 'error'
	_YEAR_SECONDS = 365.4 * 24 * 3600

	def __init__(self, timeout: int = 3, keystroke_delay: int = .005, headless: bool = True, disable_flash: bool = True, disable_images: bool = True):
		self.driver = Firefox(headless=headless, disable_flash=disable_flash, disable_images=disable_images)
		self.timeout = timeout
		self.keystroke_delay = keystroke_delay

	def browse(self, path: str):
		self.driver.get(path)
		WebDriverWait(self.driver, self.timeout).until(lambda d: d.execute_script('return document.readyState') == 'complete')
		self.driver.execute_script('var CONSOLE_MESSAGES = [];%s' % ';'.join(
			'console.%s = (m) => CONSOLE_MESSAGES.push([\'%s\', m])' % (level, level)
			for level in self._CONSOLE_LEVELS
		))

	def wait(self, element: str, message: str = 'Timeout waiting for element: ', raise_errors=True) -> None:
		try:
			WebDriverWait(self.driver, self.timeout).until(EC.presence_of_element_located((By.CSS_SELECTOR, element)))
			return True
		except TimeoutException as e:
			if raise_errors:
				raise AssertionError(message + element) from e
		return False

	def select(self, element: Union[str, WebElement], wait: bool = True, all: bool = False, raise_errors: bool = None) -> WebElement:
		if isinstance(element, WebElement): return element
		if wait:
			found = self.wait(element, raise_errors=all if raise_errors is None else raise_errors)
		if all:
			return self.driver.find_elements_by_css_selector(element)
		elif found:
			return self.driver.find_element_by_css_selector(element)

	def write(self, element: Union[str, WebElement], text: str, clear: bool = False) -> None:
		element = self.select(element)
		if clear:
			self.click(element)
			ActionChains(self.driver).key_down(Keys.CONTROL).send_keys('a').key_up(Keys.CONTROL).send_keys(Keys.BACKSPACE).perform()
		for char in text:
			element.send_keys(self.translate(char))
			sleep(self.keystroke_delay)

	def press(self, text: str):
		for char in text:
			ActionChains(self.driver).send_keys(self.translate(char)).perform()
			sleep(self.keystroke_delay)

	def click(self, element: Union[str, WebElement]) -> None:
		self.select(element).click()

	def hover(self, element: Union[str, WebElement]) -> None:
		ActionChains(self.driver).move_to_element(self.select(element)).perform()

	def focus(self, element: Union[str, WebElement]) -> None:
		ActionChains(self.driver).move_to_element(self.select(element)).click().perform()

	def drag(self, element: Union[str, WebElement], x_offset: int = 0, y_offset: int = 0) -> None:
		ActionChains(self.driver).drag_and_drop_by_offset(self.select(element), x_offset, y_offset).perform()

	def scroll(self, element: Union[str, WebElement], x_delta: float = 0, y_delta: float = 0, mouse_x: float = 0, mouse_y: float = 0) -> None:
		self.driver.execute_script('''arguments[0].dispatchEvent(new WheelEvent("wheel", { bubbles: true,
			deltaX: arguments[1], deltaY: arguments[2], clientX: arguments[3], clientY: arguments[4]
		}))''', self.select(element), x_delta, y_delta, mouse_x, mouse_y)

	def attribute(self, element: Union[str, WebElement], attribute: str, value: Optional[str] = None) -> Optional[str]:
		args = [self.select(element), attribute]
		if value is None:
			script = 'return !arguments[0].hasAttribute(arguments[1]) ? null : arguments[0].getAttribute(arguments[1])'
		else:
			script = 'arguments[0].setAttribute(arguments[1], arguments[2])'
			args.append(value)
		return self.driver.execute_script(script, *args)

	def style(self, element: Union[str, WebElement], property: str, value: Optional[str] = None) -> Optional[str]:
		args = [self.select(element), property]
		if value is None:
			script = 'return getComputedStyle(arguments[0])[arguments[1]]'
		else:
			script = 'arguments[0].style[arguments[1]] = arguments[2]'
			args.append(value)
		return self.driver.execute_script(script, *args)

	def bounding_box(self, element: Union[str, WebElement]) -> Dict[str, float]:
		return self.driver.execute_script('return arguments[0].getBoundingClientRect()', self.select(element))

	def has_class(self, element: Union[str, WebElement], class_name: str) -> bool:
		return self.driver.execute_script(
			'return arguments[0].classList.contains(arguments[1])',
			self.select(element),
			class_name
		)

	def cookie(self, name: str, value: Optional[str] = None, delete: bool = False) -> Optional[str]:
		if delete:
			self.driver.delete_cookie(name)
		elif value is None:
			return self.driver.get_cookie(name)['value']
		else:
			self.driver.add_cookie({'name': name, 'value': value, 'path': '/', 'expiry': int(time() + self._YEAR_SECONDS)})

	def clear_cookies(self):
		self.driver.delete_all_cookies()

	def box(self, element: Union[str, WebElement]) -> Tuple[float, float]:
		res = self.driver.execute_script('return arguments[0].getBoundingClientRect()', self.select(element))
		res['center_left'] = res['left'] + res['width'] / 2
		res['center_top'] = res['top'] + res['height'] / 2
		return res

	def translate(self, char: str) -> str:
		if char == '\t':
			return Keys.TAB
		elif char == '\n':
			return Keys.ENTER
		else:
			return char

	def console_clear(self):
		self.driver.execute_script('CONSOLE_MESSAGES = []')

	def console_messages(self, group_by_level: bool = False) -> Dict[str, str]:
		messages = self.driver.execute_script('return CONSOLE_MESSAGES')
		if group_by_level:
			res = {}
			for level, message in messages:
				res.setdefault(level, []).append(message)
			return res
		else:
			return [m[1] for m in messages]