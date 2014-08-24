#!/usr/bin/python

# -*- coding: utf-8 -*-

# Copyright (C) 2009-2012:
#    Gabes Jean, naparuba@gmail.com
#    Gerhard Lausser, Gerhard.Lausser@consol.de
#    Gregory Starck, g.starck@gmail.com
#    Hartmut Goebel, h.goebel@goebel-consult.de
#
# This file is part of Shinken.
#
# Shinken is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Shinken is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with Shinken.  If not, see <http://www.gnu.org/licenses/>.

"""
Unit test for GraphiteWebui module.
"""
import unittest
import time

from shinken.objects import Module, Service, Host, Command
from module.module import get_instance


GRAPHEND = time.time()-3600
GRAPHSTART = GRAPHEND-3600

def init_module():
    """Initialize the module with standard configuration"""
    config_options = Module({
        'module_name': 'ui-graphite',
        'module_type': 'graphite-webui',
        'uri': 'http://YOURSERVERNAME/',
    })
    return get_instance(config_options)

def init_service(params={}):
    """Create a service with specified parameters

    Parameters
    * params : A dict of parms
        * command_name : The command name (default dummy_cmd)
        * command_line : The command line (default dummy_cmd!1)
        * host_name : The host name (default Dummy host)
        * service_description: The service name (default Dummy service)
        * perf_data : The service perf data (default empty)
    """

    command_name = params.get('command_name', 'dummy_cmd')
    command_line = params.get('command_line', 'dummy_cmd!1')
    host_name = params.get('host_name', 'Dummy host')
    service_description = params.get('service_description', 'Dummy service')
    perf_data = params.get('perf_data', '')

    host = Host({
        'host_name': host_name,
    })

    cmd = Command({
        'command_name': command_name,
        'command_line': command_line,
    })

    srv = Service({
        'service_description': service_description,
        'perf_data': perf_data,
    })
    srv.host = host
    srv.check_command = cmd

    return srv


class GetMetricAndValueTest(unittest.TestCase):
    """Test the get_metric_and_value function"""

    def test_without_metric(self):
        """Test standard return without perf data"""
        module = init_module()

        metric = ''

        ret = module.get_metric_and_value(metric)

        self.assertIsInstance(ret, list)
        self.assertIs(len(ret), 0)

    def test_with_metric(self):
        """Test standard return with perf data"""

        module = init_module()

        metric = """/=30MB;4899;4568;1234;0
/var=50MB;4899;4568;1234;0
/toto="""

        ret = module.get_metric_and_value(metric)

        self.assertIsInstance(ret, list)
        self.assertIs(len(ret), 6)
        self.assertIn(('_', (30, 'MB')), ret)
        self.assertIn(('__crit', 4568), ret)
        self.assertIn(('__warn', 4899), ret)
        self.assertIn(('_var', (50, 'MB')), ret)
        self.assertIn(('_var_crit', 4568), ret)
        self.assertIn(('_var_warn', 4899), ret)

class ReplaceFontSizeTest(unittest.TestCase):
    """Test the replace_font_size function"""

    def test_replace_font_size(self):
        """Test the replacement with already specified font size in url"""

        module = init_module()
        url = 'http://shinken.example.com/graph?before=1&fontSize=42&after=2'
        new_size = '123'

        new_url = module.replace_font_size(url, new_size)
        self.assertIn('fontSize=123', new_url)
        self.assertIn('before=1', new_url)
        self.assertIn('after=2', new_url)

    def test_add_font_size(self):
        """Test the adding of new size"""

        module = init_module()
        url = 'http://shinken.example.com/graph?before=1&after=2'
        new_size = '123'

        new_url = module.replace_font_size(url, new_size)
        self.assertIn('fontSize=123', new_url)
        self.assertIn('before=1', new_url)
        self.assertIn('after=2', new_url)

