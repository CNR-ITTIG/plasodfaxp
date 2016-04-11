# -*- coding: utf-8 -*-
#
# The MIT License (MIT)
#
# Copyright (c) 2016 CNR-ITTIG
#
# Developed under the Grant Agreement Number 608185 Collaborative Project
#                            EVIDENCE Project
# "European Informatics Data Exchange Framework for Courts and Evidence"
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
"""Alpha DFAX output module (please see plaso2dfax on CNR-ITTIG@github)."""

import logging
import os

from plaso.lib import event
from plaso.lib import eventdata
from plaso.lib import timelib
from plaso.output import interface
from plaso.output import manager

from cybox.bindings.url_history_object import (
    URLHistoryEntryType as cyboxUrlHistoryEntry)
from cybox.common import Hash as cyboxHash
from cybox.common import object_properties as cyboxObjectProperties
from cybox.core import Observable as cyboxObservable
from cybox.core import Observables as cyboxObservables
from cybox.objects.file_object import File as cyboxFile


class PlasoDFaxOutputModule(interface.OutputModule):
  """Dumps event objects to a DFax file."""

  NAME = u'pdfax'
  DESCRIPTION = u'Dumps event objects to a DFax file.'

  # A dict containing mappings between the name of event source and
  # a callback function used for the conversion to a Cybox object.
  _EVENT_TO_CYBOX_CALLBACKS = {
      u'fs:stat': u'_FileStat',
      #u'msiecf:url': u'URLHistory',
  }

  NULL_PATHSPEC = hash(u'')

  def __init__(self, output_mediator):
    """Initializes the output module object.

    Args:
      output_mediator: The output mediator object (instance of OutputMediator).
    """
    super(PlasoDFaxOutputModule, self).__init__(output_mediator)
    self._file_path = None
    self._storage_file = None
    # The dictionary is used to keep track of pathspecs.
    self._pathspecs = {}
    # The _uuid_map is used to map event to cybox objects by plaso uuid.
    self._uuid_map = {}
    # The file object todo
    self._cybox_files = {}

  def Close(self):
    """Closes the plaso storage file."""
    observables = cyboxObservables()

    for _, cybox_file in self._cybox_files.iteritems():
      observables.add(cyboxObservable(cybox_file))

    print observables.to_xml()
    self._storage_file.Close()

  def Open(self):
    """Opens the plaso DFax file."""
    pre_obj = event.PreprocessObject()
    pre_obj.collection_information = {
        u'time_of_run': timelib.Timestamp.GetNow()}

    filter_expression = self._output_mediator.filter_expression
    if filter_expression:
      pre_obj.collection_information[u'filter'] = filter_expression

    storage_file_path = self._output_mediator.storage_file_path
    if storage_file_path:
      pre_obj.collection_information[u'file_processed'] = storage_file_path

    self._storage_file = None

  def SetFilePath(self, file_path):
    """Sets the file-like object based on the file path.

    Args:
      file_path: the full path to the output file.
    """
    self._file_path = file_path

  def _CreateCyboxFile(self, event_object):
    '''_CreateCyboxFile'''
    file_path, file_name_ext = os.path.split(event_object.filename)
    file_name, file_extension = os.path.splitext(file_name_ext)
    file_extension = file_extension.lstrip(u'.')

    cybox_file = cyboxFile()
    cybox_file.file_name = file_name
    cybox_file.file_path = file_path
    cybox_file.file_extension = file_extension

    if hasattr(event_object, u'sha256_hash'):
      cybox_file.add_hash(cyboxHash(
          hash_value=event_object.sha256_hash, type_=cyboxHash.TYPE_SHA256))
    if hasattr(event_object, u'sha1_hash'):
      cybox_file.add_hash(cyboxHash(
          hash_value=event_object.sha1_hash, type_=cyboxHash.TYPE_SHA1))
    if hasattr(event_object, u'md5_hash'):
      cybox_file.add_hash(cyboxHash(
          hash_value=event_object.md5_hash, type_=cyboxHash.TYPE_MD5))

    if hasattr(event_object, u'pathspec'):
      pathspec = event_object.pathspec
      self._pathspecs[event_object.filename] = hash(pathspec)

      custom_property = cyboxObjectProperties.Property()
      custom_property.name = u'pathspec'
      custom_property.description = 'dfvfs path specification'
      custom_property._value = u'My Custom Value'

      cybox_file.custom_properties = cyboxObjectProperties.CustomProperties()
      cybox_file.custom_properties.append(custom_property)
    else:
      self._pathspecs[cybox_file] = self.NULL_PATHSPEC

    self._cybox_files[event_object.filename] = cybox_file
    return cybox_file

  def _GetCyboxFileObject(self, event_object):
    '''_GetCyboxFileObject'''
    cybox_file = self._cybox_files.get(event_object.filename, None)
    if not cybox_file:
      logging.debug(u'New Cybox File, file {}'.format(event_object.filename))
      cybox_file = self._CreateCyboxFile(event_object)
    else:
      cached_pathspec_hash = self._pathspecs.get(event_object.filename)

      pathspec_hash = self.NULL_PATHSPEC
      if hasattr(event_object, u'pathspec'):
        pathspec_hash = hash(event_object.pathspec)

      if cached_pathspec_hash != pathspec_hash:
        logging.debug(u'New Cybox File due to pathspecs, file {}'.format(
            event_object.filename))
        cybox_file = self._CreateCyboxFile(event_object)

    return cybox_file

  def _Dummy(self, event_object, cybox_file):
    '''_Dummy callback'''
    if event_object:
      pass
    if cybox_file:
      pass
    return None, None

  def _FileStat(self, event_object, cybox_file):
    '''_FileStat callback'''
    date_use = timelib.Timestamp.CopyToDatetime(
        event_object.timestamp, self._output_mediator.timezone)

    for desc in event_object.timestamp_desc.split(u';'):
      if desc == u'crtime':
        cybox_file.created_time = date_use
      elif desc == u'atime':
        cybox_file.accessed_time = date_use
      elif desc == u'mtime':
        cybox_file.modified_time = date_use
      elif desc == u'ctime':
        # Cybox File Object does not support it.
        pass
      else:
        logging.warning(u'Unknown timestamp description [{}], event {}'.format(
            desc, event_object.uuid))

    return cybox_file, None

  def _URLHistory(self, event_object, cybox_file):
    '''_URLHistory callback'''
    cybox_url = cyboxUrlHistoryEntry()

    date_use = timelib.Timestamp.CopyToDatetime(
        event_object.timestamp, self._output_mediator.timezone)
    desc = event_object.timestamp_desc

    if desc == eventdata.EventTimestamp.LAST_VISITED_TIME:
      cybox_url.Last_Visit_DateTime = date_use
    elif desc == eventdata.EventTimestamp.EXPIRATION_TIME:
      cybox_url.Expiration_DateTime = date_use
    else:
      logging.warning(
          u'Unknown URL timestamp description [{}], event {}'.format(
              desc, event_object.uuid))

    return cybox_file, cybox_url

  def _EventToCybox(self, event_object):
    """_EventToCybox"""
    if event_object.uuid in self._uuid_map:
      logging.debug(u'Plaso event with uuid {} already mapped.'.format(
          event_object.uuid))
      return
    self._uuid_map[event_object.uuid] = True

    cybox_file = self._GetCyboxFileObject(event_object)

    callback_name = self._EVENT_TO_CYBOX_CALLBACKS.get(
        event_object.data_type, None)
    callback_function = None
    if callback_name:
      callback_function = getattr(self, callback_name, None)
    else:
      callback_function = self._Dummy

    cybox_file_new, _ = callback_function(event_object, cybox_file)

    # Updating cybox files
    if cybox_file_new:
      self._cybox_files[event_object.filename] = cybox_file_new

  def WriteEventBody(self, event_object):
    """Writes the body of an event object to the output."""
    self._EventToCybox(event_object)


manager.OutputManager.RegisterOutput(PlasoDFaxOutputModule)
