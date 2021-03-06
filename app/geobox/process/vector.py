# This file is part of the GBI project.
# Copyright (C) 2012 Omniscale GmbH & Co. KG <http://omniscale.com>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from datetime import datetime

from geobox.process.base import ProcessBase
from geobox.lib.couchdb import CouchDB
from geobox.lib.vectormapping import default_mappings as mappings
from geobox.lib.vectorconvert import load_json_from_shape, write_json_to_shape, ConvertError


import logging
log = logging.getLogger(__name__)

class VectorExportProcess(ProcessBase):
    def process(self):
        log.debug('Start vector export process. Task %d' % self.task_id)
        try:
            with self.task() as task:
                mapping = mappings[task.mapping_name].copy()
                output_file = self.app_state.user_data_path('export', task.project.title, task.mapping_name + '.shp', make_dirs=True)

                couch = CouchDB('http://%s:%s' % ('127.0.0.1', self.app_state.config.get('couchdb', 'port')), task.db_name)
                write_json_to_shape(couch.load_records(), mapping, output_file)
            self.task_done()
        except ConvertError, e:
            self.task_failed(e)
        except AssertionError, e:
            # fiona uses assertions without error messages
            if not str(e):
                self.task_failed(ConvertError('unable to write shapefile'))
            else:
                self.task_failed(e)
        except KeyError, e:
            # mapping not exists
            self.task_failed(e)
        except Exception, e:
            self.task_failed(e)


class VectorImportProcess(ProcessBase):
    def process(self):
        log.debug('Start vector import process. Task %d' % self.task_id)
        try:
            with self.task() as task:
                mapping = mappings[task.mapping_name].copy()
                mapping.json_defaults = mapping.json_defaults.copy()
                mapping.json_defaults['import_timestamp'] = datetime.now().isoformat();
                mapping.json_defaults['import_file'] = task.file_name;

                input_file = self.app_state.user_data_path('import', task.file_name)
                couch = CouchDB('http://%s:%s' % ('127.0.0.1', self.app_state.config.get('couchdb', 'port')), task.db_name)
                couch.store_records(
                    load_json_from_shape(input_file, mapping)
                )
            self.task_done()
        except ConvertError, e:
            self.task_failed(e)
        except AssertionError, e:
            # fiona uses assertions without error messages
            if not str(e):
                self.task_failed(ConvertError('unable to read shapefile'))
            else:
                self.task_failed(e)
        except KeyError, e:
            # mapping not exists
            self.task_failed(e)
        except Exception, e:
            self.task_failed(e)
