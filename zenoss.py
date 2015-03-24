from errbot import BotPlugin, botcmd
import logging, urllib2, urllib, json

logger = logging.getLogger('errbot.botplugin.Zenoss')

class Zenoss(BotPlugin):
	"""An Err plugin to interact with Zenoss 4"""

    ROUTERS = { 'MessagingRouter': 'messaging',
                'EventsRouter': 'evconsole',
                'ProcessRouter': 'process',
                'ServiceRouter': 'service',
                'DeviceRouter': 'device',
                'NetworkRouter': 'network',
                'TemplateRouter': 'template',
                'DetailNavRouter': 'detailnav',
                'ReportRouter': 'report',
                'MibRouter': 'mib',
                'ZenPackRouter': 'zenpack' }
    connected = False
    reqCount = 0

    def activate(self):
        """Initialize the API connection, log in, and store authentication cookie
           Use the HTTPCookieProcessor as urllib2 does not save cookies by default"""
        super(Zenoss, self).activate()

        if self.config is not None and set(("ZENOSS_INST", "ZENOSS_USER", "ZENOSS_PASS")) <= set(self.config):
            self.urlOpener = urllib2.build_opener(urllib2.HTTPCookieProcessor())
            self.reqCount = 1
            # Contruct POST params and submit login.
            loginParams = urllib.urlencode(dict(
                        __ac_name = self.config['ZENOSS_USER'],
                        __ac_password = self.config['ZENOSS_PASS'],
                        submitted = 'true',
                        came_from = self.config['ZENOSS_INST'] + '/zport/dmd'))
            self.urlOpener.open(self.config['ZENOSS_INST'] + '/zport/acl_users/cookieAuthHelper/login', loginParams)
            self.connected = True
        else:
            logger.warn("Unable to connect to Zenoss, plugin not configured.")

	def get_configuration_template(self):
		"""Defines the configuration structure this plugin supports"""

		return {'ZENOSS_INST': 'http://server:8080',
                'ZENOSS_USER': "admin",
		        'ZENOSS_PASS': "admin"
		       }

    def request(self, router, method, data=[]):
        if router not in self.ROUTERS:
            raise Exception('Router "' + router + '" not available.')

        # Contruct a standard URL request for API calls
        req = urllib2.Request(self.config['ZENOSS_INSTANCE'] + '/zport/dmd/' +
                              self.ROUTERS[router] + '_router')

        # NOTE: Content-type MUST be set to 'application/json' for these requests
        req.add_header('Content-type', 'application/json; charset=utf-8')

        # Convert the request parameters into JSON
        reqData = json.dumps([dict(
                    action=router,
                    method=method,
                    data=data,
                    type='rpc',
                    tid=self.reqCount)])

        # Increment the request count ('tid'). More important if sending multiple
        # calls in a single request
        self.reqCount += 1

        # Submit the request and convert the returned JSON to objects
        return json.loads(self.urlOpener.open(req, reqData).read())

	# Passing split_args_with=None will cause arguments to be split on any kind
	# of whitespace, just like Python's split() does
	@botcmd(split_args_with=None)
    def get_devices(self, deviceClass='/zport/dmd/Devices'):
        return self.request('DeviceRouter', 
                            'getDevices',
                            data=[{ 'uid': deviceClass, 
                                    'limit': 2600,
                                    'params': {} }]
                            )['result']
