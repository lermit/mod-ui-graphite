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
This class is for linking the WebUI with Graphite,
for mainly get graphs and links.
"""

import re
import socket
import os

from shinken.log import logger
from string import Template
from shinken.basemodule import BaseModule
from datetime import datetime
from shinken.misc.perfdata import PerfDatas


properties = {
    'daemons': ['webui'],
    'type': 'graphite_webui'
    }

DEBUG_PREFIX = '[Graphite UI] '

def get_instance(plugin):
    """called by the plugin manager"""
    logger.debug("{prefix}Get an GRAPHITE UI module for plugin {name}".format(
        prefix=DEBUG_PREFIX,
        name=plugin.get_name()))

    instance = GraphiteWebui(plugin)
    return instance


class GraphiteWebui(BaseModule):
    """Main module class"""
    def __init__(self, modconf):
        BaseModule.__init__(self, modconf)
        self.multival = re.compile(r'_(\d+)$')
        self.uri = getattr(modconf, 'uri', None)
        self.templates_path = getattr(modconf, 'templates_path', '/tmp')

        if not self.uri:
            raise Exception(
                'The WebUI Graphite module is missing uri parameter.')

        self.uri = self.uri.strip()
        if not self.uri.endswith('/'):
            self.uri += '/'

        # Change YOURSERVERNAME by our server name if we got it
        if 'YOURSERVERNAME' in self.uri:
            my_name = socket.gethostname()
            self.uri = self.uri.replace('YOURSERVERNAME', my_name)

        # optional "sub-folder" in graphite to hold the data of a specific host
        self.graphite_data_source = self.illegal_char.sub(
            '_',
            getattr(modconf, 'graphite_data_source', ''))

    def init(self):
        """Try to connect if we got true parameter"""
        pass

    def load(self, app):
        """To load the webui application"""
        self.app = app

    def get_external_ui_link(self):
        """Give the link for the GRAPHITE UI, with a Name
        """
        return {'label': 'Graphite', 'uri': self.uri}

    def get_metric_and_value(self, perf_data):
        """For a perf_data like
          /=30MB;4899;4568;1234;0
          /var=50MB;4899;4568;1234;0
          /toto=

          return ('/', '30'), ('/var', '50')
        """
        res = []
        metrics = PerfDatas(perf_data)

        for e in metrics:
            try:
                logger.debug("{prefix}groking: {metric}".format(
                    prefix=DEBUG_PREFIX,
                    metric=str(e)))
            except UnicodeEncodeError:
                pass

            name = self.illegal_char.sub('_', e.name)
            name = self.multival.sub(r'.*', name)

            # get metric value and its thresholds values if they exist
            name_value = {name: (e.value, e.uom)}
            if e.warning and e.critical:
                name_value[name + '_warn'] = e.warning
                name_value[name + '_crit'] = e.critical
            # bailout if need
            if name_value[name] == '':
                continue
            try:
                logger.debug("{prefix}Got in the end: {name}, {value}".format(
                    prefix=DEBUG_PREFIX,
                    name=name,
                    value=e.value))
            except UnicodeEncodeError:
                pass
            for key, value in name_value.items():
                res.append((key, value))
        return res

    @staticmethod
    def replace_font_size(url, newsize):
        """Private function to replace the fontsize uri parameter by the correct
        value or add it if not present."""

        # Do we have fontSize in the url already, or not ?
        if re.search('fontSize=', url) is None:
            url = url + '&fontSize=' + newsize
        else:
            url = re.sub(
                r'(fontSize=)[^\&]+',
                r'\g<1>' + newsize,
                url)
        return url

    @staticmethod
    def replace_graph_size(url, width, height):
        """Private function to replace the graph size by the specified
        value."""

        # Replace width
        if re.search('width=', url) is None:
            url = "{url}&width={width}".format(
                url=url,
                width=width)
        else:
            url = re.sub(
                r'width=[^\&]+',
                'width={width}'.format(width=width),
                url)

        # Replace Height
        if re.search('height=', url) is None:
            url = "{url}&height={height}".format(
                url=url,
                height=height)
        else:
            url = re.sub(
                r'height=[^\&]+',
                'height={height}'.format(height=height),
                url)

        return url

    def get_graphite_variables(self, elt):
        """return the good graphite pre and post string regarding
        the element type

        Return a tuple (graphite_pre,graphite_post)
        """
        graphite_pre = ""
        graphite_post = ""
        if elt.__class__.my_type == 'host':
            if "_GRAPHITE_PRE" in elt.customs:
                graphite_pre = "%s." % self.illegal_char.sub("_", elt.customs["_GRAPHITE_PRE"])
        elif elt.__class__.my_type == 'service':
            if "_GRAPHITE_PRE" in elt.host.customs:
                graphite_pre = "%s." % self.illegal_char.sub("_", elt.host.customs["_GRAPHITE_PRE"])
            if "_GRAPHITE_POST" in elt.customs:
                graphite_post = ".%s" % self.illegal_char.sub("_", elt.customs["_GRAPHITE_POST"])
        return (graphite_pre, graphite_post)


    def get_graph_uris(self, elt, graphstart, graphend,
                       source='detail', params={}):
        """Ask for an host or a service the graph UI that the UI should
        give to get the graph image link and Graphite page link too.

        Parameters
        * params : array of extra parameter :
            * width: graph width (default 586)
            * height: graph height (default 308)
        """
        # Ugly to hard-code such values. But where else should I put them ?
        fontsize = {'detail':'8', 'dashboard':'18'}
        height = params.get('height', 308)
        width = params.get('width', 586)
        if not elt:
            return []

        ret = []

        # Hanling Graphite variables
        data_source = ""
        if self.graphite_data_source:
            data_source = ".%s" % self.graphite_data_source

        graphite_pre, graphite_post = self.get_graphite_variables(elt)

        # Format the start & end time (and not only the date)
        start_date = datetime.fromtimestamp(graphstart)
        start_date = start_date.strftime('%H:%M_%Y%m%d')
        end_date = datetime.fromtimestamp(graphend)
        end_date = end_date.strftime('%H:%M_%Y%m%d')

        filename = elt.check_command.get_name().split('!')[0] + '.graph'

        # Do we have a template for the given source?
        thefile = os.path.join(self.templates_path, source, filename)

        # If not try to use the one for the parent folder
        if not os.path.isfile(thefile):
            # In case of CHECK_NRPE, the check_name is in second place
            if len(elt.check_command.get_name().split('!')) > 1:
                filename = "{first_part}_{second_part}.graph".format(
                    first_part=elt.check_command.get_name().split('!')[0],
                    second_part=elt.check_command.get_name().split('!')[1])
                thefile = os.path.join(self.templates_path, source, filename)
            if not os.path.isfile(thefile):
                thefile = os.path.join(self.templates_path, filename)

        if os.path.isfile(thefile):
            template_html = ''
            with open(thefile, 'r') as template_file:
                template_html += template_file.read()
            # Read the template file, as template string python object

            html = Template(template_html)
            # Build the dict to instantiate the template string
            values = {}
            if elt.__class__.my_type == 'host':
                values['host'] = "{graphite_pre}{hostname}{datasource}".format(
                    graphite_pre=graphite_pre,
                    hostname=self.illegal_char.sub("_", elt.host_name),
                    datasource=data_source)
                values['service'] = '__HOST__'
            elif elt.__class__.my_type == 'service':
                values['host'] = "{graphite_pre}{hostname}{datasource}".format(
                    graphite_pre=graphite_pre,
                    hostname=self.illegal_char.sub("_", elt.host.host_name),
                    datasource=data_source)
                values['service'] = "{srvdesc}{graphite_post}".format(
                    srvdesc=self.illegal_char.sub("_", elt.service_description),
                    graphite_post=graphite_post)
            values['uri'] = self.uri
            # Split, we may have several images.
            for img in html.substitute(values).split('\n'):
                if not img == "":
                    graph = {}
                    graph['link'] = self.uri
                    graph['img_src'] = "{img}&from={since}&until={to}".format(
                        img=img.replace('"', "'"),
                        since=start_date,
                        to=end_date)
                    graph['img_src'] = self.replace_font_size(
                        graph['img_src'],
                        fontsize[source])
                    graph['img_src'] = self.replace_graph_size(
                        graph['img_src'],
                        width,
                        height)
                    ret.append(graph)
            # No need to continue, we have the images already.
            return ret

        # If no template is present, then the usual way
        if elt.__class__.my_type == 'host':
            couples = self.get_metric_and_value(elt.perf_data)

            # If no values, we can exit now
            if len(couples) == 0:
                return []

            # Remove all non alpha numeric character
            host_name = self.illegal_char.sub('_', elt.host_name)

            # Send a bulk of all metrics at once
            for (metric, _) in couples:
                uri = self.uri + 'render/?lineMode=connected&from=' + start_date + "&until=" + end_date
                if re.search(r'_warn|_crit', metric):
                    continue
                target = "&target=%s%s%s.__HOST__.%s" % (graphite_pre,
                                                         host_name,
                                                         data_source,
                                                         metric)
                uri += target + target + "?????"
                graph = {}
                graph['link'] = self.uri
                graph['img_src'] = uri
                graph['img_src'] = self.replace_font_size(
                    graph['img_src'],
                    fontsize[source])
                graph['img_src'] = self.replace_graph_size(
                    graph['img_src'],
                    width,
                    height)
                ret.append(graph)
        elif elt.__class__.my_type == 'service':
            couples = self.get_metric_and_value(elt.perf_data)

            # If no values, we can exit now
            if len(couples) == 0:
                return []

            # Remove all non alpha numeric character
            desc = self.illegal_char.sub('_', elt.service_description)
            host_name = self.illegal_char.sub('_', elt.host.host_name)

            # Send a bulk of all metrics at once
            for (metric, value) in couples:
                uri = self.uri + 'render/?lineMode=connected&from=' + start_date + "&until=" + end_date
                if re.search(r'_warn|_crit', metric):
                    continue
                elif value[1] == '%':
                    uri += "&yMin=0&yMax=100"
                target = "&target=%s%s%s.%s.%s%s" % (
                    graphite_pre,
                    host_name,
                    data_source,
                    desc,
                    metric,
                    graphite_post)
                uri += target + target + "?????"
                graph = {}
                graph['link'] = self.uri
                graph['img_src'] = uri
                graph['img_src'] = self.replace_font_size(
                    graph['img_src'],
                    fontsize[source])
                graph['img_src'] = self.replace_graph_size(
                    graph['img_src'],
                    width,
                    height)
                ret.append(graph)
        # Oups, bad type?
        else:
            return []
        return ret

