import logging
import http
import werkzeug
from threading import Lock
from requests import Session, adapters
from requests.exceptions import ReadTimeout
from flask_restful import abort
from time import time, sleep
import ccxt

from .exceptions import *

GRACE_TIME = 5 # Seconds to sleep on exception
API_RETRIES = 3  # Times to retry query before giving up

class Exchange(object):
    _initialized = False
    _req = 0
    _reqtime = 0
    
    # default values
    _reqinterval = 1    # seconds
    _reqlimit = 100     # essentially no limit (100 req/s)
    _reqtimeout = 15    # seconds

    @classmethod
    def initclass(cls):
        if not cls._initialized:
            cls.logger = logging.getLogger(cls.__module__)
            cls._session = Session()
            adapter = adapters.HTTPAdapter(max_retries=5)
            cls._session.mount('http://', adapter)
            cls._session.mount('https://', adapter)
            cls._reqlock = Lock()
            cls._initialized = True
            cls.logger.debug('Initializing ' + cls.__name__)
        
    def __init__(self, key=None, secret=None, passphrase=None, user_id=None):
        self.initclass()
        self.key = key
        self.secret = secret
        self.passphrase = passphrase
        self.user_id = user_id
        
    @classmethod
    def _query(cls, method, url, *args, **kwargs):
        # may be worth error handling here - retry / temp blacklist
        with cls._reqlock:
            # throttle
            t = cls._reqtime - time()
            if (t > 0 and cls._req == cls._reqlimit):
                cls.logger.info('reqlimit hit. sleeping %.2fs' % t)
                sleep(t)
            # new interval
            if cls._reqtime <= time():
                cls._reqtime = time() + cls._reqinterval
                cls._req = 0
            cls._req += 1
        cls.logger.debug('request: %s' % dict(
            method=method, url=url, args=args, kwargs=kwargs))
        kwargs['timeout'] = cls._reqtimeout

        # TODO: add blacklisting
        try:
            r = cls._session.request(method, url, *args, **kwargs)
        except APIKeyError:
            # raised by exchange auth call
            raise
        except ReadTimeout as e:
            exc = 'ReadTimeout'
        except Exception as e:
            cls.logger.warning(repr(e))
            exc = e
        else:
            cls.logger.debug('response: %s' % r.text)
            try:
                return r.json()
            except Exception as e:
                cls.logger.warning(repr(e))
            try:
                status = ' %s' % http.client.responses[r.status_code]
            except:
                status = ''
            raise ConnectionError('HTTP %s%s' % (r.status_code, status))
        raise ConnectionError(exc)

    @classmethod
    def _ccxt_query(cls, exchange, method, *args):
        # may be worth error handling here - retry / temp blacklist
        with cls._reqlock:
            # throttle
            t = cls._reqtime - time()
            if (t > 0 and cls._req == cls._reqlimit):
                cls.logger.info('reqlimit hit. sleeping %.2fs' % t)
                sleep(t)
            # new interval
            if cls._reqtime <= time():
                cls._reqtime = time() + cls._reqinterval
                cls._req = 0
            cls._req += 1
        cls.logger.debug('CCXT request: %s' % dict(
            method=method, args=args))
        for i in range(API_RETRIES + 1):
            try:
                call = getattr(exchange, method)
                return call(*args)
            except ccxt.OrderNotFound:
                return False  
            except ccxt.InvalidOrder:
                abort(400)             
            except ccxt.AuthenticationError:
                abort(403)
            except ccxt.PermissionDenied:
                abort(403)
            except ccxt.InvalidNonce:
                abort(503)
            except ccxt.ExchangeError:
                abort(404)
            except ccxt.NetworkError:
                if i == API_RETRIES:
                    abort(503)
                sleep(GRACE_TIME)
            except http.client.RemoteDisconnected:
                if i == API_RETRIES:
                    abort(503)
                sleep(GRACE_TIME)
            except ccxt.ExchangeNotAvailable:
                if i == API_RETRIES:
                    abort(503)
                sleep(GRACE_TIME)  
            except werkzeug.exceptions.ServiceUnavailable:
                if i == API_RETRIES:
                    abort(503)
                sleep(GRACE_TIME)       
            except Exception as e:
                cls.logger.debug(e)
                abort(503)

    @staticmethod
    def trunc(v, d=8):
        # truncates v to d decimal places
        return int(float(v) * pow(10, d)) / pow(10, d)

    @staticmethod
    def round(roundDown, price, stepSize, minPrice = 0):
        diff = price - minPrice
        quotient = diff // stepSize
        remainder = diff % stepSize
        if remainder > 0:
            price = minPrice + ((quotient + (0 if roundDown else 1)) * stepSize)
        return price