class ReplaceGraphSizeTest(unittest.TestCase):
    """Test the replacement of graph size"""

    def test_replace_graph_size(self):
        """Test the replace with already specified graph size in url"""

        module = init_module()
        url = 'http://shinken.example.com/graph?width=42&height=42&after=2'
        new_height = '123'
        new_width = '123'

        new_url = module.replace_graph_size(url, new_width, new_height)
        self.assertIn('height=123', new_url)
        self.assertIn('width=123', new_url)
        self.assertIn('after=2', new_url)

    def test_add_graph_size(self):
        """Test the adding of new graph size"""

        module = init_module()
        url = 'http://shinken.example.com/graph?before=1&after=2'
        new_height = '123'
        new_width = '123'

        new_url = module.replace_graph_size(url, new_width, new_height)
        self.assertIn('height=123', new_url)
        self.assertIn('width=123', new_url)
        self.assertIn('before=1', new_url)
        self.assertIn('after=2', new_url)

    def test_add_graph_size_height(self):
        """Test adding height graph size"""

        module = init_module()
        url = 'http://shinken.example.com/graph?before=1&width=42&after=2'
        new_height = '123'
        new_width = '123'

        new_url = module.replace_graph_size(url, new_width, new_height)
        self.assertIn('height=123', new_url)
        self.assertIn('width=123', new_url)
        self.assertIn('before=1', new_url)
        self.assertIn('after=2', new_url)

    def test_add_graph_size_width(self):
        """Test adding width graph size"""

        module = init_module()
        url = 'http://shinken.example.com/graph?before=1&height=42&after=2'
        new_height = '123'
        new_width = '123'

        new_url = module.replace_graph_size(url, new_width, new_height)
        self.assertIn('height=123', new_url)
        self.assertIn('width=123', new_url)
        self.assertIn('before=1', new_url)
        self.assertIn('after=2', new_url)

class GetGraphUrisTest(unittest.TestCase):
    """Test the get_graph_uris function"""

    def test_service_uri_without_graph(self):
        """Get a simple service graph uri with no graph"""
        module = init_module()
        service = init_service()

        uris = module.get_graph_uris(service, GRAPHSTART, GRAPHEND)

        self.assertIs(type(uris), list)
        self.assertEquals(len(uris), 0)

    def test_service_with_percent(self):
        """Get graph for service with only one perf data field"""
        module = init_module()
        service = init_service({
            'perf_data': 'dummy_service=50%;70;80',
        })

        uris = module.get_graph_uris(service, GRAPHSTART, GRAPHEND)

        self.assertIs(type(uris), list)
        self.assertEquals(len(uris), 1)
        img_src = uris[0]['img_src']
        self.assertIn('yMin=0', img_src)
        self.assertIn('yMax=100', img_src)
        self.assertIn('target=Dummy_host.Dummy_service.dummy_service', img_src)
        self.assertIn('fontSize=8', img_src)
        self.assertIn('width=586', img_src)
        self.assertIn('height=308', img_src)

    def test_service_with_min_max(self):
        """Get graph for service with only one perf data field"""
        module = init_module()
        service = init_service({
            'perf_data': 'dummy_service=500M;300;400;110;1000;',
        })

        uris = module.get_graph_uris(service, GRAPHSTART, GRAPHEND)

        self.assertIs(type(uris), list)
        self.assertEquals(len(uris), 1)
        img_src = uris[0]['img_src']
        #self.assertIn('yMin=110', img_src)
        #self.assertIn('yMax=1000', img_src)
        self.assertIn('target=Dummy_host.Dummy_service.dummy_service', img_src)
        self.assertIn('fontSize=8', img_src)
        self.assertIn('width=586', img_src)
        self.assertIn('height=308', img_src)

    def test_service_with_graph_size(self):
        """Test if we can specified font size"""
        module = init_module()
        service = init_service({
            'perf_data': 'dummy_service=500M;300;400;110;1000;',
        })
        graph_size = {
            'width': '42',
            'height': '4242',
        }

        uris = module.get_graph_uris(
            service,
            GRAPHSTART,
            GRAPHEND,
            params=graph_size)
        img_src = uris[0]['img_src']

        self.assertIn('width=42', img_src)
        self.assertIn('height=4242', img_src)

if __name__ == '__main__':
    unittest.main()
