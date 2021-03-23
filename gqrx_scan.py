import argparse
import telnetlib
import csv
import signal
import time

def interrupted(signum, fram):
	pass

signal.signal(signal.SIGALRM, interrupted)

class Scanner:

	def __init__(self, hostname, port, waitTime=5, signalStrength=-20):
		self.host = hostname
		self.port = port
		self.waitTime = waitTime
		self.signalStrength = signalStrength

	def _update(self, msg):
		"""
		update the frequency/mode GQRX is listening to
		"""
		try:
			tn = telnetlib.Telnet(self.host, self.port)
		except Exception as e:
			print("Error connecting to " + self.host + ":" + str(self.port) + "\n\t" + str(e))
			exit()
		tn.write(('%s\n' % msg).encode('ascii'))
		response = tn.read_some().decode('ascii').strip()
		tn.write('q\n'.encode('ascii'))
		return response

	def scan(self):
		"""
		loop over the frequencies in the list,
		and stop if the frequency is active (signal strength is high enough)
		"""
		while(1):
			for freq in self.freqs.keys():
				out = [self.freqs[freq]['tag'], freq]
				out.append(self._set_freq(freq))
				out.append(self._set_mode(self.freqs[freq]['mode']))
				out.append(self._set_squelch(self.signalStrength))
				print('\t'.join([str(x) for x in out]))
				time.sleep(1)
				if float(self._get_level()) >= self.signalStrength:
					timenow = str(time.localtime().tm_hour) + ':' + str(time.localtime().tm_min)
					print('SIGNAL!', timenow, freq, self.freqs[freq]['tag'])
					while float(self._get_level()) >= self.signalStrength:
						try:
							signal.alarm(self.waitTime)
							key = raw_input()
							if key == '':
								break
						except:
							pass


	def scan_range(self, minfreq, maxfreq, mode, step=500, save = None):
		"""
		Scan a range of frequencies

		:param minfreq: lower frequency
		:param maxfreq: upper frequency
		:param mode: mode to scan in
		:param save: (optional) a txt file to save the active frequencies to
		:return: none

		"""
		minfreq = str(float(minfreq) * 1e5)
		minfreq = int(minfreq.replace('.', ''))

		maxfreq = str(float(maxfreq) * 1e5)
		maxfreq = int(maxfreq.replace('.', ''))

		if save is not None:
			pass

		else:
			freq = minfreq
			while(1):
				if freq <= maxfreq:

					self._set_freq(freq)
					self._set_mode(mode)
					self._set_squelch(self.signalStrength)
					time.sleep(0.5)
					if float(self._get_level()) >= self.signalStrength:
						timenow = str(time.localtime().tm_hour) + ':' + str(time.localtime().tm_min)
						print(timenow, freq)
						print("Press enter to continue scanning")
						while float(self._get_level()) >= self.signalStrength:
							key = raw_input()
							if key == '':
								freq = freq + step
								break

					else:
						freq = freq + step
				else:
					freq = minfreq


		pass

	def load(self, freq_csv, delimiter=','):
		"""
		read the csv file with the frequencies & modes
		in it into a dict{} where keys are the freq and
		the value is a dict with the mode and a tag
		"""
		self.freqs = {}
		with open(freq_csv, 'r') as csvfile:
			reader = csv.reader(csvfile, delimiter=delimiter)
			for row in reader:
				if not row:
					continue
				freq = str(float(row[0])*1e5)	    					# 1e5 isn't good
				freq = int(freq.replace('.', ''))   					# converted to hz
				print(row)
				if len(row) == 2:
					self.freqs[freq] = {'mode': row[1], 'tag': None}
				elif len(row) > 2:
					self.freqs[freq] = {'mode' : row[1], 'tag': ', '.join(row[2:])}		# add the freq to the dict as a key and the mode as the value

	def _set_freq(self, freq):
		return self._update("F %s" % freq)

	def _set_mode(self, mode):
		return self._update("M %s" % mode)

	def _set_squelch(self, sql):
		return self._update("L SQL %s" % sql)

	def _get_level(self):
		return self._update("l")

	def _get_mode(self):
		return self._update('m')

def parse_args():
	ap = argparse.ArgumentParser()
	ap.add_argument('-c', '--csv', help='CSV file to parse', default='freq.csv')
	ap.add_argument('-d', '--delimiter', help='CSV Delimiter', default=',')
	ap.add_argument('-i', '--hostname', help='IP or hostname for gqrx', default='127.0.0.1')
	ap.add_argument('-p', '--port', help='Port for gqrx', default=7356)
	return ap.parse_args()

if __name__ == "__main__":
	args = parse_args()
	scanner = Scanner(
		hostname=args.hostname,
		port=args.port
	)
	scanner.load(args.csv, args.delimiter)
	if not len(scanner.freqs) > 1:
		raise RuntimeError('No frequencies found in {}'.format(args.csv))
	scanner.scan()
